install:
	pip install	--upgrade pip && \
	pip install -r requirements.txt

format: 
	black *.py
lint:
	pylint --disable=R,C,E0602,W polymath.py
test:
	python -m pytest  -vv --cov=test test_polymath.py
