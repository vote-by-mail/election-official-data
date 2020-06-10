import os
import pkgutil
import importlib
import unittest
from invoke import task
from common import normalize_state, diff_and_save


@task
def collect(c, state):  # pylint: disable=unused-argument,invalid-name
  states_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'states')
  states_ispkg = {name: ispkg for _, name, ispkg in pkgutil.iter_modules([states_path])}

  if state in states_ispkg:
    states_ispkg = {state: states_ispkg[state]}
  elif state != 'all':
    print(f"State '{state}' not found.")
    print("Available states are:\n\t" + "\n\t".join(states_ispkg.keys()))
    return

  for state_name, ispkg in states_ispkg.items():
    print(f'Process {state_name}')
    state_module = importlib.import_module(f"states.{state_name}{'.main' if ispkg else ''}")
    data = state_module.fetch_data()
    data = normalize_state(data)
    diff_and_save(data, f'{state_name}.json')


@task
def test(c):  # pylint: disable=unused-argument,invalid-name
  suite = unittest.TestLoader().discover('tests')
  unittest.TextTestRunner().run(suite)
