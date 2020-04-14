import requests
from ediblepickle import checkpoint

def key_namer(args, kwargs):
  url = args[0]
  return str(abs(hash(url))) + '.pkl'

@checkpoint(key=key_namer, work_dir='cache')
def cache_request(url):
  response = requests.get(url)
  return response.text
