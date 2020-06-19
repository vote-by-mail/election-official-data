import unittest
import glob
import json
import re
from parameterized import parameterized
from common import public_dir


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
      self.assertTrue(regex.search(val))

  def assert_string_list(self, list_, allow_none=True, regex=None):
    if allow_none and list_ is None:
      return

    self.assertIsInstance(list_, list)
    self.assertEqual(len(list_), len(set(list_)))
    for val in list_:
      self.assertIsInstance(val, str)

      if regex:
        self.assertTrue(regex.search(val), f'"{val}" does not match regex "{regex.pattern}"')
      else:
        self.assertTrue(val)

  @parameterized.expand(publics, skip_on_empty=True)
  def test_state(self, public_filename):
    with open(public_filename) as public_file:
      data = json.load(public_file)

    self.assertIsInstance(data, list)
    if 'alaska' in public_filename:
      self.assertEqual(len(data), 1)
    else:
      self.assertGreater(len(data), 10)

    for datum in data:
      self.assert_nonempty_string(datum.get('locale'), allow_none=False)
      self.assert_nonempty_string(datum.get('official'), titled=False)

      self.assert_nonempty_string(datum.get('city'))
      self.assert_nonempty_string(datum.get('county'), regex=re.compile(' County$'))

      self.assert_string_list(
        datum.get('emails'),
        regex=re.compile(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$')
      )
      self.assert_string_list(
        datum.get('faxes'),
        regex=re.compile(r'^\D*1?\D*\d{3}\D*\d{3}\D*\d{4}\D*$')
      )


if __name__ == '__main__':
  unittest.main()
