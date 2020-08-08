import random
import re
from time import sleep
from ediblepickle import checkpoint
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
from common import key_namer, work_dir, to_list, cache_selenium, cache_request

BASE_URL = 'https://indianavoters.in.gov/CountyContact/Index'
EMAIL_LINK_URL = 'https://indianavoters.in.gov/MVPHome/PrintDocuments'

re_county = re.compile(r'Election Board Contact Information\s*(?P<addr>.*?)\s*'
                       + r'(?:\n\s*PHONE:\s*(?P<phone>[^\n]*)\s*)?(?:\n\s*FAX:\s*(?P<fax>[^\n]*)\s*)?\n\n',
                       re.MULTILINE | re.DOTALL)


def indiana_key_namer(args, kwargs):
  key_kwargs = kwargs.copy()
  key_kwargs['state'] = 'indiana'
  return key_namer(args[1:], key_kwargs)


@checkpoint(key=indiana_key_namer, work_dir=work_dir)
def cache_county(driver, county_name):
  """Use Selenium to select a county from the base page,
  triggering an ajax request to update a portion of the page.
  Return the updated portion as both HTML and text."""
  select = Select(driver.find_element_by_id('ddlCCounty'))
  select.select_by_visible_text(county_name)
  sleep(random.uniform(.3, .7))  # unhide county-box for first county AND don't overload server
  contact_box = driver.find_element_by_id('contact-box')
  return contact_box.get_attribute('innerHTML'), contact_box.text


@checkpoint(key=indiana_key_namer, work_dir=work_dir)
def cache_list(url=BASE_URL, verbose=True):  # use a keyword arg for key namer
  """Use Selenium to load the base page and loop through all counties.
  Returns a dictionary of county_name: html_snippet, text_snippet;
  as well as the full source of the base page"""
  counties = {}
  options = webdriver.ChromeOptions()
  options.add_argument('headless')
  with webdriver.Chrome(options=options) as driver:
    driver.get(url)
    select = Select(driver.find_element_by_id('ddlCCounty'))
    county_names = [option.text for option in select.options if option.get_attribute('value')]
    for county_name in tqdm(county_names, disable=not verbose):
      counties[county_name] = cache_county(driver, county_name)
    return counties, driver.page_source


def parse_county(county_name, county_text):
  locale = county_name.title() + ' County'
  match_dict = re_county.search(f'{county_text}\n\n').groupdict()
  return {
    'locale': locale,
    'county': locale,
    'phones': to_list(match_dict['phone']),
    'faxes': to_list(match_dict['fax']),
    'address': match_dict['addr'].replace('\n', ', '),
    # emails are supplied in a separate list
  }


def fetch_emails():
  html = cache_selenium(EMAIL_LINK_URL)
  soup = BeautifulSoup(html, 'html.parser')
  xlsx_url = soup('a', text=re.compile(r'county.*e-?mail', re.IGNORECASE))[0]['href']
  xlsx = cache_request(xlsx_url, is_binary=True)
  emails = pd.read_excel(xlsx).fillna(method='ffill').apply(lambda x: x.str.strip())
  emails = emails.rename(columns={'Email': 'emails'})
  emails['locale'] = emails['County'].str.title() + ' County'
  return emails.groupby('locale')['emails'].apply(list)


def fetch_data(verbose=True):
  counties, _ = cache_list(verbose=verbose)
  data = pd.DataFrame(parse_county(county_name, county_text)
                      for county_name, (_, county_text) in tqdm(counties.items(), disable=not verbose))
  data = data.join(fetch_emails(), on='locale', how='left')
  data['emails'] = data['emails'].apply(lambda x: x if isinstance(x, list) else [])
  return data.to_dict(orient='records')


if __name__ == '__main__':
  print(fetch_data())
