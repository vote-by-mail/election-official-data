import re
from bs4 import BeautifulSoup
from common import cache_request

URL = 'https://www.dcboe.org/Voters/Absentee-Voting/Request-an-Absentee-Ballot'

re_fax = re.compile(r"fax(?:\s+to)?\s*([\d\-\.]+)")
re_phone = re.compile(r"\(?\d{3}\)?[\.\-\s]*\d{3}[\.\-\s]*\d{4}")
re_email = re.compile(r"\S+@\S+.\S+")


def fetch_data(verbose=True):  # pylint: disable=unused-argument
  html = cache_request(URL)
  soup = BeautifulSoup(html, 'html.parser')
  text = soup.find(class_='dcboeContent').get_text('\n')
  faxes = re_fax.findall(text)
  return [{
    'locale': 'All',
    'emails': re_email.findall(text),
    'phones': [phone for phone in re_phone.findall(text) if phone not in faxes],
    'faxes': faxes,
  }]


if __name__ == '__main__':
  print(fetch_data())
