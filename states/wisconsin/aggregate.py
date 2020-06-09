import json
import glob
import os
import re

import pandas as pd
import numpy as np


from common import dir_path


def aggregate(records):
  df_noemail = pd.DataFrame(records)

  df_muni = pd.DataFrame([row['muni_clerk'] for row in records if 'muni_clerk' in row]).dropna(axis=0, how='all')
  df_mail = pd.DataFrame([row['mail_clerk'] for row in records if 'mail_clerk' in row]).dropna(axis=0, how='all')
  df_muni['key'] = df_muni['jurisdictionName'].str.upper()
  df_mail['key'] = df_mail['jurisdictionName'].str.upper()

  df_fetched = pd.concat([
    df_muni.set_index('key'),
    df_mail.set_index('key'),
  ]).drop_duplicates()

  print(df_fetched.sample(n=5, random_state=42))

  df_noemail2 = df_noemail.set_index('key')
  fix_cols = ['city_type', 'city', 'county', 'clerk', 'deputy_clerk', 'municipal_address', 'mailing_address']
  for col in fix_cols:
    df_noemail2[col] = df_noemail2[col].str.title()

  df_master = df_noemail2.merge(df_fetched, on='key', how='left').reset_index()
  df_master['title_key'] = df_master['key'].str.title()

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

  df_output.to_json('public/wisconsin.json', orient='records')
