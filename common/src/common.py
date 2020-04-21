import requests
import time
from ediblepickle import checkpoint

def key_namer(args, kwargs):
  wait_free = { k: v for k, v in kwargs.items() if k != 'wait' }
  return str(abs(hash(str(args) + str(wait_free)))) + '.pkl'

@checkpoint(key=key_namer, work_dir='cache')
def cache_request(url, method='GET', data={}, wait=None):
  if wait is not None:
    time.sleep(wait)
  if data:
    response = requests.request(method, url, data=data)
  else:
    response = requests.request(method, url)
  return response.text
