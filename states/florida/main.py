from bs4 import BeautifulSoup

from common import dir_path, cache_request, decode_email, diff_and_save

BASE_URL = 'https://dos.elections.myflorida.com/supervisors/'


def parse_county(soup, county_link):
  # step 1: scrape raw county data
  # (originally used artoo and saved in individual json files)
  datum = {}
  datum['county'] = county_link.split('=')[1]
  datum['name'] = soup.find('span', class_='bigRed').text
  datum['title'] = soup.find('p', class_='title').text
  links = soup.find(id='rightContent')('a')
  datum['email'] = decode_email(links[0].find('span', class_='__cf_email__').get('data-cfemail'))
  datum['url'] = links[1]['href']

  # step 2: parse raw scraped county data
  county = datum['title'].split('Supervisor')[0].strip()
  return {
    'locale': county,
    'official': datum['name'].replace(u'\xa0', ' ').split(',')[0].strip(),
    'emails': [datum['email'].strip()], # no longer need to strip mailto:
    'url': datum['url'],
    'county': county,
  }

if __name__ == '__main__':
  data = []

  text = cache_request(BASE_URL)
  soup = BeautifulSoup(text, 'html.parser')

  # links to county pages
  county_links = map(lambda x: x['href'], soup.select('a[href^=countyInfo]'))
  for county_link in county_links:
    text = cache_request(BASE_URL+county_link)
    data.append(parse_county(BeautifulSoup(text, 'html.parser'), county_link))
  print("Florida # of counties: {}".format(len(data)))

  # sort by locale for consistent ordering
  data.sort(key=lambda x: x['locale'])

  diff = diff_and_save(data, 'public/florida.json')
  print("Florida diff: {}".format(diff))