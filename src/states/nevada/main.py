import unicodedata
import re
from bs4 import BeautifulSoup
from common import cache_webkit

BASE_URL = 'https://www.nvsos.gov/sos/elections/voters/county-clerk-contact-information'

re_county = re.compile(r'^([^\n]*?(?:CITY|COUNTY)[^\n]*?:.*?)(?=\n[^\n]*(?:CITY|COUNTY)(?![^\n]*Mailing))',
                       re.DOTALL + re.MULTILINE)
re_locale = re.compile(r'^(.*(?:CITY|COUNTY).*)(?=:)', re.MULTILINE)
re_official = re.compile(r'^.*\n(.*),.*\n')
re_address = re.compile(r'^[^\n]*\n[^\n]*\n(.*?[\d-]{5,10})\n', re.DOTALL)
re_phone = re.compile(r'(?<!FAX )\(\d{3}\) \d{3}-(?:\d{4}|VOTE)')
re_fax = re.compile(r'(?<=FAX )\(\d{3}\) \d{3}-(?:\d{4}|VOTE)')
re_email = re.compile(r'Email:\s*\n(.*)(?:\n|$)')
re_url = re.compile(r'Website:\s*\n(.*)(?:\n|$)')


def parse_county(text):
  locale = re_locale.findall(text)[0].title().replace('Elections Department', '').strip()
  init = {'city': locale} if locale.endswith('City') else {'county': locale}

  urls = re_url.findall(text)
  if urls:
    init['url'] = urls[0]

  return {
    **init,
    'locale': locale,
    'official': re_official.findall(text)[0],
    'address': re_address.findall(text)[0].replace('\n', ', '),
    'phones': re_phone.findall(text),
    'faxes': re_fax.findall(text),
    'emails': re_email.findall(text),
  }


def fetch_data():
  html = cache_webkit(BASE_URL)

  # watch for occasional captcha requirement (no current way around it)
  print(html)

  soup = BeautifulSoup(html, 'html.parser')
  text = soup.find('div', class_='content_area').get_text('\n', strip=True)
  text = unicodedata.normalize('NFKD', text)
  data = []
  for county_text in re_county.findall(f"{text}\nCOUNTY"):
    data.append(parse_county(county_text))
  return data


if __name__ == '__main__':
  print(fetch_data())
