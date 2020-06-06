from bs4 import BeautifulSoup

from common import cache_request, decode_email, normalize_state, diff_and_save

BASE_URL = 'https://dos.elections.myflorida.com/supervisors/'


def parse_county(soup):
  county = soup.find('p', class_='title').text.split('Supervisor')[0].strip()
  links = soup.find(id='rightContent')('a')
  return {
    'locale': county,
    'official': soup.find('span', class_='bigRed').text.replace(u'\xa0', ' ').split(',')[0].strip(),
    'emails': [decode_email(links[0].find('span', class_='__cf_email__').get('data-cfemail')).strip()],
    'url': links[1]['href'].strip(),
    'county': county,
  }


def main():
  data = []
  text = cache_request(BASE_URL)
  soup = BeautifulSoup(text, 'html.parser')
  for county_link in soup.select('a[href^=countyInfo]'):
    text = cache_request(BASE_URL + county_link['href'])
    data.append(parse_county(BeautifulSoup(text, 'html.parser')))

  data = normalize_state(data)
  diff_and_save(data, 'public/florida.json')


if __name__ == '__main__':
  main()
