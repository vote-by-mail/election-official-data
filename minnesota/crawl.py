import requests

URL = 'https://www.sos.state.mn.us/elections-voting/find-county-election-office/'

if __name__ == '__main__':
  response = requests.get(URL)
  with open('results/page.html', 'w') as fh:
    fh.write(response.text)
