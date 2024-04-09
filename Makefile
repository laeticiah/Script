default: test

run:
	python3 -m venv .venv && \
	source .venv/bin/activate && \
	python3 -m pip install --upgrade -r requirements.txt -q && \
	python main.py laeticiah config.yaml output.csv https://api.github.com

test:
	python3 -m venv .venv && \
	source .venv/bin/activate && \
	python3 -m pip install --upgrade -r requirements.txt -q && \
	python -m pytest --verbose

clean:
	rm -rf ".venv" "*.csv" "__pycache__"
