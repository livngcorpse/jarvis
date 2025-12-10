# Makefile for Jarvis Telegram Bot

# Default target
.PHONY: help install test lint clean

help:
	@echo "Jarvis Telegram Bot Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install     Install dependencies"
	@echo "  test        Run tests"
	@echo "  lint        Run code linting"
	@echo "  clean       Clean temporary files"

install:
	pip install -r requirements.txt

test:
	pytest -q

lint:
	ruff check .
	black --check .

clean:
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf .pytest_cache
	find . -type f -name "*.pyc" -delete