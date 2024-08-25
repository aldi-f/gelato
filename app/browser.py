from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import requests as r
from selenium.webdriver.common.by import By


class Browser:
    _instance = None
    _driver = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Browser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._driver:
            service = Service(executable_path="/usr/local/bin/geckodriver")
            options = webdriver.FirefoxOptions()
            options.add_argument('-no-sandbox')
            options.add_argument('--headless')
            options.add_argument('--disable-dev-shm-usage')
            self._driver = webdriver.Firefox(options=options, service=service)

    def reel_download_url(self, url) -> str:
        self._driver.get(url)
        wait = WebDriverWait(self._driver, 20)
        element = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'video')))

        reel_source = element.get_attribute('src')

        return reel_source
    

# ChromeBrowser = Browser()
