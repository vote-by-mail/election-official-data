from setuptools import setup, find_packages

setup(
  name='common',
  package_dir={'': 'src'},
  packages=find_packages(where='src'),
  install_requires=['ediblepickle', 'requests'],
)
