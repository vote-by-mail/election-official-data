import os
import re
import json
import random
from tqdm import tqdm
import requests

from common import dir_path, cache_request

POST_URL = 'https://myvote.wi.gov/DesktopModules/GabMyVoteModules/api/WhereDoIVote/SearchPollingPlace'

re_addr = re.compile(r'^(.+?),\s*(.+?),?\s*WI\.?\s*([\d-]+)')


def fetch_clerk_results(address):
  street, city, zipcode = re_addr.search(address).groups()
  data = {'addressLine': street, 'unit': "", 'city': city, 'zip': zipcode}
  result = cache_request(POST_URL, method='POST', data=data, wait=random.uniform(.1,.3))
  json_data = json.loads(result)
  datum = json_data.get('Data') or {}
  return datum.get('clerk') or {}


def augment(records):
  for record in tqdm(records):
    key = record['key']
    if record['municipal_address']:
      record['muni_clerk'] = fetch_clerk_results(record['municipal_address'])
    if record['mailing_address']:
      record['mail_clerk'] = fetch_clerk_results(record['mailing_address'])
  return records