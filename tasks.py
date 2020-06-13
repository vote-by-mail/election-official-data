import os
from invoke import task

VENV_ACTIVATE = "venv\\Scripts\\activate" if os.name == 'nt' else ". ./venv/bin/activate"


@task
def collect(c, state):
  c.run(f"{VENV_ACTIVATE} && cd src && inv collect {state}")


@task
def lint(c):
  c.run(f"{VENV_ACTIVATE} && pylint tasks.py src --rcfile=.pylintrc")


@task
def lintwarn(c):
  '''
  This is temporary and used to identify cases where certain warning flags are showing up
  Remove me when I no longer generate warnings.
  '''
  disable = "--disable=missing-module-docstring,missing-class-docstring,missing-function-docstring"
  c.run(f"{VENV_ACTIVATE} && pylint tasks.py src --rcfile=.pylintrc --exit-zero --enable=all {disable} --reports=y")


@task
def test(c):
  c.run(f"{VENV_ACTIVATE} && cd src && inv test")
