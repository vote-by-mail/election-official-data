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
	
lint:
	source venv/bin/activate && inv lint
	
lintwarn:
	source venv/bin/activate && inv lintwarn

test:
	source venv/bin/activate && inv test
