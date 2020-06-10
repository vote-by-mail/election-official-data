import re
import json
import random
import pandas as pd
import numpy as np
from tqdm import tqdm
from common import cache_request, to_list, normalize_state, diff_and_save
import parse_pdf

POST_URL = 'https://myvote.wi.gov/DesktopModules/GabMyVoteModules/api/WhereDoIVote/SearchPollingPlace'

re_addr = re.compile(r'^(.+?),\s*(.+?),?\s*WI\.?\s*([\d-]+)', re.IGNORECASE)


def query_clerk_data(pdf_data):
  clerk_data = []
  for pdf_datum in tqdm(pdf_data):
    for field in ['municipal_address', 'mailing_address']:
      if pdf_datum.get(field):
        street, city, zipcode = re_addr.search(pdf_datum.get(field)).groups()
        post_data = {'addressLine': street, 'unit': "", 'city': city, 'zip': zipcode}
        result = cache_request(POST_URL, method='POST', data=post_data, wait=random.uniform(.1, .3))
        json_data = json.loads(result).get('Data') or {}
        if json_data.get('clerk'):
          clerk_data.append(json_data['clerk'])
  return clerk_data


def split_emails(cell):
  if isinstance(cell, str):
    return [email for email in re.split(r'\s*[;,]\s*', cell.strip()) if email]
  return []


def aggregate(pdf_data, qry_data):
  # merge dataframes
  df_pdf = pd.DataFrame(pdf_data)
  df_qry = pd.DataFrame(qry_data).dropna(axis=0, how='all').drop_duplicates()
  df_qry = df_qry.rename({
    'fax': 'faxes',
    'muncipalAddress': 'physicalAddress',
    'mailingAddress': 'address',
    'clerkName': 'official',
    'jurisdictionName': 'locale',
  }, axis=1)
  df_qry['key'] = df_qry['locale'].str.title()
  df_merged = df_pdf.merge(df_qry, on='key', how='left').reset_index(drop=True)

  # merge columns
  df_final = pd.DataFrame()
  col_pairs = [
    ('physicalAddress', 'municipal_address'),
    ('address', 'mailing_address'),
    ('official', 'clerk'),
    ('faxes', 'fax'),
    ('locale', 'key'),
  ]
  for first, second in col_pairs:
    df_final[first] = df_merged[first].where(df_merged[first].notnull(), df_merged[second])

  # clean up columns
  df_final['locale'] = df_final['locale'].str.replace(' - ', ':').str.replace(' Of ', ' of ')
  df_final['locale'] = df_final['locale'].str.replace('Multiple Counties', '').str.strip()
  df_final['city'] = (df_merged['city_type'] + ' of ' + df_merged['city']).str.strip()
  df_final['county'] = df_merged['county'].replace('Multiple Counties', np.nan).str.strip()
  df_final['faxes'] = df_final['faxes'].apply(to_list)
  df_final['emails'] = (df_merged['email'] + '; ' + df_merged['notificationEmail']).apply(split_emails)

  df_final = df_final.where(pd.notnull(df_final), None)
  return df_final.to_dict(orient='records')


def main():
  pdf_data = parse_pdf.parse_pdf()
  qry_data = query_clerk_data(pdf_data)
  data = aggregate(pdf_data, qry_data)
  data = normalize_state(data)
  diff_and_save(data, 'public/wisconsin.json')


if __name__ == "__main__":
  main()
