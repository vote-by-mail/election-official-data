import os.path
from urllib.parse import urljoin
from time import sleep
from ediblepickle import checkpoint
from selenium import webdriver
import pandas as pd
from common import key_namer, work_dir, to_list

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
    "download.default_directory": os.path.abspath(work_dir),
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
    xlsx_link.click()
    return None


def parse_df(xlsx_df):
  xlsx_df = xlsx_df.where(xlsx_df.notna(), '').apply(lambda x: x.str.strip())
  data = pd.DataFrame()
  data['city'] = xlsx_df['Town']
  data['county'] = xlsx_df['County'] + ' County'
  data['locale'] = xlsx_df['County'] + ':' + xlsx_df['Town']
  data['official'] = xlsx_df.apply(lambda x: x['First'] + ' ' + x['Last'] if x['First'] != 'Vacant' else None, axis=1)
  data['phones'] = xlsx_df['Office Phone'].apply(to_list)
  data['faxes'] = xlsx_df['Office Fax'].apply(to_list)
  data['emails'] = xlsx_df["Clerk's Email Address"].str.split(' or ')
  data['address'] = (xlsx_df['Office Mailing Address'] + ', ' + xlsx_df['City/Town:']
                     + ', ' + xlsx_df['State:'] + ' ' + xlsx_df['ZIP:'])
  data['physicalAddress'] = (xlsx_df['Physical Address'] + ', ' + xlsx_df['City/Town:.1']
                             + ', ' + xlsx_df['State:.1'] + ' ' + xlsx_df['ZIP:.1'])
  return data.to_dict(orient='records')


def fetch_data():
  #xlsx = cache_xlsx()
  return parse_df(pd.read_excel(os.path.join(work_dir, 'clerkcontactinfoexcel.xlsx'), skiprows=[0], dtype=str))


if __name__ == '__main__':
  print(fetch_data())
