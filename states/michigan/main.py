import json
import urllib.parse as urlparse
from urllib.parse import parse_qs
import os

from common import to_list, dir_path, normalize_state, diff_and_save


def filter_dict_by_key(d, keys):
  keys = set(keys)
  return { k: v for k, v in d.items() if k in keys}

def secondary_parse():
  output = []

  with open('cache/Michigan.jl') as fh:
    for line in fh:
      data = json.loads(line)

      if data['type'] != 'local':
        continue

      value = filter_dict_by_key(
        data,
        {'clerk', 'email', 'phone', 'fax'}
      )

      value['county'] = data['CountyName']
      value['city'] = data['jurisdictionName']

      # rename Twp to Township
      if value['city'].endswith('Twp'):
        value['city'] = value['city'][:-3] + 'Township'

      county = value['county'].title().strip()

      output += [{
        'locale': value['city'] + ':' + county,
        'city': value['city'],
        'county': county,
        'emails': to_list(value['email']),
        'phones': to_list(value['phone']),
        'faxes': to_list(value['fax']),
        'official': value['clerk'],
      }]

  with open('public/michigan.json', 'w') as fh:
    json.dump(output, fh)
  
if __name__ == '__main__':
  command = "scrapy runspider states/michigan/old/Michigan.py --logfile cache/Michigan.log.txt -o cache/Michigan.jl"
  return_code = os.system(command)

  secondary_parse()
  #normalize_state(data)
  #diff_and_save(data, 'public/michigan.json')
