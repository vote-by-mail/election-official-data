import requests
import time
from ediblepickle import checkpoint

def key_namer(args, kwargs):
  kwargs.pop('wait', None)
  return str(abs(hash(str(args) + str(kwargs)))) + '.pkl'

@checkpoint(key=key_namer, work_dir='cache')
def cache_request(url, method='GET', data={}, wait=None):
  if wait:
    time.sleep(wait)
  if data:
    response = requests.request(method, url, data=data)
  else:
    response = requests.request(method, url)
  return response.text
