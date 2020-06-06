import unittest
import glob
import json
import re

from parameterized import parameterized


def publics():
  return glob.glob('public/*.json')


class TestPublic(unittest.TestCase):
  def assert_nonempty_string(self, x, allow_none=True, regex=None, stripped=True, titled=True):
    if allow_none and x is None:
      return
    self.assertIsInstance(x, str)
    self.assertIsNot(x, '')

    if stripped:
      self.assertEqual(x, x.strip())

    if titled:
      self.assertNotEqual(x, x.lower())
      self.assertNotEqual(x, x.upper())

    if regex:
      self.assertTrue(regex.search(x))

  def assert_string_list(self, list_, allow_none=True, regex=None):
    if allow_none and list_ is None:
      return

    self.assertIsInstance(list_, list)
    self.assertEqual(len(list_), len(set(list_)))
    for x in list_:
      self.assertIsInstance(x, str)

      if regex:
        self.assertTrue(regex.search(x), f'"{x}" does not match regex "{regex.pattern}"')
      else:
        self.assertTrue(x)

  @parameterized.expand(publics)
  def test_state(self, public_file):
    with open(public_file) as fh:
      data = json.load(fh)

    self.assertIsInstance(data, list)
    self.assertGreater(len(data), 10)

    for d in data:
      self.assert_nonempty_string(d.get('locale'), allow_none=False)
      self.assert_nonempty_string(d.get('official'), titled=False)

      self.assert_nonempty_string(d.get('city'))
      self.assert_nonempty_string(d.get('county'), regex=re.compile(' County$'))

      self.assert_string_list(
        d.get('emails'),
        regex=re.compile(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$')
      )
      self.assert_string_list(
        d.get('faxes'),
        regex=re.compile(r'^\D*1?\D*\d{3}\D*\d{3}\D*\d{4}\D*$')
      )


if __name__ == '__main__':
  unittest.main()
