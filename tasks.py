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
def lint(c, warn=None):
  dirs = [d for d in glob('**/') if not d.startswith('venv')]
  pyfiles = glob('*.py')
  extra_opt = '--enable=R,C --disable=C0103,C0114,C0115,C0116 --exit-zero --reports=y' if warn else ''
  for d in dirs:
    pyfiles += glob(f'{d}**/*.py', recursive=True)
  if glob('venv/'):
    c.run(f"{VENV_ACTIVATE} && pylint {' '.join(pyfiles)} --rcfile=.pylintrc {extra_opt}")
  else:
    c.run(f"pylint {' '.join(pyfiles)} --rcfile=.pylintrc {extra_opt}")
