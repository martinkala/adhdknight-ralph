.PHONY: dev test test-bdd test-all migrate clean install venv

VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
UVICORN  := $(VENV)/bin/uvicorn
ALEMBIC  := $(VENV)/bin/alembic
PYTEST   := $(VENV)/bin/pytest
BEHAVE   := $(VENV)/bin/behave

venv:
	@if [ ! -d $(VENV) ]; then python3 -m venv $(VENV) && echo "Created virtualenv $(VENV)"; fi

install: venv
	@echo "Installing dependencies..."
	$(PIP) install --quiet -r requirements.txt

dev: install
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi
	$(MAKE) migrate
	#$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8095
	$(UVICORN) app.main:app --reload --host 192.168.77.24 --port 8095

migrate: venv
	$(ALEMBIC) upgrade head

test: venv
	$(PYTEST) tests/unit tests/api -v

test-bdd: venv
	@if [ -n "$(FEATURE)" ]; then \
		$(BEHAVE) tests/bdd/features/$(FEATURE).feature --no-capture; \
	else \
		$(BEHAVE) tests/bdd/features/ --no-capture; \
	fi

test-all: venv
	$(PYTEST) tests/unit tests/api -v --cov=app --cov-report=term-missing
	$(MAKE) test-bdd

clean:
	rm -f dev.db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

clean-all: clean
	rm -rf $(VENV)
