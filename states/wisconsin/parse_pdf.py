import re
from io import BytesIO
import PyPDF2
from bs4 import BeautifulSoup
from tqdm import tqdm

from common import cache_request

BASE_URL = 'https://elections.wi.gov/clerks/directory'

re_city_chunk = re.compile(r'((?:CITY|TOWN|VILLAGE)\s+OF.+?)(?=\n(?:CITY|TOWN|VILLAGE) OF|Page \d+ of \d+)', flags=re.DOTALL)
city_county_re = re.compile(r'(CITY|TOWN|VILLAGE)\s+OF\s+([A-Z.\- \n]+)\s+-\s+([A-Z.\- \n]+\s+COUNTY|MULTIPLE\s+COUNTIES)')
clerk_re = re.compile(r'CLERK: (.*)')
deputy_clerk_re = re.compile('DEPUTY CLERK: (.*)')
municipal_address_re = re.compile(r'Municipal Address :([^:]+\n)+')
mailing_address_re = re.compile(r'Mailing Address :([^:]+\n)+')
phone_re = re.compile(r'Phone \d: ([()\d-]+)')
fax_re = re.compile(r'Fax: ([()\d-]+)')
url_re = re.compile(r'(https?://[^\s/$.?#].[^\s]*)')


def first_group(regex, text):
  match = regex.search(text)
  return match.group(1).strip() if match else None


def strip_newline(string):
  return string.replace('\n', '')


def parse_city(text):
  match = city_county_re.search(text)
  ret = {
    'key': match.group(0).strip(),
    'city_type': match.group(1),
    'city': match.group(2),
    'county': match.group(3),
    'clerk': first_group(clerk_re, text),
    'deputy_clerk': first_group(deputy_clerk_re, text),
    'municipal_address': first_group(municipal_address_re, text),
    'mailing_address': first_group(mailing_address_re, text),
    'phones': phone_re.findall(text),
    'fax': first_group(fax_re, text),
    'url': first_group(url_re, text),
  }
  return {k: strip_newline(v) if isinstance(v, str) else v for k, v in ret.items()}

def parse_pdf():
  html = cache_request(BASE_URL)
  soup = BeautifulSoup(html, 'html.parser')
  pdf_url = soup.find('a', text=re.compile('^WI Municipal Clerks'))['href']
  req = cache_request(pdf_url, is_binary=True)
  with BytesIO(req) as pdf_bytes:
    pdf_reader = PyPDF2.PdfFileReader(pdf_bytes)
    records = []
    for page_num in tqdm(range(pdf_reader.numPages)):
      text = pdf_reader.getPage(page_num).extractText()
      for city_chunk in re_city_chunk.findall(text):
        records.append(parse_city(city_chunk))
  return records
