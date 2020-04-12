import os
import json
from tqdm import tqdm
import requests

URL = 'https://myvote.wi.gov/DesktopModules/GabMyVoteModules/api/WhereDoIVote/SearchPollingPlace'

def fetch_clerk_results(address):
  parts = address.split(',')
  if len(parts) == 3:
    zipcode = parts[2].split('WI ')[1].strip()
    data = {'addressLine': parts[0].strip(), 'unit': "", 'city': parts[1].strip(), 'zip': zipcode}
  if len(parts) == 2:
    city, zipcode = parts[1].split(' WI ')
    data = {'addressLine': parts[0].strip(), 'unit': "", 'city': city, 'zip': zipcode}

  result = requests.post(URL, data=data)
  return result.json()


if __name__ == '__main__':
  with open('results/records.noemail.json') as fh:
    records = json.load(fh)
    print(len(records))
    [r['municipal_address'] for r in records if len(r['municipal_address'].split(',')) != 3]

  for record in tqdm(records[:None]):
    key = record['key']
    file_name = f'results/municipal_address/{key}.json'
    if os.path.isfile(file_name):
      continue
    data = fetch_clerk_results(record['municipal_address'])
    with open(file_name, 'w') as fh:
      json.dump(data, fh)

    # Really care about ['Data']['clerk']
