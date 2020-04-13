import json
import glob
import os

def read_noemail():
  with open('results/result.noemail.json') as fh:
    return json.load(fh)

def _read_address(pattern, add_lookup_key):
  data = []
  for file in glob.glob(pattern):
    base = os.path.basename(file)
    key = os.path.splitext(base)[0]
    with open(file) as fh:
      datum = json.load(fh).get('Data') or {}
      clerk_dict = datum.get('clerk') or {}
      if add_lookup_key:
        key_dict = {'lookup_key': key}
        data += [{**clerk_dict, **key_dict}]
      else:
        data += [clerk_dict]
  return data

def read_municipal_address(add_lookup_key=False):
  return _read_address('results/municipal_address/*.json', add_lookup_key)

def read_mailing_address(add_lookup_key=False):
  return _read_address('results/mailing_address/*.json', add_lookup_key)
