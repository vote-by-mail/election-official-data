from glob import glob
import os

from invoke import task

VENV_ACTIVATE = "venv\\Scripts\\activate" if os.name == 'nt' else ". ./venv/bin/activate"


@task
def collect(c, state):
  if state == 'all':
    scripts = glob('states/*/main.py')
  else:
    scripts = [f'states/{state}/main.py']
  for script in scripts:
    print(f'Process {script}')
    c.run(f'{VENV_ACTIVATE} && python {script}')


@task
def lint(c):
  dirs = [d for d in glob('**/') if not d.startswith('venv')]
  pyfiles = glob('*.py')
  for d in dirs:
    pyfiles += glob(f'{d}**/*.py', recursive=True)
  c.run(f"{VENV_ACTIVATE} && pylint {' '.join(pyfiles)} --rcfile=.pylintrc")
