import os
import json
from tqdm import tqdm
import requests

from common import dir_path

URL = 'https://myvote.wi.gov/DesktopModules/GabMyVoteModules/api/WhereDoIVote/SearchPollingPlace'


def fetch_clerk_results(address):
  parts = address.split(',')
  if len(parts) == 3:
    zipcode = parts[2].split('WI ')[1].strip()
    data = {'addressLine': parts[0].strip(), 'unit': "", 'city': parts[1].strip(), 'zip': zipcode}
  if len(parts) == 2:
    try:
      city, zipcode = parts[1].split(' WI ')
    except ValueError:
      city, zipcode = parts[1].split(' WI. ')  # some mistakes in the file
    data = {'addressLine': parts[0].strip(), 'unit': "", 'city': city, 'zip': zipcode}

  result = requests.post(URL, data=data)
  return result.json()


def save_data(address, file_name):
  if os.path.isfile(file_name):
    return
  data = fetch_clerk_results(address)
  with open(file_name, 'w') as fh:
    json.dump(data, fh)


def main():
  with open(dir_path(__file__) + '/results/records.noemail.json') as fh:
    records = json.load(fh)

  for record in tqdm(records[:None]):
    key = record['key']
    if record['municipal_address']:
      save_data(
        record['municipal_address'],
        dir_path(__file__) + f'/results/municipal_address/{key}.json',
      )

    if record['mailing_address']:
      save_data(
        record['mailing_address'],
        dir_path(__file__) + f'/results/mailing_address/{key}.json',
      )

    # Really care about ['Data']['clerk']


if __name__ == '__main__':
  main()
