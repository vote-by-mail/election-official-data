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
re_addr = re.compile(r"Address:\n((?:[^\n]+\n)+)Phone")


def fetch_county(county_name):
  locale = f"{county_name} County"
  html = cache_request(f"{BASE_URL}?County={county_name}", wait=random.uniform(.5, 1.5))
  soup = BeautifulSoup(html, 'lxml')
  table = soup.select_one('table#data')
  text = re_dense_lines.sub('\n', table.get_text('\n'))
  url = re_url.findall(text)
  addr = re_addr.findall(text)
  return {
    'locale': locale,
    'county': locale,
    'official': re_official.findall(text)[0],
    'emails': re_email.findall(text),
    'faxes': re_fax.findall(text),
    'phones': re_phone.findall(text),
    'url': url[0] if url else None,
    'address': addr[0].strip().replace('\n', ', ') if addr else None,
  }


def fetch_data():
  html = cache_request(BASE_URL)
  soup = BeautifulSoup(html, 'lxml')
  counties = [option['value'] for option in soup.select('select>option') if option['value']]
  return [fetch_county(county_name) for county_name in tqdm(counties)]


if __name__ == '__main__':
  print(fetch_data())
