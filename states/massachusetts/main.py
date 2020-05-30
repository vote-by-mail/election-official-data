from bs4 import BeautifulSoup
import json

def parse_html(html):
  soup = BeautifulSoup(html, 'html.parser')
  raw_clerk_data = [x.text for x in soup.select_one('div', {'id' : 'content_third'}).find_all("p")]
  sanitized_clerk_data = []

  for stripped_data in raw_clerk_data:
    stripped_data = [x.lstrip().rstrip() for x in stripped_data.split('\n')]

    if(len(stripped_data) < 8): # all clerks data blocks follow the same exact format
      continue

    sanitized_data = {
      'locale' : stripped_data[0].capitalize(),
      'city' : stripped_data[0].capitalize(), 
      'address' : " ".join(x.capitalize() for x in " ".join(stripped_data[1:4]).split()), 
      'phones' : [stripped_data[4].split()[1]],
      'faxes' : [stripped_data[5].split()[1]],
      'emails' : [stripped_data[6].split()[1]],
      'url' : stripped_data[7].split()[1]
    }
    sanitized_clerk_data.append(sanitized_data)
    
  return sanitized_clerk_data
    
if __name__ == "__main__":
  with open('mass_clerks.html') as f:
    json_data = parse_html(f)

  with open('../../public/massachusetts.json', 'w') as f:
    json.dump(json_data, f)