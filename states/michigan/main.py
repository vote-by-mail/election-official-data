import json
import urllib.parse as urlparse
from urllib.parse import parse_qs
import os
import re

from bs4 import BeautifulSoup

from common import to_list, cache_request, normalize_state, diff_and_save

BASE_URL = "https://mvic.sos.state.mi.us/Clerk"


def urlparse_qs(url):
  parsed = urlparse.urlparse(url)
  return parse_qs(parsed.query)

def safe_extract(selector):
  results = selector.extract()
  if not results:
    return None
  element = results[0]
  if not element:
    return None
  return element.strip()

def filter_dict_by_key(d, keys):
  keys = set(keys)
  return { k: v for k, v in d.items() if k in keys}
  
def parse_township(soup, jurisdiction_name, county_name):
  body = response.css('div.card-body')
  phone = safe_extract(body.xpath('*[contains(text(), "Phone")]/following-sibling::text()'))
  fax = safe_extract(body.xpath('*[contains(text(), "Fax")]/following-sibling::text()'))

  emails = response.css('div.card-body a::attr(href)').getall()
  try:
    email = next(e.split('mailto:')[1] for e in emails if e.startswith('mailto:'))
  except StopIteration:
    email = None

  first_line = body.css('::text').getall()[0].strip().split(',')
  if len(first_line) >= 2:
    clerk, title = first_line[0], first_line[-1] 
  elif len(first_line) == 1:
    clerk, title = first_line[0], None

  value = {}
  value['county'] = county_name
  value['city'] = jurisdiction_name

  # rename Twp to Township
  if value['city'].endswith('Twp'):
    value['city'] = value['city'][:-3] + 'Township'

  county = value['county'].title().strip()

  return {
    'locale': value['city'] + ':' + county,
    'city': value['city'],
    'county': county,
    'emails': to_list(email),
    'phones': to_list(phone),
    'faxes': to_list(fax),
    'official': clerk,
  }

  with open('public/michigan.json', 'w') as fh:
    json.dump(output, fh)
  
if __name__ == '__main__':
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
    county_data = {'CountyID': county.get('value'), 'CountyName': county.text}
    wait = 0 #random.uniform(1, 3)
    county_text = cache_request(f'{BASE_URL}/SearchByCounty', method='POST', data=county_data, wait=wait, verify=False)
    county_soup = BeautifulSoup(county_text, 'html.parser')
    for township_a in county_soup('a', class_='local-clerk-link'):
      params = urlparse_qs(township_a.get('href'))
      if 'dummy' in params:
        del params['dummy']
      township_data = {k: v[0] for k,v in params.items()}
      wait = 0 #random.uniform(1, 3)
      township_text = cache_request(f'{BASE_URL}/LocalClerk', method='POST', data=township_data, wait=wait, verify=False)
      township_soup = BeautifulSoup(township_text, 'html.parser')
      data.append(parse_township(township_soup, township_data['jurisdictionName'], county.text))
      print(data)
      break
    break

  #normalize_state(data)
  #diff_and_save(data, 'public/michigan.json')
