import re
import json
import random
from io import BytesIO
import pandas as pd
import numpy as np
import PyPDF2
from bs4 import BeautifulSoup
from tqdm import tqdm
from common import cache_request, to_list

BASE_URL = 'https://elections.wi.gov/clerks/directory'
POST_URL = 'https://myvote.wi.gov/DesktopModules/GabMyVoteModules/api/WhereDoIVote/SearchPollingPlace'

re_city_chunk = re.compile(r'((?:CITY|TOWN|VILLAGE)\s+OF.+?)(?=\n(?:CITY|TOWN|VILLAGE) OF|Page \d+ of \d+)', flags=re.DOTALL)
city_county_re = re.compile(r'(CITY|TOWN|VILLAGE)\s+OF\s+([A-Z.\- \n]+)\s+-\s+([A-Z.\- \n]+\s+COUNTY|MULTIPLE\s+COUNTIES)')
clerk_re = re.compile(r'CLERK: (.*)')
deputy_clerk_re = re.compile('DEPUTY CLERK: (.*)')
municipal_address_re = re.compile(r'Municipal Address :([^:]+\n)+')
mailing_address_re = re.compile(r'Mailing Address :([^:]+\n)+')
phone_re = re.compile(r'Phone \d: ([()\d-]+)')
fax_re = re.compile(r'Fax: ([()\d-]+)')
url_re = re.compile(r'(https?://[^\s/$.?#].[^\s]*)')
re_addr = re.compile(r'^(.+?),\s*(.+?),?\s*WI\.?\s*([\d-]+)', re.IGNORECASE)


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


def parse_pdf():
  html = cache_request(BASE_URL)
  soup = BeautifulSoup(html, 'html.parser')
  pdf_url = soup.find('a', text=re.compile('^WI Municipal Clerks'))['href']
  req = cache_request(pdf_url, is_binary=True)
  with BytesIO(req) as pdf_bytes:
    pdf_reader = PyPDF2.PdfFileReader(pdf_bytes)
    records = []
    for page_num in tqdm(range(pdf_reader.numPages)):
      text = pdf_reader.getPage(page_num).extractText()
      for city_chunk in re_city_chunk.findall(text):
        records.append(parse_city(city_chunk))
  return records


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


def fetch_data():
  pdf_data = parse_pdf()
  qry_data = query_clerk_data(pdf_data)
  data = aggregate(pdf_data, qry_data)
  return data


if __name__ == "__main__":
  print(fetch_data())
