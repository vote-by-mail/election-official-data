from common import cache_request
import csv
import json
from io import StringIO

def record(datum):
  return {
    'county': datum[0],
    'name': datum[1],
    'address': datum[2:5],
    'phone': datum[5],
    'fax': datum[6],
  }

if __name__ == '__main__':
  text = cache_request('https://www.maine.gov/tools/whatsnew/index.php?topic=cec_clerks_registrars&v=text')
  if text.startswith('<plaintext>'):
    text = text[len('<plaintext>'):]
  reader = csv.reader(StringIO(text), delimiter='|')
  csv_data = [line for line in reader if line]

  json_data = [record(datum) for datum in csv_data]
  with open('public/maine.json', 'w') as fh:
    json.dump(json_data, fh)
