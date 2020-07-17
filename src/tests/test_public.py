import unittest
import glob
import json
import re
from parameterized import parameterized
from common import public_dir, re_email

re_phone_fax_test = re.compile(r'\+1\d{10}(x\d+)?')


def publics():
  return glob.glob(f'{public_dir}/*.json')


class TestPublic(unittest.TestCase):
  def assert_nonempty_string(self, val, allow_none=True, regex=None, stripped=True, titled=True):  # pylint: disable=too-many-arguments
    if allow_none and val is None:
      return
    self.assertIsInstance(val, str)
    self.assertIsNot(val, '')

    if stripped:
      self.assertEqual(val, val.strip())

    if titled:
      self.assertNotEqual(val, val.lower())
      self.assertNotEqual(val, val.upper())

    if regex:
      # fullmatch requires the whole string to match the pattern (i.e. no whitespace)
      self.assertTrue(regex.fullmatch(val))

  def assert_string_list(self, list_, allow_none=True, regex=None):
    if allow_none and list_ is None:
      return

    self.assertIsInstance(list_, list)
    self.assertEqual(len(list_), len(set(list_)))
    for val in list_:
      self.assertIsInstance(val, str)

      if regex:
        # fullmatch requires the whole string to match the pattern (i.e. no whitespace)
        self.assertTrue(regex.fullmatch(val), f'"{val}" does not match regex "{regex.pattern}"')
      else:
        self.assertTrue(val)

  @parameterized.expand(publics, skip_on_empty=True)
  def test_state(self, public_filename):
    with open(public_filename) as public_file:
      data = json.load(public_file)

    self.assertIsInstance(data, list)
    if 'alaska' in public_filename or 'district_of_columbia' in public_filename:
      self.assertEqual(len(data), 1)
    else:
      self.assertGreater(len(data), 10)

    for datum in data:
      self.assert_nonempty_string(datum.get('locale'), allow_none=False)
      self.assert_nonempty_string(datum.get('official'), titled=False)

      self.assert_nonempty_string(datum.get('city'))
      self.assert_nonempty_string(datum.get('county'), regex=re.compile('.* County'))

      self.assert_string_list(datum.get('emails'), regex=re_email)

      self.assert_string_list(datum.get('faxes'), regex=re_phone_fax_test)
      self.assert_string_list(datum.get('phones'), regex=re_phone_fax_test)

      # common address error is to leave title in field
      for field in ('address', 'physicalAddress'):
        addr = datum.get(field)
        if addr:
          self.assertNotIn('Address:', addr)


if __name__ == '__main__':
  unittest.main()
