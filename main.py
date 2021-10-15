# pip install  git+https://github.com/ultrafunkamsterdam/undetected-chromedriver.git
import gzip
import json
import pickle
import random
import re
import time
import math

import pandas as pd
import numpy as np
# from selenium import webdriver
# import undetected_chromedriver as uc
from selenium.common.exceptions import JavascriptException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
from nameparser import HumanName
from tqdm import tqdm


def get_driver(proxy=None, timeout=60):
    seleniumwire_options = {'verify_ssl': False}
    if proxy:
        seleniumwire_options['suppress_connection_errors'] = False
        seleniumwire_options['proxy'] = {
            'https': f'https://{proxy}',
            'http': f'http://{proxy}',
        }

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--headless')

    driver = webdriver.Chrome(
        options=options,
        seleniumwire_options=seleniumwire_options
    )

    """
    TODO: install ublock here
    get_ublock()
    extensions.ublock0.adminSettings = best settings for twitter here
    browser.install_addon(extension_dir + extension, temporary=True)
    """

    driver.set_page_load_timeout(timeout)

    return driver


def scroll_page(driver):
    page_height = driver.execute_script("return document.body.scrollHeight")
    scroll_height = 0
    while True:
        scroll_height += int(page_height / 10)
        if scroll_height > page_height:
            break
        driver.execute_script(f"window.scrollTo(0, {scroll_height})")
        time.sleep(1)


def scroll_down(driver, num_press=10, pause=1):
    actions = ActionChains(driver)
    for _ in range(num_press):
        actions.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.5)
    actions.pause(pause)
    actions.perform()


def login(driver, email, password):
    driver.get('https://www.linkedin.com/sales')
    driver.find_element_by_id('username').send_keys(email)
    driver.find_element_by_id('password').send_keys(password + '\n')


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output)


def decode_body(body):
    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        return None


# driver = uc.Chrome()
driver = get_driver()
with open('credentials.json') as json_file:
    credentials = json.loads(json_file.read())
email = credentials['email']
password = credentials['password']

login(driver, email, password)

base_url = 'https://www.linkedin.com'

# exclude CEO
query_url = 'https://www.linkedin.com/sales/search/people?companySize=B%2CC%2CD&companyType=P&doFetchHeroCard=false' \
            '&geoIncluded=101165590%2C104738515&industryIncluded=43%2C42%2C124%2C144%2C34%2C17%2C25%2C63&logHistory' \
            '=false&page={page}&rsLogId=1083025178&searchSessionId=tH1elhyOROGZhSS53cliZA%3D%3D' \
            '&tenureAtCurrentCompany=1%2C2%2C3%2C4&titleExcluded=Founder%3A35&titleIncluded=Chief%2520Operating' \
            '%2520Officer%3A280%2CChief%2520Financial%2520Officer%3A68%2CChief%2520Marketing%2520Officer%3A716' \
            '%2CChief%2520Executive%2520Officer%3A8%2CCo-Founder%3A103&titleTimeScope=CURRENT'

driver.get(query_url.format(page=1))
relevant_responses = {}
page = 1
while page <= 5:
    # scroll_page(driver)
    scroll_down(driver)
    relevant_responses = {
                    i: decode_body(gzip.decompress(r.response.body)) for i, r in enumerate(driver.requests)
                    if 'PeopleSearch' in r.path and i not in relevant_responses}
    # goto next page
    driver.find_element_by_css_selector('button.search-results__pagination-next-button').click()
    page += 1
    time.sleep(random.randint(3, 10))


def retrieve_page_leads(page_elements):

    last_name = [e['lastName'] for e in page_elements]
    first_name = [e['firstName'] for e in page_elements]
    # https://www.linkedin.com/sales/people/{linkedin_url}
    linkedin_url = [re.findall(r'\((.*?)\)', e['entityUrn'])[0] for e in page_elements]
    company_name = [e['currentPositions'][0]['companyName'] for e in page_elements]
    df = pd.DataFrame({'first_name': first_name, 'last_name': last_name, 'company_name': company_name,
                       'linkedin_url': linkedin_url})
    return df
