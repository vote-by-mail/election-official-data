import re
import json
import unicodedata
from collections import OrderedDict
from bs4 import BeautifulSoup
from common import cache_request

BASE_URL = 'https://www.votespa.com/Resources/Pages/Contact-Your-Election-Officials.aspx'

re_county = re.compile(
  r'\s*Contact.*\n'
  r'(?:\s*?(?:(Ms.\s*?\n)?(?P<official>.*?)\s*?\n)?'
  r'(?:.*(?:Director|Manager|Secretary|Supervisor|Clerk|Designee'
    r'|Coordinator|Administrator|Registrar).*\n))?'
  r'\s*(?P<addr>(?:.*\n)*.*\d{5}(?:-\d{4})?)\s*?\n'
  r'\s*(?P<phone>\D*\d{3}\D*\d{3}\D*\d{4}.*?)\s*?$'  # include extension
  r'\n?(?:.*\n)*?'  # ignore extra lines in between
  r'\n?\s*(?P<email>[\w\-\.]+@[\w\-\.]+\.[a-zA-Z]{2,5})?\s*$',
  re.MULTILINE
)


def use_last_value(ord_dict, key):
  for item in reversed(ord_dict.values()):
    if item[key]:
      return item[key]
  return None


def use_all_values(ord_dict, key):
  return [item[key] for item in ord_dict.values() if item[key]]


def parse_county(county):
  fields = {field['FieldName']: field['FieldContent'] for field in county}
  matches = OrderedDict([('Election', None), ('Voter Registration', None)])
  for field_name in matches.keys():
    text = BeautifulSoup(fields[field_name], 'html.parser').get_text('\n')
    text = unicodedata.normalize('NFKC', re.sub(r'\s*\n\s*', r'\n', text.strip()))
    matches[field_name] = re_county.search(text).groupdict()
  return {
    'locale': fields['Title'],
    'county': fields['Title'],
    'official': use_last_value(matches, 'official'),
    'phones': use_all_values(matches, 'phone'),
    # no fax numbers provided
    'emails': use_all_values(matches, 'email'),
    'address': use_last_value(matches, 'addr').replace('\n', ', '),
    'url': fields.get('County Website'),
  }


def fetch_data(verbose=True):  # pylint: disable=unused-argument
  html = cache_request(BASE_URL).replace(u'\u200b', ' ')
  json_str = re.findall(r'CountyMap.MapPopup.init\(({.*?})\)', html)[0]
  raw_data = json.loads(json_str)['data']['Items']
  return [parse_county(county) for county in raw_data.values()]


if __name__ == '__main__':
  print(fetch_data())
