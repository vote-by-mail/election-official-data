from urllib.parse import urlparse, parse_qs
import re
import random
import unicodedata
import os
from tqdm import tqdm
from bs4 import BeautifulSoup
from common import dir_path, cache_request, re_to_e164

BASE_URL = "https://mvic.sos.state.mi.us/Clerk"

# resolved issue with SSL cert chain by fixing intermediate cert
# base64 root-intermediate-site certs saved from Chrome, converted to pem using openssl,
# concatenated into mich_chain.pem
SSL_CERT = os.path.join(dir_path(__file__), 'michigan_chain.pem')

re_official = re.compile(r'^\s*(.*?)\s*[,\n]')
re_phys_addr = re.compile(r'\n(.*?\d{5}(?:-\d{4})?)\n', re.MULTILINE | re.DOTALL)
re_mail_addr = re.compile(r'Mailing\s+Address:\s+(.*?\d{5}(?:-\d{4})?)\n', re.MULTILINE | re.DOTALL)
re_phone = re.compile(r'\nPhone:[^\n\S]*(' + re_to_e164.pattern[1:] + r')\s*\n')
re_fax = re.compile(r'Fax:[^\n\S]*(' + re_to_e164.pattern[1:] + r')\s*\n')


def random_wait(min_wait=.1, max_wait=.3):
  return random.uniform(min_wait, max_wait)

def parse_jurisdiction(soup, jurisdiction_name, county_name, fipscode):
  city = re.sub(r'\s+Twp', ' Township', jurisdiction_name)
  county = county_name.title().strip()
  body = soup.find('div', class_='card-body')
  info = re.sub(r'\s*\n\s*', '\n', unicodedata.normalize('NFKD', body.text).strip())
  phys_addr = re_phys_addr.findall(info)
  mail_addr = re_mail_addr.findall(info)
  return {
    'locale': f'{city}:{county}',
    'city': city,
    'county': county,
    'emails': [a['href'].replace('mailto:', '').strip() for a in body.select("a[href^=mailto]")],
    'phones': [match[0] for match in re_phone.findall(info)],
    'faxes': [match[0] for match in re_fax.findall(info)],
    'official': re_official.findall(info)[0],
    'address': mail_addr[0].replace('\n', ', ') if mail_addr else None,
    'physicalAddress': phys_addr[0].replace('\n', ', ') if phys_addr else None,
    'fipscode': fipscode,
  }


def fetch_data(verbose=True):
  data = []
  text = cache_request(BASE_URL, verify=SSL_CERT)
  soup = BeautifulSoup(text, 'html.parser')
  for county in tqdm(soup.find('select', id='Counties')('option'), disable=not verbose):
    if not county.get('value'):
      continue
    county_text = cache_request(
      f'{BASE_URL}/SearchByCounty',
      method='POST',
      data={'CountyID': county.get('value')},
      wait=random_wait(),
      verify=SSL_CERT
    )
    county_soup = BeautifulSoup(county_text, 'html.parser')
    for jurisdiction_a in county_soup('a', class_='local-clerk-link'):
      qrystr_params = parse_qs(urlparse(jurisdiction_a.get('href')).query)
      jurisdiction_data = {k: v[0] for k, v in qrystr_params.items() if k != 'dummy'}
      jurisdiction_text = cache_request(
        f'{BASE_URL}/LocalClerk',
        method='POST',
        data=jurisdiction_data,
        wait=random_wait(),
        verify=SSL_CERT
      )
      jurisdiction_soup = BeautifulSoup(jurisdiction_text, 'html.parser')
      data.append(parse_jurisdiction(
        jurisdiction_soup,
        jurisdiction_data['jurisdictionName'],
        county.text,
        fipscode=jurisdiction_data['jurisdictionCode']
      ))

  return data


if __name__ == '__main__':
  print(fetch_data())
