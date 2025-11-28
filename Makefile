SHELL := /bin/bash

.PHONY: setup-env install fetch-data plot list-contracts validate clean

setup-env:
	@bash tools/scripts/create_venv.sh
	@echo ""
	@echo "Run: source .venv/bin/activate"

install:
	@echo "Installing dependencies..."
	@.venv/bin/uv pip install -e .
	@echo "Dependencies installed!"

fetch-data:
	@echo "Fetching all COT data..."
	@cd src && ../.venv/bin/python main.py

plot:
	@echo "Starting interactive plotter..."
	@cd src && ../.venv/bin/python example_plot.py

list-contracts:
	@echo "Listing all available contracts..."
	@cd src && ../.venv/bin/python list_contracts.py

validate:
	@cd src && ../.venv/bin/python validate_data.py $(CONTRACT) $(DATE)

clean:
	@echo "Cleaning data directory..."
	@rm -rf data/
	@echo "Data directory cleaned"
