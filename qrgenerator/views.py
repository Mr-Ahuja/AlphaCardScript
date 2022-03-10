
from email.mime import base
from genericpath import isdir
from lib2to3.pgen2 import driver
from logging import exception
import threading
from django.shortcuts import render
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
import glob
import os
import pandas as pd
import json

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

completed_thread = 0
status_current = {
    "success": 0,
    "failed": 0,
    "resuccess": 0
}


def automate(data, driver, type_of_card, failed_execution=False):

    global input_url, status_current
    if failed_execution and data["Status"] == "SUCCESS":
        status_current['resuccess'] += 1
        status_current['success'] += 1
        return
    driver.set_page_load_timeout(10)
    # https://pages.razorpay.com/pl_IxSeGmoIFaJddc/view
    # https://payments.cashfree.com/forms/oneononeindus

    if "cashfree" in input_url:
        driver.get(input_url)
        wait_till_visible('//input[@id="customerAmount"]', driver)
        driver.find_element_by_xpath(
            '//input[@id="customerAmount"]').send_keys(str(data["Amount"]))
        driver.find_element_by_xpath(
            '//input[@id="customerEmail"]').send_keys(str(data["Email"]))
        driver.find_element_by_xpath(
            '//input[@id="customerPhoneNumber"]').send_keys(str(data["Mobile1"]))
        driver.find_element_by_xpath(
            '//input[@id="Name"]').send_keys(str(data["Name1"]))

        driver.find_element_by_xpath(
            '//button[contains(text(),"Pay Securely")]').click()
        wait_till_visible('//h2[text()="Card"]', driver)

        driver.find_element_by_xpath('//h2[text()="Card"]').click()
        input = driver.find_element_by_id("CardNumber1")
        card = str(int(data["Card_No"]))
        input.send_keys(card)

        month = str(data["Month"])

        if len(month) == 1:
            month = "0" + month

        driver.find_element_by_id('CardDate1').send_keys(month)
        driver.find_element_by_id('CardDate1').send_keys(
            str(int(data["Year"]))[2:])
        cvv = str(int(data["CVV"]))
        if len(str(cvv)) < 3:
            cvv = "0"*(3-len(cvv))+cvv
        else:
            cvv = cvv
        driver.find_element_by_id('CVVFormatter1').send_keys(cvv)
        driver.find_element_by_id(
            'CardHolderName1').send_keys(str(data["Name1"]))
        driver.find_element_by_xpath(
            '//button[contains(text(),"Pay Now")]').click()

    if "razorpay" in input_url:
        driver.get(input_url)
        wait_till_visible(
            '//*[@id="form-section"]/form/div[1]/div[1]/div/div[2]/div[1]/input', driver)
        driver.find_element_by_xpath(
            '//*[@id="form-section"]/form/div[1]/div[1]/div/div[2]/div[1]/input').send_keys(str(data["Amount"]))
        driver.find_element_by_xpath(
            '//input[@name="email"]').send_keys(str(data["Email"]))
        driver.find_element_by_xpath(
            '//input[@name="phone"]').send_keys(str(data["Mobile1"]))

        time.sleep(2)
        driver.find_element_by_xpath("//button//span").click()
        # from selenium.webdriver.common.action_chains import ActionChains
        # action = ActionChains(driver)
        # action.move_to_element(element)
        # action.click(element)
        # action.perform()
        # driver.find_element_by_xpath(
        #     '//input[@id="Name"]').send_keys(str(data["Name1"]))

        time.sleep(5)
        wait_till_visible('//iframe[@allowpaymentrequest="true"]', driver)
        driver.switch_to.frame(driver.find_element_by_xpath(
            '//iframe[@allowpaymentrequest="true"]'))

        wait_till_visible('//button[@method="card"]', driver)

        driver.find_element_by_xpath('//button[@method="card"]').click()

        wait_till_visible('//*[@id="card_number"]', driver)
        time.sleep(2)
        input = driver.find_element_by_id("card_number")
        card = str(int(data["Card_No"]))
        input.send_keys(card)

        month = str(data["Month"])

        if len(month) == 1:
            month = "0" + month

        driver.find_element_by_id('card_expiry').send_keys(month)
        driver.find_element_by_id('card_expiry').send_keys(
            str(int(data["Year"]))[2:])
        cvv = str(int(data["CVV"]))
        if len(str(cvv)) < 3:
            cvv = "0"*(3-len(cvv))+cvv
        else:
            cvv = cvv
        driver.find_element_by_id('card_cvv').send_keys(cvv)
        driver.find_element_by_id('card_name').send_keys(str(data["Name1"]))
        driver.find_element_by_id('should-save-card').click()

        driver.find_element_by_xpath(
            '//*[@id="footer"]').click()

        time.sleep(3)

        driver.switch_to.window(driver.window_handles[1])

    if type_of_card == "zaggle":
        wait_till_visible('//*[@id="ipin"]', driver)

        driver.find_element_by_id("ipin").send_keys(str(data["ipin"]))
        driver.find_element_by_id("otpbut").click()

    if type_of_card == "nsdl":
        wait_till_visible('//*[@id="txtipin"]', driver)

        driver.find_element_by_id("txtipin").send_keys(str(data["ipin"]))
        driver.find_element_by_id("btnverify").click()

    if type_of_card == "zoduko":
        wait_till_visible('//*[@id="expDate"]', driver)

        driver.find_element_by_id("expDate").send_keys(month)
        for year_digit in str(int(data["Year"])):
            driver.find_element_by_id("expDate").send_keys(year_digit)

        driver.find_element_by_id("pin").send_keys(str(data["ipin"]))
        driver.find_element_by_id("submitButtonIdForPin").click()

    wait_till_visible('//*[text()="Order ID"]', driver)

    if "razorpay" in input_url:
        driver.switch_to.window(driver.window_handles[0])
        if not check_exists_by_xpath('//button[text()="Retry"]', driver):
            data["Status"] = "SUCCESS"
            status_current['success'] += 1

        else:
            raise Exception()

    if "cashfree" in input_url:
        if check_exists_by_xpath('//div[text()="Payment successful"]', driver):
            data["Status"] = "SUCCESS"
            status_current['success'] += 1

        else:
            raise Exception()


def wait_till_visible(xpath, driver, max_wait=5):
    if max_wait == 0:
        raise Exception()

    if check_exists_by_xpath(xpath, driver):
        return
    else:
        time.sleep(1)
        wait_till_visible(xpath, driver, max_wait-1)


def check_exists_by_xpath(xpath, driver):
    try:
        driver.find_element_by_xpath(xpath)
    except Exception:
        return False
    return True


def check_exists_by_id(id, driver):
    try:
        driver.find_element_by_id(id)
    except Exception:
        return False
    return True


def read_data(file_name):
    df = pd.read_excel(file_name, sheet_name="Sheet1")
    df['Card_No'] = df['Card_No'].astype(str)
    return df.to_dict('records')


def main_file(batch_range, name, job_id, file_name, type_of_card, failed_execution=False):
    global completed_thread, status_current

    options = Options()
    options.add_argument('--headless')
    # options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(
        ChromeDriverManager().install(), chrome_options=options)
    df = read_data(file_name)[batch_range[0]:batch_range[1]]
    for data in df:
        try:
            automate(data, driver, type_of_card, failed_execution)
        except Exception as e:
            print(e)
            data["Status"] = "FAILED"
            status_current['failed'] += 1
        pd.DataFrame(df).to_excel("media\\tmp\\"+str(job_id) +
                                  "\\"+name+'.xlsx', index=False)
        if job_id not in open('running.txt').read():
            driver.close()
            return
    completed_thread += 1
    driver.close()

# -------------------------------------------Thread Content --------------------------------------------------------


def run_job(pool_size, data_size, input_url_pass, job_id, file_name, type_of_card, failed_execution=False):
    import threading
    import time
    import glob
    import os
    import math
    global input_url, completed_thread, status_current
    status_current["success"] = 0

    status_current["resuccess"] = 0
    status_current["failed"] = 0
    completed_thread = 0
    input_url = input_url_pass

    per_batch_data = data_size//pool_size

    if not os.path.exists("media/tmp/"+str(job_id)):
        os.makedirs("media/tmp/"+str(job_id))
    else:
        files_in = glob.glob('media/tmp/'+str(job_id)+'/*')
        for f in files_in:
            os.remove(f)

    job_profile = {'input_url_pass': input_url_pass,
                   'type_of_card': type_of_card, 'pool_size': pool_size}
    f = open("media/tmp/"+job_id + "/"+job_id + ".json", "w+")
    f.write(str(json.dumps(job_profile)))
    f.close()

    for x in range(pool_size):
        min_val = x*per_batch_data
        max_val = min((x+1)*per_batch_data, data_size)
        thread = threading.Thread(target=main_file, args=(
            (min_val, max_val), "Batch" + str(x), job_id, file_name, type_of_card, failed_execution,))
        thread.start()
        time.sleep(1)

    if data_size % pool_size != 0:

        thread = threading.Thread(target=main_file, args=(((pool_size)*per_batch_data, data_size),
                                  "Batch" + str(pool_size+1), job_id, file_name, type_of_card, failed_execution,))
        thread.start()
        pool_size += 1

    while completed_thread != pool_size:
        time.sleep(2)
        if job_id not in open("running.txt").read():
            break

    print("Generating Reports...")
    tokens_left = int(open("token.txt").read())

    file1 = open("token.txt", "w+")
    file1.write(
        str(tokens_left - status_current["success"] + status_current['resuccess']))
    file1.close()

    os.chdir(".")

    report_path = 'media/Reports'
    if not os.path.exists(report_path):
        os.makedirs(report_path)
    else:
        files_in = glob.glob('media/Reports/'+str(job_id)+'/*')
        for f in files_in:
            os.remove(f)

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
    else:
        files_in = glob.glob('media/Reports/'+str(job_id)+'/*')
        for f in files_in:
            os.remove(f)

    if len(excl_merged) != 0:
        excl_merged["Card_No"] = excl_merged['Card_No'].astype(str)
    excl_merged.to_excel('media\\Reports\\'+str(job_id) +
                         '\\Full Report.xlsx', index=False)
    success = excl_merged[excl_merged["Status"] == "SUCCESS"]
    failed = excl_merged[excl_merged["Status"] == "FAILED"]
    not_attempted = excl_merged[excl_merged["Status"].isnull()]

    success.to_excel('media\\Reports\\'+str(job_id) +
                     '\\Success.xlsx', index=False)
    failed.to_excel('media\\Reports\\'+str(job_id) +
                    '\\Failure.xlsx', index=False)
    not_attempted.to_excel('media\\Reports\\'+str(job_id) +
                           '\\Not_Attempted.xlsx', index=False)

    failed_and_not_attempted = pd.DataFrame()
    failed_and_not_attempted = failed_and_not_attempted.append(
        failed, ignore_index=True)
    failed_and_not_attempted = failed_and_not_attempted.append(
        not_attempted, ignore_index=True)

    failed_and_not_attempted.to_excel(
        'media\\Reports\\'+str(job_id)+'\\Re-attempt-file.xlsx', index=False)
    file1 = open("running.txt", "w+")
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
    context = {'token': open("token.txt").read()}
    media_path = settings.MEDIA_ROOT
    myfiles = [f for f in listdir(media_path) if isfile(join(media_path, f))]
    results = []
    fs = FileSystemStorage()
    for file in myfiles:
        data = file.split("__")
        my_file = open("running.txt")

        status = "Not Executed"
        if os.path.exists("media/Reports/"+str(data[2].split(".")[0])):
            status = "Done"
        elif my_file.read() == data[2].split('.')[0]:
            status = "In Progress"

        dt_obj = datetime.fromtimestamp(int(data[1].split(".")[0]))
        results.append({'name': data[0], 'date': dt_obj.strftime(
            '%d-%m-%y'), 'time': dt_obj.time(), 'download': file, 'job': data[2].split('.')[0], 'status': status})
    context['results'] = results
    return render(request, 'qrgenerator/home.html', context=context)


def upload(request):
    context = {'token': open("token.txt").read()}
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        job_id = ''.join(["{}".format(randint(0, 9)) for num in range(0, 6)])
        name = fs.save(uploaded_file.name.split(
            ".")[0] + "__" + str(time.time()) + "__" + job_id + ".xlsx", uploaded_file)

        context['url'] = fs.url(name)
        return redirect(job, job_id)
    return render(request, 'qrgenerator/upload.html', context)


def delete_job(request, job_id):
    if request.method == 'POST' and open('running.txt') != job_id:
        media_path = settings.MEDIA_ROOT
        myfiles = [f for f in listdir(
            media_path) if isfile(join(media_path, f))]
        data_file = ""
        for file in myfiles:
            if str(job_id) in file:
                data_file = file
        if os.path.exists("media/"+data_file):
            os.remove("media/"+data_file)

        if os.path.exists("media/tmp/"+str(job_id)):
            files_in = glob.glob('media/tmp/'+str(job_id)+'/*')
            for f in files_in:
                os.remove(f)
            os.rmdir("media/tmp/"+str(job_id))

        if os.path.exists("media/Reports/"+str(job_id)):
            files_in = glob.glob('media/Reports/'+str(job_id)+'/*')
            for f in files_in:
                os.remove(f)
            os.rmdir("media/Reports/"+str(job_id))
    return redirect(Home)


def job(request, job_id, reattempt=False):
    reattempt = bool(reattempt)
    context = {'token': open("token.txt").read()}
    media_path = settings.MEDIA_ROOT
    myfiles = [f for f in listdir(media_path) if isfile(join(media_path, f))]

    data_file = ""

    for file in myfiles:
        if str(job_id) in file:
            data_file = file

    if data_file != "":
        df = pd.read_excel("media/"+data_file, sheet_name="Sheet1")
        df['Card_No'] = df['Card_No'].astype(str)
        context['results'] = df.to_dict('records')
        context['main_file'] = file

    if open("running.txt").read() == job_id:
        global status_current
        context['success'] = status_current['success']
        context['failed'] = status_current['failed']
        context['not_attempted'] = len(df.to_dict(
            'records')) - status_current['success'] - status_current['failed']
        context['is_job_done'] = "running"
    else:
        if os.path.exists("media/Reports/"+str(job_id)) or os.path.exists("media/tmp/"+str(job_id)):
            full_report = pd.read_excel(
                "media\\Reports\\"+str(job_id)+'\\Full Report.xlsx')
            full_report['Card_No'] = full_report['Card_No'].astype(str)
            context['results'] = full_report.to_dict('records')
            context['is_job_done'] = "completed"
            context['success'] = len(
                full_report[full_report["Status"] == "SUCCESS"])
            context['failed'] = len(
                full_report[full_report["Status"] == "FAILED"])
            context['not_attempted'] = len(
                full_report) - context['success'] - context['failed']

            context['full_report'] = "Reports/" + job_id + "/Full Report.xlsx"
            context['failure_report'] = "Reports/" + job_id + "/Failure.xlsx"
            context['success_report'] = "Reports/" + job_id + "/Success.xlsx"
            context['not_attempted_report'] = "Reports/" + \
                job_id + "/Not_Attempted.xlsx"
        else:
            context['is_job_done'] = "not run"
    if request.method == 'POST' or bool(reattempt):
        if open("running.txt").read() != "":
            context['error_message'] = "Job Already In Progress"
            return render(request, 'qrgenerator/job.html', context)
        if int(open("token.txt").read()) < len(read_data("media/"+data_file)):
            context['error_message'] = "Please Recharge First, Not Enough Tokens"
            return render(request, 'qrgenerator/job.html', context)
        file1 = open("running.txt", "w+")
        file1.write(str(job_id))
        file1.close()

        url = windows = type_of_card = ""
        if reattempt:
            f = open('media\\tmp\\'+job_id+'\\'+job_id+'.json')
            last_profile = json.loads(f.read())
            url = last_profile['input_url_pass']
            windows = last_profile['pool_size']
            type_of_card = last_profile['type_of_card']
            data_file = "Reports/" + job_id + "/Full Report.xlsx"
        else:
            url = request.POST.get('url')
            windows = request.POST.get('windows')
            type_of_card = request.POST.get('type')

        thread = threading.Thread(target=run_job, args=(int(windows), len(
            context['results']), url, job_id, "media/"+data_file, type_of_card, reattempt,))
        thread.start()
        return redirect(job, job_id)
    return render(request, 'qrgenerator/job.html', context)


def load_token(request, token_to_add):
    if request.method == 'POST':
        file1 = open("token.txt", "w+")
        file1.write(int(file1.read()) + token_to_add)
        file1.close()
    return "Done"


def stop_job(request, job_id):
    if request.method == 'POST':
        file1 = open("running.txt", "w+")
        file1.write("")
        file1.close()
    return redirect(job, job_id)


def retrigger(request, job_id):
    return redirect(job, job_id=job_id, reattempt=True)


class PennyWindow:
    def __init__(self, job_id):
        self.job_id = job_id
        options = Options()
        options.add_argument("--start-maximized")
        # options.add_argument('--headless')
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(), chrome_options=options)

        current_driver = self.driver
        current_driver.get("https://digitalseva.csc.gov.in/auth/user/login")

        self.status = "not_running"

    def create_login_session(self, user_id, password):
        self.driver.get("https://digitalseva.csc.gov.in/auth/user/login")
        wait_till_visible("//*[@id='csclogin']", self.driver)

        self.driver.find_element_by_id('csclogin').send_keys(user_id)
        self.driver.find_element_by_id('cscpass').send_keys(password)
        wait_till_visible("//*[@id='csclogin']", self.driver)
        self.driver.find_element_by_xpath(
            '//*[@id="captchaimgs"]/img').screenshot("media/penny/screenshots/"+self.job_id+".png")

    def enter_captcha(self, captcha):
        self.driver.find_element_by_id('captcha').send_keys(captcha)
        self.driver.find_element_by_xpath('//input[@value="Sign In"]').click()

    def load_cards(self):
        self.base_file = "media/penny/" + \
            [f for f in listdir("media/penny/") if self.job_id in str(f)][0]
        return read_data(self.base_file)

    def load_portal(self):
        time.sleep(2)
        self.driver.get("https://digitalseva.csc.gov.in/auth/user/login")
        time.sleep(10)
        self.driver.get('https://digitalseva.csc.gov.in/wallet/addmoney')
        wait_till_visible('//*[@id="amount"]', self.driver)

    def add_money(self):
        all_cards = self.load_cards()

        for card in all_cards:
            total_transactions = int(card['Amount_Left'])//101
            for x in range(total_transactions):
                try:
                    self.automation(card)
                    card['Amount_Left'] = int(card['Amount_Left']) - 101
                except Exception:
                    pass
                pd.DataFrame(all_cards).to_excel(
                    "media\\penny\\resource\\"+self.job_id + '.xlsx', index=False)
        pd.DataFrame(all_cards).to_excel(
                    "media\\penny\\Reports\\"+self.job_id + '.xlsx', index=False)

    def automation(self, card):
        self.driver.get('https://digitalseva.csc.gov.in/wallet/addmoney')
        wait_till_visible('//*[@id="amount"]', self.driver)

        self.driver.find_element_by_id('amount').send_keys(101)
        self.driver.find_element_by_id('phone').send_keys(card['Mobile'])

        self.driver.find_element_by_xpath(
            '//*[@id="add-money-to-pg-div"]/div[3]/label[1]').click()
        self.driver.find_element_by_id('add-mbtn').click()

        wait_till_visible('//ul[@class="payment_mode"]/li', self.driver)
        self.driver.find_element_by_xpath(
            '//ul[@class="payment_mode"]/li').click()

        time.sleep(2)
        self.driver.find_element_by_id('OPTCRDC').click()

        wait_till_visible('//*[@id="cardNumberField"]', self.driver)
        self.driver.find_element_by_id(
            'cardNumberField').send_keys(str(card['Card_No']))

        self.driver.find_element_by_id(
            'cardHolderNameField').send_keys(str(card['Name']))

        month = str(card["Month"])

        if len(month) == 1:
            month = "0" + month

        self.driver.find_element_by_id('expiryDateField').send_keys(month)

        self.driver.find_element_by_id('expiryDateField').send_keys(
            str(int(card["Year"]))[2:])

        cvv = str(int(card["CVV"]))
        if len(str(cvv)) < 3:
            cvv = "0"*(3-len(cvv))+cvv
        else:
            cvv = cvv
        self.driver.find_element_by_id('cvvNumberField').send_keys(cvv)

        self.driver.find_element_by_xpath(
            '//*[@id="TransactionForm"]//a[text()="confirm Payment"][1]').click()

        wait_till_visible('//*[@id="expDate"]', self.driver)
        print(month,card["Year"])
        self.driver.find_element_by_id("expDate").send_keys(month)
        for year_digit in str(int(card["Year"])):
            self.driver.find_element_by_id("expDate").send_keys(year_digit)

        self.driver.find_element_by_id("pin").send_keys(str(card["ipin"]))
        self.driver.find_element_by_id("submitButtonIdForPin").click()

        wait_till_visible('//*[@class="payment"][1]',self.driver,20)
        if self.driver.find_element_by_xpath('//*[@class="payment"][1]').text != "Decline":
            card["Amount_Left"]  = str(int(card["Amount_Left"])-101)


def executor(penny_window):
    # 30 second wait for credentials and captch
    for _ in range(100):
        time.sleep(1)
        print(_)
        if os.path.exists("media/penny/credentials/"+penny_window.job_id+".json"):
            credentials_json = open(
                "media/penny/credentials/"+penny_window.job_id+".json", 'r')
            credentials = json.loads(credentials_json.read())
            credentials_json.close()
            try:
                penny_window.enter_captcha(credentials['captcha'])
                penny_window.load_portal()
                penny_window.add_money()
                os.remove("media/penny/screenshots/" +
                          penny_window.job_id + ".png")
                os.remove("media/penny/credentials/" +
                          penny_window.job_id + ".json")
            except Exception:
                os.remove("media/penny/screenshots/" +
                          penny_window.job_id + ".png")
                os.remove("media/penny/credentials/" +
                          penny_window.job_id + ".json")
            break
    else:
        os.remove("media/penny/screenshots/" + penny_window.job_id + ".png")


def penny(request):
    context = {'token': open("token.txt").read()}
    if not os.path.exists("media/penny/"):
        os.makedirs("media/penny/")
        os.makedirs("media/penny/Reports")
        os.makedirs("media/penny/resource")
        os.makedirs("media/penny/screenshots")
        os.makedirs("media/penny/credentials")

    context = {'token': open("token.txt").read()}
    all_files = [f for f in listdir(
        "media/penny") if isfile(join("media/penny", f))]
    running = [f.split('.')[0] for f in listdir(
        "media/penny/screenshots/") if isfile(join("media/penny/screenshots/", f))]
    completed = [f.split('.')[0] for f in listdir(
        "media/penny/resource") if isfile(join("media/penny/resource", f))]
    results = []
    for file in all_files:
        data = file.split("__")
        job_id = str(data[2].split(".")[0])

        status = "Not Executed"

        if job_id in running:
            status = "In Progress"
        elif job_id in completed:
            status = "Done"

        dt_obj = datetime.fromtimestamp(int(data[1].split(".")[0]))
        results.append({'name': data[0], 'date': dt_obj.strftime(
            '%d-%m-%y'), 'time': dt_obj.time(), 'download': file, 'job': data[2].split('.')[0], 'status': status})
    context['results'] = results

    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage(location="media/penny/")
        job_id = ''.join(["{}".format(randint(0, 9)) for num in range(0, 6)])
        name = fs.save(uploaded_file.name.split(
            ".")[0] + "__" + str(time.time()) + "__" + job_id + ".xlsx", uploaded_file)
        context['url'] = fs.url(name)
        return redirect(penny_job, job_id)
    return render(request, 'qrgenerator/penny.html', context=context)


def penny_job(request, job_id):
    context = {'token': open("token.txt").read(), 'job_id': job_id}

    running = [f.split('.')[0] for f in listdir(
        "media/penny/screenshots/") if isfile(join("media/penny/screenshots/", f))]
    completed = [f.split('.')[0] for f in listdir(
        "media/penny/resource/") if isfile(join("media/penny/resource/", f))]
    base_file = "media/penny/" + \
        [f for f in listdir("media/penny/") if job_id in str(f)][0]

    file_name = "media/penny/resource/" + job_id + ".xlsx"
    if job_id in running:
        context['is_job_done'] = "running"
        file_name = base_file
    else:
        if job_id in completed:
            context['is_job_done'] = "completed"
        else:
            context['is_job_done'] = "not run"
            file_name = base_file
    full_report = pd.read_excel(file_name)
    full_report['Card_No'] = full_report['Card_No'].astype(str)
    context['results'] = full_report.to_dict('records')

    if request.method == "POST":
        if not os.path.exists("media/penny/screenshots/" + job_id + ".png"):
            user_id = request.POST.get('user_id')
            password = request.POST.get('password')
            penny_window = PennyWindow(job_id)
            penny_window.create_login_session(user_id, password)

            thread = threading.Thread(target=executor, args=(penny_window,))
            thread.start()
        context['captcha'] = 'True'

    return render(request, 'qrgenerator/penny_job.html', context=context)


def captcha(request, job_id):
    captcha_json = {'captcha': request.POST.get('captcha')}
    credentials = open("media/penny/credentials/"+job_id + ".json", "w+")
    credentials.write(str(json.dumps(captcha_json)))
    credentials.close()
    return redirect(penny_job, job_id)

def penny_delete(request,job_id):
    base_file = "media/penny/" + \
        [f for f in listdir("media/penny/") if job_id in str(f)][0]
    os.remove(base_file)
    if os.path.exists("media/penny/screenshots/" + job_id + ".png"):
        os.remove("media/penny/screenshots/" + job_id + ".png")
    if os.path.exists("media/penny/credentials/" + job_id + ".png"):   
        os.remove("media/penny/credentials/" + job_id + ".json")
    
    return redirect(penny)