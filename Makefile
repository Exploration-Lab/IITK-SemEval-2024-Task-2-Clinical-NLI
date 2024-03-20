.PHONY: create_environment requirements

### GLOBALS ###

PROJECT_NAME = Gemini
PYTHON_INTERPRETER = python3

## Create Python Environment
create_environment:
	conda create --name $(PROJECT_NAME) python=3.10
	@echo ">>> New conda environment created."
	conda activate $(PROJECT_NAME)
	@echo ">>> New conda environment activated. Ready to install packages."

## Install Python Dependencies
requirements:
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt