import re
import json
import random

import pandas as pd
import numpy as np
from deepdiff import DeepDiff
from tqdm import tqdm

import parse_pdf

from common import cache_request, normalize_state, diff_and_save

POST_URL = 'https://myvote.wi.gov/DesktopModules/GabMyVoteModules/api/WhereDoIVote/SearchPollingPlace'

re_addr = re.compile(r'^(.+?),\s*(.+?),?\s*WI\.?\s*([\d-]+)', re.IGNORECASE)


def fetch_clerk_results(address):
  street, city, zipcode = re_addr.search(address).groups()
  data = {'addressLine': street, 'unit': "", 'city': city, 'zip': zipcode}
  result = cache_request(POST_URL, method='POST', data=data, wait=random.uniform(.1, .3))
  json_data = json.loads(result)
  datum = json_data.get('Data') or {}
  return datum.get('clerk') or {}


def aggregate(no_email, muni_clerk, mail_clerk):
  df_noemail = pd.DataFrame(no_email)

  df_muni = pd.DataFrame([row for row in muni_clerk if row]).dropna(axis=0, how='all')
  df_mail = pd.DataFrame([row for row in mail_clerk if row]).dropna(axis=0, how='all')
  df_muni['key'] = df_muni['jurisdictionName'].str.upper()
  df_mail['key'] = df_mail['jurisdictionName'].str.upper()

  df_fetched = pd.concat([
    df_muni.set_index('key'),
    df_mail.set_index('key'),
  ]).drop_duplicates()

  df_noemail2 = df_noemail.set_index('key')
  fix_cols = ['city_type', 'city', 'county', 'clerk', 'deputy_clerk', 'municipal_address', 'mailing_address']
  for col in fix_cols:
    df_noemail2[col] = df_noemail2[col].str.title()

  df_master = df_noemail2.merge(df_fetched, on='key', how='left').reset_index()
  df_master['title_key'] = df_master['key'].str.title()

  #try first else use second
  def merge_all_cols(df, pairs):
    return pd.DataFrame({
      first: df[first].where(df[first].notnull(), df[second])
      for first, second in pairs
    })

  df_final = pd.concat([
    merge_all_cols(df_master, [
      ['muncipalAddress', 'municipal_address'],
      ['mailingAddress', 'mailing_address'],
      ['clerkName', 'clerk'],
      ['fax_y', 'fax_x'],
      ['jurisdictionName', 'title_key']
    ]),
    df_master[['email', 'notificationEmail', 'county']],
  ], axis=1).rename({
    'fax_y': 'fax',
    'city_type': 'cityType'
  }, axis=1)

  df_final['city'] = df_master['city_type'] + ' of ' + df_master['city']

  df_output = df_final[
    ['muncipalAddress', 'mailingAddress', 'clerkName', 'jurisdictionName', 'county', 'city']
  ].rename({
    'muncipalAddress': 'physicalAddress',
    'mailingAddress': 'address',
    'clerkName': 'official',
    'jurisdictionName': 'locale',
  }, axis=1)

  def to_list(df):
    return df.apply(
      lambda row: list(set(
        email.strip()
        for cell in row
        if pd.notnull(cell)
        if cell
        for email in re.split(';|,', cell)
        if email
      )),
      axis=1
    )

  df_output['county'] = df_output['county'].replace('Multiple Counties', np.nan).str.strip()
  df_output['locale'] = df_output['locale'].str.replace(' - ', ':').str.replace(' Of ', ' of ')
  df_output['locale'] = df_output['locale'].str.replace('Multiple Counties', '').str.strip()
  df_output['city'] = df_output['city'].str.strip()

  df_output['faxes'] = to_list(df_final[['fax']])
  df_output['emails'] = to_list(df_final[['email', 'notificationEmail']])

  return json.loads(df_output.to_json(orient='records'))


def main():
  data = parse_pdf.parse_pdf()
  print('\n')
  muni_clerk = []
  mail_clerk = []
  for record in tqdm(data):
    if record['municipal_address']:
      muni_clerk.append(fetch_clerk_results(record['municipal_address']))
    if record['mailing_address']:
      mail_clerk.append(fetch_clerk_results(record['mailing_address']))
  data = aggregate(data, muni_clerk, mail_clerk)
  data = normalize_state(data)
  diff_and_save(data, 'public/wisconsin.json')
  #records = aggregate.aggregate(records)

  with open('public/wisconsin_old.json', 'r') as f:
    old_data = json.load(f)
  old_data = normalize_state(old_data)
  old_data = {x['locale']:x for x in old_data}

  with open('public/wisconsin.json', 'r') as f:
    new_data = json.load(f)
  new_data = normalize_state(new_data)
  new_data = {x['locale']:x for x in new_data}

  print(f'{len(old_data)}, {len(new_data)}')

  diff = DeepDiff(old_data, new_data)
  for k, v in diff.items():
    print(k, len(v))
  '''
  for k, v in diff.items():
    print(f'\n\n******\n{k}\n******')
    if isinstance(v, dict):
      for k2, v2 in v.items():
        print(k2, v2)
    else:
      for v2 in v:
        print(v2)
  '''


if __name__ == "__main__":
  main()
