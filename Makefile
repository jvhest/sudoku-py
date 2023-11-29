.PHONY: first-commit
first-commit: ## install requirement and commit
	@echo "🚀 installing dependencies..."
	@pip install pip-tools
	@pip-compile -o requirements.txt pyproject.toml requirements/dev-requirements.in
	@pip-sync
	@echo "🚀 editable install of project..."
	@python -m pip install -e .
	@echo "🚀 creating git repository..."
	@git init -b main
	@pre-commit install
	@echo "🚀 do first commit..."
	@git add .
	@git commit -m "first-commit"

.PHONY: editable-install
editable-install: ## Install package editable
	@python -m pip install -e .

.PHONY: update-requirements
update-requirements: ## Run code quality tools
	@pip-compile -o requirements.txt pyproject.toml requirements/dev-requirements.in
	@pip-sync
	@python -m pip install -e .

.PHONY: check
check: ## Run code quality tools
	@echo "Run code quality tools:"
	@echo "🚀 Linting code: running flake8 ..."
	@flake8
	@echo "🚀 Static type checking: running mypy ..."
	@mypy src/

.PHONY: test
test: ## Run pytest
	@echo "🚀 Testing code: Running pytest"
	@pytest --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: build
build: clean-build  ## Build wheel file
	@echo "🚀 Creating wheel file"
	@build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@echo "🚀 clean-up build artifacts"
	@rm -rf dist

.PHONY: help
help:  ## this help menu
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
