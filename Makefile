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

run:
	$(PY) src/main.py

freeze:
	$(PIP) freeze > requirements.txt

clean:
	rm -rf $(VENV)

format:
	$(PIP) install black
	$(VENV)/bin/black src/