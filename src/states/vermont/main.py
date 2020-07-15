import random
from os.path import abspath
import re
import unicodedata
from urllib.parse import urljoin
from time import sleep
from ediblepickle import checkpoint
from selenium import webdriver
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
from common import key_namer, work_dir, to_list, cache_webkit, cache_selenium

BASE_URL = 'https://sos.vermont.gov/elections/town-clerks/'
XLSX_URL = 'https://sos.vermont.gov/media/fyvdm1j0/clerkcontactinfoexcel.xlsx'

def vermont_key_namer(args, kwargs):
  key_kwargs = kwargs.copy()
  key_kwargs['state'] = 'vermont'
  return key_namer(args, key_kwargs)


@checkpoint(key=vermont_key_namer, work_dir=work_dir)
def cache_xlsx(url=BASE_URL):  # use a keyword arg for key namer
  """
  Use Selenium to load the page with the link to the Excel file
  and click the link to download (since download is protected)
  """
  options = webdriver.ChromeOptions()
  options.add_argument('headless')
  # https://medium.com/@moungpeter/how-to-automate-downloading-files-using-python-selenium-and-headless-chrome-9014f0cdd196
  options.add_experimental_option("prefs", {
    "download.default_directory": abspath(work_dir),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing_for_trusted_sources_enabled": False,
    "safebrowsing.enabled": False
  })
  with webdriver.Chrome(options=options) as driver:
    driver.get(url)
    sleep(.5)
    print(driver.page_source)
    xlsx_link = driver.find_element_by_partial_link_text('Town Clerk contact information (Excel)')
    xlsx.click()
    return None


def fetch_data():
  xlsx = cache_xlsx()
  print(xlsx)
  #data = pd.read_excel(xlsx) #.fillna(method='ffill').apply(lambda x: x.str.strip())
  #print(data)
  return [{'locale': 'dummy'}]


if __name__ == '__main__':
  print(fetch_data())
