SHELL := /bin/bash

# set variables
export NAME = elections-officials

create-install:
	python3 -m venv venv
	source venv/bin/activate \
		&& pip3 install -r requirements.txt \
		&& ipython kernel install --user --name=$$NAME

install:
	source venv/bin/activate && pip3 install -r requirements.txt

ipython:
	source venv/bin/activate && ipython --pdb

jupyter:
	source venv/bin/activate && jupyter notebook

test:
	source venv/bin/activate && python test_public.py
	
lint:
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# the GitHub editor is 127 chars wide
	flake8 . --count --ignore=E111,E114,E121,E128 --max-line-length=127 --statistics
	# exit-zero treats all errors as warnings
	flake8 . --exit-zero --count --select=E121,E128 --max-complexity=10 --statistics
