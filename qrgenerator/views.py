from doctest import master
from multiprocessing import context
import threading
from unittest import result
from django.shortcuts import render
from django.http import HttpResponse
from .models import QRModel
import time
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from os import listdir
from os.path import isfile, join
from random import randint
import pandas as pd
from datetime import datetime
from django.shortcuts import redirect
import os
from selenium import webdriver
import glob, os
import pandas as pd

completed_thread = 0

def automate(data,driver,type_of_card):
    global input_url
    driver.set_page_load_timeout(10)
    #https://payments.cashfree.com/forms/oneononeindus
    driver.get(input_url)
    wait_till_visible('//input[@id="customerAmount"]',driver)
    driver.find_element_by_xpath('//input[@id="customerAmount"]').send_keys("10000")
    driver.find_element_by_xpath('//input[@id="customerEmail"]').send_keys(str(data["Email"]))
    driver.find_element_by_xpath('//input[@id="customerPhoneNumber"]').send_keys(str(data["Mobile1"]))
    driver.find_element_by_xpath('//input[@id="Name"]').send_keys(str(data["Name1"]))

    driver.find_element_by_xpath('//button[contains(text(),"Pay Securely")]').click()
    wait_till_visible('//h2[text()="Card"]',driver)

    driver.find_element_by_xpath('//h2[text()="Card"]').click()
    input = driver.find_element_by_id("CardNumber1")
    card = str(int(data["Card_No"]))
    input.send_keys(card)
    
    month = str(data["Month"])

    if len(month) == 1:
        month = "0" + month
    
    driver.find_element_by_id('CardDate1').send_keys(month)
    driver.find_element_by_id('CardDate1').send_keys(str(int(data["Year"]))[2:])
    cvv = str(int(data["CVV"]))
    if len(str(cvv)) < 3:
        cvv = "0"*(3-len(cvv))+cvv
    else:
        cvv = cvv
    driver.find_element_by_id('CVVFormatter1').send_keys(cvv)
    driver.find_element_by_id('CardHolderName1').send_keys(str(data["Name1"]))
    driver.find_element_by_xpath('//button[contains(text(),"Pay Now")]').click()

    if type_of_card == "zaggle":
        wait_till_visible('//*[@id="ipin"]',driver)

        driver.find_element_by_id("ipin").send_keys(str(data["ipin"]))
        driver.find_element_by_id("otpbut").click()


    if type_of_card == "nsdl":
        wait_till_visible('//*[@id="txtipin"]',driver)

        driver.find_element_by_id("txtipin").send_keys(str(data["ipin"]))
        driver.find_element_by_id("btnverify").click()
        
    wait_till_visible('//*[text()="Order ID"]',driver)
    
    if check_exists_by_xpath('//div[text()="Payment successful"]',driver):
        data["Status"] = "SUCCESS"
    else:
        raise Exception()

def wait_till_visible(xpath,driver,max_wait = 5):
    if max_wait ==0:
        raise Exception()

    if check_exists_by_xpath(xpath,driver):
        return
    else:
        time.sleep(1)
        wait_till_visible(xpath,driver,max_wait-1)

def check_exists_by_xpath(xpath,driver):
    try:
        driver.find_element_by_xpath(xpath)
    except Exception:
        return False
    return True

def check_exists_by_id(id,driver):
    try:
        driver.find_element_by_id(id)
    except Exception:
        return False
    return True

def read_data(file_name):
    df = pd.read_excel  (file_name,sheet_name="Sheet1")
    df['Card_No']=df['Card_No'].astype(str)
    return df.to_dict('records')

def main_file(batch_range,name,job_id,file_name,type_of_card):
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.options import Options

    options = Options()
    #options.add_argument('--headless')
    #options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=options)
    df = read_data(file_name)[batch_range[0]:batch_range[1]]
    print(list(df))
    for data in df:
        print(data)
        try:
            automate(data,driver,type_of_card)
            print(data)
        except Exception as e:
            print(e)
            data["Status"] = "FAILED"
        pd.DataFrame(df).to_excel("media\\tmp\\"+str(job_id)+"\\"+name+'.xlsx', index=False)
    global completed_thread
    completed_thread += 1
    driver.close()

#-------------------------------------------Thread Content --------------------------------------------------------

def run_job(pool_size,data_size,input_url_pass,job_id,file_name,type_of_card):                                                      

    import threading
    import time,glob,os
    global input_url, completed_thread
    input_url = input_url_pass

    per_batch_data = data_size//pool_size

    os.makedirs('media/tmp/'+str(job_id))



    for x in range(pool_size):
        min_val = max(x*per_batch_data , 0)
        max_val = min((x+1)*per_batch_data, data_size)
        print(min_val, max_val)
        thread = threading.Thread(target=main_file, args=((min_val,max_val),"Batch" + str(x),job_id,file_name,type_of_card,))
        thread.start()
        print("done")

    while completed_thread != pool_size:
        time.sleep(2)

    print("Generating Reports...")


    os.chdir(".")

    report_path = 'media/Reports'
    if not os.path.exists(report_path):
        os.makedirs(report_path)

    file_list = []
    for file in glob.glob("media/tmp/"+str(job_id)+"/Batch*.xlsx"):
        file_list.append(file)
    excl_list = []
    
    for file in file_list:
        excl_list.append(pd.read_excel(file))
    

    excl_merged = pd.DataFrame()
    
    for excl_file in excl_list:
        excl_merged = excl_merged.append(
        excl_file, ignore_index=True)


    if not os.path.exists("media/Reports/"+str(job_id)):
        os.makedirs("media/Reports/"+str(job_id))

    excl_merged["Card_No"] = excl_merged['Card_No'].astype(str)
    excl_merged.to_excel('media\\Reports\\'+str(job_id)+'\\Full Report.xlsx', index=False)
    success = excl_merged[excl_merged["Status"]=="SUCCESS"]
    failed = excl_merged[excl_merged["Status"]=="FAILED"]
    not_attempted = excl_merged[excl_merged["Status"].isnull()]

    success.to_excel('media\\Reports\\'+str(job_id)+'\\Success.xlsx', index=False)
    failed.to_excel('media\\Reports\\'+str(job_id)+'\\Failure.xlsx', index=False)
    not_attempted.to_excel('media\\Reports\\'+str(job_id)+'\\Not_Attempted.xlsx', index=False)


    failed_and_not_attempted = pd.DataFrame()
    failed_and_not_attempted = failed_and_not_attempted.append(
        failed, ignore_index=True)
    failed_and_not_attempted = failed_and_not_attempted.append(
        not_attempted, ignore_index=True)

    failed_and_not_attempted.to_excel('media\\Reports\\'+str(job_id)+'\\Re-attempt-file.xlsx', index=False)
    file1 = open("running.txt","w")
    file1.write("")
    file1.close()
    

# Create your views here.
def saveqrimage(text):
    image = pyqrcode.create(text)
    imagename = str(int(time.time()))
    image.png("./media/Qr-Images/{}.png".format(imagename), scale=10)
    return imagename

def Home(request):
    from django.core.files.storage import default_storage
    context = {}
    media_path = settings.MEDIA_ROOT
    myfiles = [f for f in listdir(media_path) if isfile(join(media_path, f))]
    print(myfiles)
    results = []
    fs = FileSystemStorage()
    for file in myfiles:
        data = file.split("__")
        my_file = open("running.txt")
        
        status = "Not Executed"
        print(data)
        if os.path.exists("media/Reports/"+str(data[2].split(".")[0])):
            status = "Done"
        elif my_file.read() == data[2]:
            status = "In Progress"
        
        dt_obj = datetime.fromtimestamp(int(data[1].split(".")[0]))
        results.append({'name' : data[0],'date' : dt_obj.strftime('%d-%m-%y'),'time' : dt_obj.time(), 'download' :file, 'job':data[2].split('.')[0],'status' : status})
    context['results'] = results
    return render(request, 'qrgenerator/home.html', context=context)

def upload(request):
    context = {}
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        job_id = ''.join(["{}".format(randint(0, 9)) for num in range(0, 6)])
        name = fs.save(uploaded_file.name.split(".")[0] + "__" + str(time.time()) + "__" + job_id + ".xlsx", uploaded_file)

        context['url'] = fs.url(name)
        return redirect(job,job_id)
    return render(request, 'qrgenerator/upload.html', context)

def job(request,job_id):
    context = {}
    media_path = settings.MEDIA_ROOT
    myfiles = [f for f in listdir(media_path) if isfile(join(media_path, f))]
    data_file = ""
    for file in myfiles:
        if str(job_id) in file:
            data_file = file
    df = pd.read_excel  ("media/"+data_file ,sheet_name="Sheet1")
    df['Card_No']=df['Card_No'].astype(str)
    context['results'] = df.to_dict('records')
    context['main_file'] = file
    my_file = open("running.txt")

    if my_file.read() == job_id:
        
        context['success'] = "In Progress"
        context['failed'] = "In Progress"
        context['not_attempted'] = "In Progress"
        context['is_job_done'] = "running"

        
    else:
        if os.path.exists("media/Reports/"+str(job_id)):
            context['is_job_done'] = "completed"
            file_list = []
            for file in glob.glob("media/tmp/"+str(job_id)+"/Batch*.xlsx"):
                file_list.append(file)
            excl_list = []
            
            for file in file_list:
                excl_list.append(pd.read_excel(file))
            

            excl_merged = pd.DataFrame()
            
            for excl_file in excl_list:
                excl_merged = excl_merged.append(
                excl_file, ignore_index=True)
            success = excl_merged[excl_merged["Status"]=="SUCCESS"]
            failed = excl_merged[excl_merged["Status"]=="FAILED"]
            not_attempted = excl_merged[excl_merged["Status"].isnull()]
            context['success'] = len(success)
            context['failed'] = len(failed)
            context['not_attempted'] = len(not_attempted)

            context['full_report'] = "Reports/" + job_id + "/Full Report.xlsx"
            context['failure_report'] = "Reports/" + job_id + "/Failure.xlsx"
            context['success_report'] = "Reports/" + job_id + "/Success.xlsx"
            context['not_attempted_report'] = "Reports/" + job_id + "/Not_Attempted.xlsx"
            
            
        else:
            context['is_job_done'] = "not run"
    if request.method == 'POST':
        file1 = open("running.txt","w")
        file1.write(str(job_id))
        file1.close()
        url = request.POST.get('url')
        windows = request.POST.get('windows')
        type_of_card = request.POST.get('type')
        thread = threading.Thread(target=run_job, args=(int(windows), len(context['results']), url, job_id,"media/"+data_file,type_of_card,))
        thread.start()
        return redirect(job,job_id)
    return render(request, 'qrgenerator/job.html', context)