import re
import json
import random
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from tqdm import tqdm
from common import fetch_pdf_text, cache_request, to_list, re_to_e164

BASE_URL = 'https://elections.wi.gov/clerks/directory'
POST_URL = 'https://myvote.wi.gov/DesktopModules/GabMyVoteModules/api/WhereDoIVote/SearchPollingPlace'

re_city_chunk = re.compile(r'((?:CITY|TOWN|VILLAGE)\s+OF.+?)(?=\n(?:CITY|TOWN|VILLAGE) OF|Page \d+ of \d+)', re.DOTALL)
city_county_re = re.compile(r'(CITY|TOWN|VILLAGE)\s+OF\s+([A-Z.\- \n]+)\s+-\s+([A-Z.\- \n]+\s+COUNTY|MULTIPLE\s+COUNTIES)')
clerk_re = re.compile(r'CLERK: (.*)')
deputy_clerk_re = re.compile('DEPUTY CLERK: (.*)')
municipal_address_re = re.compile(r'Municipal Address :([^:]+\n)+')
mailing_address_re = re.compile(r'Mailing Address :([^:]+\n)+')
phone_re = re.compile(r'Phone(?:\s*\d*)?:\s*(' + re_to_e164.pattern[1:] + ')')
fax_re = re.compile(r'Fax:\s*(' + re_to_e164.pattern[1:] + ')')
url_re = re.compile(r'(https?://[^\s/$.?#].[^\s]*)')
# actual data has included non-WI state addresses
re_addr = re.compile(r'^(.+?),\s*(.+?),?\s*([A-Za-z]{2})\.?\s*([\d-]+)', re.IGNORECASE)


def first_group(regex, text):
  match = regex.search(text)
  return match.group(1).strip() if match else None


def strip_newline(string):
  return string.replace('\n', '')


def parse_city(text):
  match = city_county_re.search(text)
  ret = {
    'key': match.group(0).strip(),
    'city_type': match.group(1),
    'city': match.group(2),
    'county': match.group(3),
    'clerk': first_group(clerk_re, text),
    'deputy_clerk': first_group(deputy_clerk_re, text),
    'municipal_address': first_group(municipal_address_re, text),
    'mailing_address': first_group(mailing_address_re, text),
    'phones': phone_re.findall(text),
    'fax': first_group(fax_re, text),
    'url': first_group(url_re, text),
  }
  return {k: strip_newline(v).title() if isinstance(v, str) else v for k, v in ret.items()}


def parse_pdf(verbose=True):
  html = cache_request(BASE_URL)
  soup = BeautifulSoup(html, 'html.parser')
  pdf_url = soup.find('a', text=re.compile('^WI Municipal Clerks'))['href']
  text = fetch_pdf_text(pdf_url)
  return [parse_city(city_chunk) for city_chunk in tqdm(re_city_chunk.findall(text), disable=not verbose)]


def query_clerk_data(pdf_data, verbose=True):
  clerk_data = []
  for pdf_datum in tqdm(pdf_data, disable=not verbose):
    for field in ['municipal_address', 'mailing_address']:
      if pdf_datum.get(field):
        street, city, _, zipcode = re_addr.search(pdf_datum.get(field)).groups()
        post_data = {'addressLine': street, 'unit': "", 'city': city, 'zip': zipcode}
        result = cache_request(POST_URL, method='POST', data=post_data, wait=random.uniform(.1, .3))
        json_data = json.loads(result).get('Data') or {}
        if json_data.get('clerk'):
          for phfax_field in ['fax', 'phone1', 'phone2']:  # remove invalid phones/faxes
            json_data['clerk'][phfax_field] = '\n'.join(
              ''.join(phfax) for phfax in re_to_e164.findall(json_data['clerk'].get(phfax_field, ''))
            )
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


def fetch_data(verbose=True):
  pdf_data = parse_pdf(verbose=verbose)
  qry_data = query_clerk_data(pdf_data, verbose=verbose)
  data = aggregate(pdf_data, qry_data)
  return data


if __name__ == "__main__":
  print(fetch_data())
