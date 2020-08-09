from bs4 import BeautifulSoup
from tqdm import tqdm
from common import init_selenium_driver, cache_selenium

BASE_URL = 'https://dos.elections.myflorida.com/supervisors/'


def fetch_and_parse_county(county_url, driver):
  html = cache_selenium(county_url, wait=1, driver=driver)
  soup = BeautifulSoup(html, 'html.parser')
  county = soup.find('p', class_='title').text.split('Supervisor')[0].strip()
  links = soup.find(id='rightContent')('a')
  return {
    'locale': county,
    'official': soup.find('span', class_='bigRed').text.replace(u'\xa0', ' ').split(',')[0].strip(),
    'emails': [links[0]['href'].replace('mailto:', '').strip()],
    'url': links[1]['href'].strip(),
    'county': county,
  }


def fetch_data(verbose=True):
  driver = init_selenium_driver()  # will be using repeatedly
  html = cache_selenium(BASE_URL, driver=driver)
  soup = BeautifulSoup(html, 'html.parser')
  county_links = soup.select('a[href^=countyInfo]')
  assert len(county_links) > 0, ('No county links found in the following HTML:\n' + '#'*30 + html + '#'*30)
  data = [fetch_and_parse_county(BASE_URL + county_link['href'], driver)
          for county_link in tqdm(county_links, disable=not verbose)]
  driver.close()
  return data


if __name__ == '__main__':
  print(fetch_data())
