import gzip
import math
import os
import random

from tqdm import tqdm

from main import *

driver = get_driver()

credentials = json_to_obj('credentials.json')
email = credentials['email']
password = credentials['password']

login(driver, email, password)

base_url = 'https://www.linkedin.com'

queries = json_to_obj('queries.json')
query_url = queries[5]['url']
# delete all previously stored requests
del driver.requests

relevant_responses = {}
page = 1
driver.get(query_url.format(page=page + 1))
total_pages = 100
p_bar = tqdm(desc='Page Number', total=total_pages)
while page <= total_pages:
    if page == 1:
        driver.find_element_by_css_selector('button.search-results__pagination-previous-button').click()
        time.sleep(5)

    # scroll_page(driver)
    scroll_down(driver, pause=random.randint(0, 1))
    new_relevant_responses = {
        i: decode_body(gzip.decompress(r.response.body)) for i, r in enumerate(driver.requests)
        if 'PeopleSearch' in r.path and i not in relevant_responses}
    leads_count = [r['paging']['total'] for i, r in new_relevant_responses.items()][0]
    total_pages = math.ceil(leads_count / 25)
    total_pages = total_pages if total_pages <= 100 else 100
    relevant_responses.update(new_relevant_responses)
    # goto next page
    driver.find_element_by_css_selector('button.search-results__pagination-next-button').click()
    page += 1
    p_bar.update()
    time.sleep(random.randint(3, 10))
p_bar.close()

df_list = [retrieve_page_leads(r['elements']) for i, r in relevant_responses.items()]
df = pd.concat(df_list).reset_index(drop=True).drop_duplicates()
df['linkedin_url'] = f'{base_url}/sales/people/' + df['linkedin_url']
df.to_csv('df.csv', index=False)

# df_list = [pd.read_csv(f) for f in os.listdir() if f.startswith('df') and f.endswith('csv')]
# linkedin_df = pd.concat(df_list).reset_index(drop=True).drop_duplicates()
# linkedin_df.to_excel('linkedin_15_10_21.xlsx', index=False)
