import random
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
from common import cache_request

BASE_URL = 'https://tnsos.org/elections/election_commissions.php'

re_dense_lines = re.compile(r'\s*\n\s*')
re_official = re.compile(r'Administrator:\n(.+)\n')
re_email = re.compile(r'\S+@\S+.\S')
re_fax = re.compile(r"Fax:\n?(\(?\d{3}\)?[\.\-\s]*\d{3}[\.\-\s]*\d{4})")
re_phone = re.compile(r"Phone:\n?(\(?\d{3}\)?[\.\-\s]*\d{3}[\.\-\s]*\d{4})")
re_url = re.compile(r"Web\s*Site:\n?(\S+?)\n")
re_mailing_addr = re.compile(r"\nMailing\s+Address:\n(.+?)\s*(\d{5}(?:-\d{4})?)\s*\n", re.MULTILINE | re.DOTALL)
re_physical_addr = re.compile(r"\nAddress:\n(.+?)\s*(\d{5}(?:-\d{4})?)\s*\n", re.MULTILINE | re.DOTALL)


def parse_addr(matches):
  if matches:
    return matches[0][0].replace('\n', ', ') + ', TN ' + matches[0][1]
  return None


def fetch_county(county_name):
  locale = f"{county_name} County"
  html = cache_request(f"{BASE_URL}?County={county_name}", wait=random.uniform(.5, 1.5))
  soup = BeautifulSoup(html, 'lxml')
  table = soup.select_one('table#data')
  text = re_dense_lines.sub('\n', table.get_text('\n'))
  url = re_url.findall(text)
  return {
    'locale': locale,
    'county': locale,
    'official': re_official.findall(text)[0],
    'emails': re_email.findall(text),
    'faxes': re_fax.findall(text),
    'phones': re_phone.findall(text),
    'url': url[0] if url else None,
    'address': parse_addr(re_mailing_addr.findall(text)),
    'physicalAddress': parse_addr(re_physical_addr.findall(text)),
  }


def fetch_data(verbose=True):
  html = cache_request(BASE_URL)
  soup = BeautifulSoup(html, 'lxml')
  counties = [option['value'] for option in soup.select('select>option') if option['value']]
  return [fetch_county(county_name) for county_name in tqdm(counties, disable=not verbose)]


if __name__ == '__main__':
  print(fetch_data())
