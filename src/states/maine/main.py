import csv
from io import StringIO
from common import cache_request, to_list

BASE_URL = 'https://www.maine.gov/tools/whatsnew/index.php?topic=cec_clerks_registrars&v=text'


def record(datum):
  return {
    'locale': datum[0],
    'city': datum[0],
    'official': datum[1],
    'address': datum[2:5],
    'phones': to_list(datum[5]),
    'faxes': to_list(datum[6]),
  }


def fetch_data():
  text = cache_request(BASE_URL)
  if text.startswith('<plaintext>'):
    text = text[len('<plaintext>'):]
  reader = csv.reader(StringIO(text), delimiter='|')
  csv_data = [line for line in reader if line]

  json_data = [record(datum) for datum in csv_data]
  return json_data


if __name__ == '__main__':
  print(fetch_data())
