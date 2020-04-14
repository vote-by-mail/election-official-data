import json
import glob

files = glob.glob('florida/cache/*.json')
data = []
print(f'Found {len(files)} files')
for file in files:
  with open(file) as fh:
    datum = json.load(fh)
    county = datum['title'].split('Supervisor')[0].strip()
    data += [{
      'locale': county,
      'official': datum['name'].replace(u'\xa0', ' ').split(',')[0].strip(),
      'emails': [datum['email'].split(':')[1].strip()],  # ignore leading 'mailto:'
      'url': datum['url'],
    }]

with open('public/florida.json', 'w') as fh:
  json.dump(data, fh)
