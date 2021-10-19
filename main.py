import json
import pickle
import re
import time

import pandas as pd
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver


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
        # time.sleep(0.5)
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


def json_to_obj(filename):
    """Extracts dta from JSON file and saves it on Python object
    """
    with open(filename) as json_file:
        obj = json.loads(json_file.read())
    return obj


def retrieve_page_leads(page_elements):
    last_name = [e['lastName'] for e in page_elements]
    first_name = [e['firstName'] for e in page_elements]
    # https://www.linkedin.com/sales/people/{linkedin_url}
    linkedin_url = [re.findall(r'\((.*?)\)', e['entityUrn'])[0] for e in page_elements]
    company_name = [e['currentPositions'][0]['companyName'] for e in page_elements]
    df = pd.DataFrame({'first_name': first_name, 'last_name': last_name, 'company_name': company_name,
                       'linkedin_url': linkedin_url})
    return df
