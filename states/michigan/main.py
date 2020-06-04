import urllib.parse as urlparse
from urllib.parse import parse_qs
import re
import random

from bs4 import BeautifulSoup

from common import cache_request, normalize_state, diff_and_save

BASE_URL = "https://mvic.sos.state.mi.us/Clerk"


def random_wait(min_wait=.1, max_wait=.3):
  return random.uniform(min_wait, max_wait)

def urlparse_qs(url):
  parsed = urlparse.urlparse(url)
  return parse_qs(parsed.query)

def safe_extract(selector):
  if not selector:
    return None
  parent = selector.parent
  if not parent:
    return None
  nextSibling = parent.nextSibling
  if not nextSibling:
    return None
  return nextSibling.strip()

def parse_jurisdiction(soup, jurisdiction_name, county_name):
  city = re.sub(r'\s+Twp', ' Township', jurisdiction_name)
  county = county_name.title().strip()
  body = soup.find('div', class_='card-body')
  return {
    'locale': f'{city}:{county}',
    'city': city,
    'county': county,
    'emails': [a['href'].replace('mailto:','').strip() for a in body.select("a[href^=mailto]")],
    'phones': [safe_extract(body.find(text=lambda x: x.startswith("Phone")))],
    'faxes': [safe_extract(body.find(text=lambda x: x.startswith("Fax")))],
    'official': body.text.strip().split('\n')[0].split(',')[0].strip(),
  }

def crawl_and_parse():
  data = []
  text = cache_request(BASE_URL, verify=False)
  soup = BeautifulSoup(text, 'html.parser')

  '''
  https://www.ssllabs.com/ssltest/analyze.html?d=mvic.sos.state.mi.us
  Chain issues	Incomplete
  
  Therefore, have temporarily modified common.py to allow passing verify=False
  Will need a better solution to avoid man-in-the-middle attacks
  
  See https://stackoverflow.com/questions/28667684/python-requests-getting-sslerror/28667850#28667850
  '''

  for county in soup.find('select', id='Counties')('option'):
    if not county.get('value'):
      continue
    county_text = cache_request(f'{BASE_URL}/SearchByCounty', method='POST', data={'CountyID': county.get('value')}, wait=random_wait(), verify=False)
    county_soup = BeautifulSoup(county_text, 'html.parser')
    for jurisdiction_a in county_soup('a', class_='local-clerk-link'):
      params = urlparse_qs(jurisdiction_a.get('href'))
      jurisdiction_data = {k: v[0] for k,v in params.items() if k != 'dummy'}
      jurisdiction_text = cache_request(f'{BASE_URL}/LocalClerk', method='POST', data=jurisdiction_data, wait=random_wait(), verify=False)
      jurisdiction_soup = BeautifulSoup(jurisdiction_text, 'html.parser')
      data.append(parse_jurisdiction(jurisdiction_soup, jurisdiction_data['jurisdictionName'], county.text))

  data = normalize_state(data)
  diff_and_save(data, 'public/michigan.json')

if __name__ == '__main__':
  crawl_and_parse()
