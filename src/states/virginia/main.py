import random
from bs4 import BeautifulSoup
from tqdm import tqdm
from common import cache_request

BASE_URL = 'https://vote.elections.virginia.gov/VoterInformation/PublicContactLookup'


def get_locality_ids():
  page = cache_request(BASE_URL)
  soup = BeautifulSoup(page, 'lxml')
  return [option['value'] for option in soup.select('select>option') if option['value']]


def get_locality_datum(id_):
  page = cache_request(
    BASE_URL,
    method='POST',
    data={'LocalityUid': id_},
    wait=random.uniform(.5, 1.5),
  )
  soup = BeautifulSoup(page, 'lxml')
  keys = soup.select('.resultsWrapper')[0].select('h5.display-lable')
  vals = soup.select('.resultsWrapper')[0].select('p.display-field')
  results = {key.text.strip(): val.text.strip() for key, val in zip(keys, vals)}
  locale = soup.select('select > option[selected="selected"]')[0].text.title()
  final = {
    'locale': locale,
    'county': locale if locale.endswith('County') else None,
    'city': locale if not locale.endswith('County') else None,
    'official': results['Registrar'],
    'emails': [results['Email']],
    'faxes': [results['Fax']],
    'url': results.get('URL'),
    'address': results.get('Mailing Address') or results.get('Address'),
    'physicalAddress': results.get('Physical Address'),
  }
  return {k: v for k, v in final.items() if v}


def fetch_data():
  ids = get_locality_ids()
  locality_data = [get_locality_datum(id_) for id_ in tqdm(ids)]
  return locality_data


if __name__ == '__main__':
  print(fetch_data())
