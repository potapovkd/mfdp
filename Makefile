.PHONY: help test test-cov lint format type-check security clean install dev-install

help: ## Показать доступные команды
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости для production
	pip install -r requirements.txt

dev-install: ## Установить зависимости для разработки
	pip install -r requirements.txt
	pip install -r requirements.dev.txt

test: ## Запустить все тесты
	pytest src/tests/ -v

test-cov: ## Запустить тесты с покрытием
	pytest src/tests/ --cov=src/ --cov-report=html --cov-report=term

test-fast: ## Запустить тесты параллельно
	pytest src/tests/ -n auto

format: ## Форматировать код
	black src/
	isort src/

lint: ## Проверить код линтером
	flake8 src/

type-check: ## Проверить типы
	mypy src/ --ignore-missing-imports

security: ## Проверить безопасность
	bandit -r src/
	safety check

quality: format lint type-check security ## Проверить качество кода (все проверки)

docker-build: ## Собрать Docker образы
	docker compose build

docker-test: ## Запустить тесты в Docker
	docker compose run --rm api pytest src/tests/ -v

docker-up: ## Запустить все сервисы
	docker compose up -d

docker-down: ## Остановить все сервисы
	docker compose down

docker-logs: ## Показать логи ML worker
	docker compose logs ml-worker

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "htmlcov" -exec rm -rf {} +
	find . -name ".pytest_cache" -exec rm -rf {} +
	find . -name ".mypy_cache" -exec rm -rf {} +

ci-test: ## Запустить тесты как в CI
	@echo "🧪 Запуск тестов как в CI..."
	pytest src/tests/ -v --tb=short

ci-quality: ## Проверить качество кода как в CI
	@echo "🔍 Проверка качества кода..."
	black --check --diff src/
	isort --check-only --diff src/
	flake8 src/
	mypy src/ --ignore-missing-imports
	bandit -r src/ 