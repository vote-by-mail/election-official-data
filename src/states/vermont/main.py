import os
import os.path
import time
from ediblepickle import checkpoint
from selenium import webdriver
import pandas as pd
from common import key_namer, work_dir

BASE_URL = 'https://sos.vermont.gov/elections/town-clerks/'


def vermont_key_namer(args, kwargs):
  key_kwargs = kwargs.copy()
  key_kwargs['state'] = 'vermont'
  return key_namer(args, key_kwargs)


@checkpoint(key=vermont_key_namer, work_dir=work_dir)
def cache_xlsx(url=BASE_URL):  # use a keyword arg for key namer
  """
  Use Selenium to load the page with the link to the Excel file
  and click the link to download (since download is protected).
  Returns page_source (for debugging), contents of xlsx file
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
    time.sleep(.5)
    xlsx_link = driver.find_element_by_partial_link_text('Town Clerk contact information (Excel)')
    xlsx_link.click()
    time.sleep(1)  # wait for download
    xlsx_path = os.path.join(work_dir, xlsx_link.get_attribute("href").split('/')[-1])
    with open(xlsx_path, mode='rb') as xlsx_file:
      xlsx = xlsx_file.read()
    os.remove(xlsx_path)
    return driver.page_source, xlsx


def parse_xlsx(xlsx):
  xlsx_df = pd.read_excel(xlsx, skiprows=[0], dtype=str)
  xlsx_df = xlsx_df.where(xlsx_df.notna(), '').apply(lambda x: x.str.strip())
  data = pd.DataFrame()
  data['city'] = xlsx_df['Town']
  data['county'] = xlsx_df['County'] + ' County'
  data['locale'] = xlsx_df['County'] + ':' + xlsx_df['Town']
  data['official'] = xlsx_df.apply(lambda x: x['First'] + ' ' + x['Last'] if x['First'] != 'Vacant' else None, axis=1)
  data['phones'] = xlsx_df['Office Phone'].str.split(' or ').apply(lambda x: [y.strip() for y in x if y])
  # add area code if missing
  data['phones'] = data['phones'].apply(lambda x: [f"802-{y}" if '802' not in y else y for y in x])
  data['faxes'] = xlsx_df['Office Fax'].str.split(' or ').apply(lambda x: [y.strip() for y in x if y])
  data['emails'] = xlsx_df["Clerk's Email Address"].str.split(' or ').apply(lambda x: [y.strip() for y in x if y])
  data['address'] = (xlsx_df['Office Mailing Address'] + ', ' + xlsx_df['City/Town:']
                     + ', ' + xlsx_df['State:'] + ' ' + xlsx_df['ZIP:'])
  data['physicalAddress'] = (xlsx_df['Physical Address'] + ', ' + xlsx_df['City/Town:.1']
                             + ', ' + xlsx_df['State:.1'] + ' ' + xlsx_df['ZIP:.1'])
  return data.to_dict(orient='records')


def fetch_data():
  _, xlsx = cache_xlsx()
  return parse_xlsx(xlsx)


if __name__ == '__main__':
  print(fetch_data())
