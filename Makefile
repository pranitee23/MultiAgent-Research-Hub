.PHONY: help install run api test verify clean

help: ## Show commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Start Chainlit UI
	chainlit run app.py

api: ## Start FastAPI backend
	uvicorn src.api.main:app --reload --port 8000

test: ## Run all tests
	pytest tests/ -v

verify: ## Run setup checks
	python verify_setup.py

evaluate: ## Run evaluation benchmark
	python -m src.evaluation.run_eval

docker: ## Start full stack
	docker-compose up --build -d

clean: ## Remove caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; rm -rf .pytest_cache .ruff_cache