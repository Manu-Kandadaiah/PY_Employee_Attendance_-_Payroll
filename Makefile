.PHONY: install run test init seed verify
install:
	python -m pip install -r requirements.txt
run:
	python run.py
test:
	python -m pytest -v
init:
	python -m flask --app run.py init-db
seed:
	python -m flask --app run.py seed-demo
verify:
	python scripts/verify_demo.py
