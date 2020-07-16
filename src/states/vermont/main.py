import os
import os.path
from ediblepickle import checkpoint
import pandas as pd
import wget
from common import key_namer, work_dir, to_list

BASE_URL = 'https://sos.vermont.gov/elections/town-clerks/'
XLSX_URL = 'https://sos.vermont.gov/media/fyvdm1j0/clerkcontactinfoexcel.xlsx'


def vermont_key_namer(args, kwargs):
  key_kwargs = kwargs.copy()
  key_kwargs['state'] = 'vermont'
  return key_namer(args, key_kwargs)


@checkpoint(key=vermont_key_namer, work_dir=work_dir)
def cache_xlsx(url=XLSX_URL):  # use a keyword arg for key namer
  xlsx_path = wget.download(url, out=work_dir)
  xlsx_path = os.path.abspath(xlsx_path)
  with open(xlsx_path, mode='rb') as xlsx_file:
    xlsx = xlsx_file.read()
  os.remove(xlsx_path)
  return xlsx


def parse_xlsx(xlsx):
  xlsx_df = pd.read_excel(xlsx, skiprows=[0], dtype=str)
  xlsx_df = xlsx_df.where(xlsx_df.notna(), '').apply(lambda x: x.str.strip())
  data = pd.DataFrame()
  data['city'] = xlsx_df['Town']
  data['county'] = xlsx_df['County'] + ' County'
  data['locale'] = xlsx_df['County'] + ':' + xlsx_df['Town']
  data['official'] = xlsx_df.apply(lambda x: x['First'] + ' ' + x['Last'] if x['First'] != 'Vacant' else None, axis=1)
  data['phones'] = xlsx_df['Office Phone'].apply(to_list)
  data['faxes'] = xlsx_df['Office Fax'].apply(to_list)
  data['emails'] = xlsx_df["Clerk's Email Address"].str.split(' or ')
  data['address'] = (xlsx_df['Office Mailing Address'] + ', ' + xlsx_df['City/Town:']
                     + ', ' + xlsx_df['State:'] + ' ' + xlsx_df['ZIP:'])
  data['physicalAddress'] = (xlsx_df['Physical Address'] + ', ' + xlsx_df['City/Town:.1']
                             + ', ' + xlsx_df['State:.1'] + ' ' + xlsx_df['ZIP:.1'])
  return data.to_dict(orient='records')


def fetch_data():
  xlsx = cache_xlsx()
  return parse_xlsx(xlsx)


if __name__ == '__main__':
  print(fetch_data())
