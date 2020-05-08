from glob import glob

from invoke import task

@task
def collect(c, state):
  if state == 'all':
    scripts = glob('states/*/main.py')
  else:
    scripts = [f'states/{state}/main.py']
  for script in scripts:
    c.run(f'. ./venv/bin/activate && python {script}')
