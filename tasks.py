import os
from invoke import task

VENV_ACTIVATE = "venv\\Scripts\\activate" if os.name == 'nt' else ". ./venv/bin/activate"


@task
def collect(c, state):  # pylint: disable=invalid-name
  c.run(f"{VENV_ACTIVATE} && cd src && inv collect {state}")


@task
def lint(c):  # pylint: disable=invalid-name
  c.run(f"{VENV_ACTIVATE} && pylint tasks.py src --rcfile=.pylintrc")


@task
def test(c):  # pylint: disable=invalid-name
  c.run(f"{VENV_ACTIVATE} && cd src && inv test")
