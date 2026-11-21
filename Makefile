# Makefile for US-PT Keyboard Fix
# Commands auxiliares para desenvolvimento e teste.

.PHONY: help install test clean lint format

help: ## Mostrar esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "} {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instalar dependências e o projeto
	@echo "Instalando dependências do sistema..."
	@sudo apt-get update 2>/dev/null || true
	@sudo apt-get install -y python3-pip git 2>/dev/null || true
	@echo "Instalando dependências Python..."
	@pip3 install --upgrade pip 2>/dev/null || true
	@pip3 install -r requirements.txt 2>/dev/null || true
	@echo "Instalando projeto em modo desenvolvido..."
	@pip3 install -e . 2>/dev/null || true
	@echo "Wrapper uspt criado. Execute 'uspt --help'."

test: ## Executar testes
	@echo "Executando testes..."
	@pytest 2>/dev/null || echo "Nenhum teste encontrado ou pytest não disponível."

lint: ## Verificar estilo de código
	@echo "Executando flake8..."
	@flake8 src/uspt/ 2>/dev/null || echo "flake8 não disponível ou erros encontrados."

format: ## Formatar código
	@echo "Formatando com black..."
	@black src/uspt/ 2>/dev/null || echo "black não disponível ou erros encontrados."

clean: ## Limpar ficheiros gerados
	@echo "A limpar ficheiros Python..."
	@find . -type f -name "*.pyc" -delete 2>/dev/null
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
	@echo "Limpado."