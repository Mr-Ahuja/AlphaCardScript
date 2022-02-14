from os import name
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
import re,os,glob
from selenium.webdriver.support.select import Select

completed_thread = 0

def automate(data,driver):
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
    card = str(int(data["Card No"]))
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

    wait_till_visible('//*[@id="ipin"]',driver)

    driver.find_element_by_id("ipin").send_keys(str(data["ipin"]))
    driver.find_element_by_id("otpbut").click()
    
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

def read_data():
    df = pd.read_excel  ('data.xlsx',sheet_name="Sheet1")
    df['Card No']=df['Card No'].astype(str)
    return df.to_dict('records')

def main_file(batch_range,name,job_id):
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument('--headless')
    #options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=options)
    df = read_data()[batch_range[0]:batch_range[1]]
    print(list(df))
    for data in df:
        print(data)
        try:
            automate(data,driver)
            print(data)
        except Exception as e:
            print(e)
            data["Status"] = "FAILED"
        pd.DataFrame(df).to_excel("media\\tmp\\"+job_id+"\\"+name+'.xlsx', index=False)
    global completed_thread
    completed_thread += 1
    driver.close()

#-------------------------------------------Thread Content --------------------------------------------------------

def run_job(pool_size,data_size,input_url_pass,job_id):                                                      

    import threading
    import time,glob,os
    global input_url, completed_thread
    input_url = input_url_pass

    per_batch_data = data_size//pool_size

    os.makedirs('media/tmp/'+job_id)



    for x in range(pool_size):
        min_val = max(x*per_batch_data , 0)
        max_val = min((x+1)*per_batch_data, data_size)
        print(min_val, max_val)
        thread = threading.Thread(target=main_file, args=((min_val,max_val),"Batch" + str(x),job_id,))
        thread.start()
        print("done")

    while completed_thread != pool_size:
        time.sleep(2)

    print("Generating Reports...")

    import glob, os
    import pandas as pd
    os.chdir(".")

    report_path = 'media/Reports'
    if not os.path.exists(report_path):
        os.makedirs(report_path)

    file_list = []
    for file in glob.glob("media/tmp/"+job_id+"/Batch*.xlsx"):
        file_list.append(file)
    excl_list = []
    
    for file in file_list:
        excl_list.append(pd.read_excel(file))
    

    excl_merged = pd.DataFrame()
    
    for excl_file in excl_list:
        excl_merged = excl_merged.append(
        excl_file, ignore_index=True)


    if not os.path.exists("media/Reports/"+job_id):
        os.makedirs("media/Reports/"+job_id)

    excl_merged["Card No"] = excl_merged['Card No'].astype(str)
    excl_merged.to_excel('media\\Reports\\'+job_id+'\\Full Report.xlsx', index=False)
    success = excl_merged[excl_merged["Status"]=="SUCCESS"]
    failed = excl_merged[excl_merged["Status"]=="FAILED"]
    not_attempted = excl_merged[excl_merged["Status"].isnull()]

    success.to_excel('media\\Reports\\'+job_id+'\\Success.xlsx', index=False)
    failed.to_excel('media\\Reports\\'+job_id+'\\Failure.xlsx', index=False)
    not_attempted.to_excel('media\\Reports\\'+job_id+'\\Not_Attempted.xlsx', index=False)


    failed_and_not_attempted = pd.DataFrame()
    failed_and_not_attempted = failed_and_not_attempted.append(
        failed, ignore_index=True)
    failed_and_not_attempted = failed_and_not_attempted.append(
        not_attempted, ignore_index=True)

    failed_and_not_attempted.to_excel('media\\Reports\\'+job_id+'\\Re-attempt-file.xlsx', index=False)