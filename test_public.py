
import unittest
import glob
import json

from parameterized import parameterized

def publics():
  return glob.glob('public/*.json')

class TestPublic(unittest.TestCase):
  def assert_nonempty_string(self, x, allow_none=True, endswith=None):
    if allow_none and x is None:
      return
    self.assertIsInstance(x, str)
    self.assertIsNot(x, '')

    if endswith:
      self.assertTrue(x.endswith(endswith))

  def assert_string_list(self, l, allow_none=True):
    if allow_none and l is None:
      return

    self.assertIsInstance(l, list)
    self.assertTrue(all(isinstance(x, str) for x in l))


  @parameterized.expand(publics)
  def test_state(self, public_file):
    with open(public_file) as fh:
      data = json.load(fh)

    self.assertIsInstance(data, list)
    self.assertGreater(len(data), 10)

    for d in data:
      self.assert_nonempty_string(d.get('locale'), allow_none=False)
      self.assert_nonempty_string(d.get('official'))

      self.assert_nonempty_string(d.get('city'))
      self.assert_nonempty_string(d.get('county'))

      self.assert_string_list(d.get('emails'))
      self.assert_string_list(d.get('faxes'))

if __name__ == '__main__':
  unittest.main()
