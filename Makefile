PYTHON=python3
VENV=venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

activate:
	$(PYTHON) -m venv $(VENV)
	source $(VENV)/bin/activate
install:

	$(PIP) install --upgrade pip 
	$(PIP) install -r requirements.txt
test:
	$(PY) -m pytest tests/*

run:
	$(PY) src/main.py

freeze:
	$(PIP) freeze > requirements.txt

clean:
	rm -rf $(VENV)

format:
	$(PIP) install black
	$(VENV)/bin/black *.py

lint:
	$(PIP) install pylint
	$(VENV)/bin/pylint *.py
