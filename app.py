from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask, render_template

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import datetime
import os
import sys

data = {
    "title": os.getenv("PAGE_TITLE", "")
}
userId = os.getenv("AIRTEL_USER_ID", "")
password = os.getenv("AIRTEL_PASSWORD", "")
chromeBinary = os.getenv("GOOGLE_CHROME_BIN", "")
chromeDriver = os.getenv("CHROMEDRIVER_PATH", "")


def getAirtelData(src, userId, password):
    global data
    print("getAirtelData fired from " + src +
          " at " + str(datetime.datetime.now()))

    # ChromeDriver configuration
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = chromeBinary
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(
        executable_path=chromeDriver, chrome_options=chrome_options)
    driver.set_page_load_timeout(20)
    URL = 'https://www.airtel.in/s/selfcare?normalLogin'
    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 10)
        mobileNumberField = wait.until(
            EC.presence_of_element_located((By.NAME, "mobileNumber")))
        passwordField = driver.find_element_by_name("password")
        submitButton = driver.find_element_by_id("loginButtonSpan")

        mobileNumberField.send_keys(userId)
        passwordField.send_keys(password)
        submitButton.click()

        usedData = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "used_tooltip")))
        detailsDiv = driver.find_elements_by_class_name("item")[1]
        detailsParagraphs = detailsDiv.find_elements_by_tag_name("p")

        periodRemaining = detailsParagraphs[1].text
        dataUsed = usedData.get_attribute('innerHTML')
        dataRemaining = detailsParagraphs[5].text

        data["periodRemaining"] = periodRemaining
        data["dataUsed"] = dataUsed
        data["dataRemaining"] = dataRemaining
        print(data)
    except:
        e = sys.exc_info()[0]
        print("Exception has been thrown. " + str(e))
    driver.close()


app = Flask(__name__)


@app.before_first_request
def init_scheduler():
    # Scheduler will refresh the in-memory data every hour
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(func=getAirtelData, trigger="interval", args=[
                            "scheduler", userId, password], max_instances=1, minutes=60)
    getAirtelData("initial startup", userId, password)
    scheduler.start()


@app.route("/")
def index():
    global data
    if "dataRemaining" not in data:
        getAirtelData("fallback of initial failure", userId, password)
    return render_template("index.html", data=data)


if __name__ == "__main__":
    app.run()
