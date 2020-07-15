from common import cache_request

BASE_URL = 'https://sos.vermont.gov/elections/town-clerks/'
XLSX_URL = 'https://sos.vermont.gov/media/fyvdm1j0/clerkcontactinfoexcel.xlsx'


def fetch_data():
  xlsx = cache_request(XLSX_URL, is_binary=True)
  print(xlsx)
  #data = pd.read_excel(xlsx) #.fillna(method='ffill').apply(lambda x: x.str.strip())
  #print(data)
  return [{'locale': 'dummy'}]


if __name__ == '__main__':
  print(fetch_data())
