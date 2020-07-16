import csv
import re
from io import StringIO
from common import cache_request, to_list

BASE_URL = 'https://www.maine.gov/tools/whatsnew/index.php?topic=cec_clerks_registrars&v=text'

re_phone_fax = re.compile(r'\d{3}\D*?\d{3}\D*?\d{4}')


def parse_locale(datum):
  # some locales use an extra column for address
  if datum[5].strip() and re_phone_fax.search(datum[5]) is None:
    addr = datum[2:6]
    datum.pop(5)
  else:
    addr = datum[2:5]

  return {
    'locale': datum[0],
    'city': datum[0],
    'official': datum[1],
    'address': ', '.join(x.strip() for x in addr if x),
    'phones': to_list(datum[5]),
    'faxes': to_list(datum[6]),
  }


def fetch_data():
  text = cache_request(BASE_URL)
  if text.startswith('<plaintext>'):
    text = text[len('<plaintext>'):]
  reader = csv.reader(StringIO(text), delimiter='|')
  return [parse_locale(datum) for datum in reader if datum]


if __name__ == '__main__':
  print(fetch_data())
