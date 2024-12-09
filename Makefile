# Variáveis
PYTHON = uv
APP_NAME = crypto-trading-bot
VENV_DIR = .venv

# Regras
.PHONY: help venv install sync add remove list run test clean

help:  ## Mostra esta ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv:  ## Cria ou ativa o ambiente virtual
	$(PYTHON) venv

install:  ## Instala as dependências listadas no projeto
	$(PYTHON) sync

add:  ## Adiciona uma nova biblioteca ao projeto (Ex.: make add PKG=requests)
	$(PYTHON) add $(PKG)

remove:  ## Remove uma biblioteca do projeto (Ex.: make remove PKG=requests)
	$(PYTHON) remove $(PKG)

list:  ## Lista as dependências instaladas
	$(PYTHON) list

run:  ## Executa a aplicação (modifique conforme necessário)
	uvicorn main:app --reload

test:  ## Executa os testes (usando pytest)
	$(PYTHON) run pytest

clean:  ## Remove o ambiente virtual e arquivos temporários
	rm -rf $(VENV_DIR) .pytest_cache __pycache__ *.pyc *.pyo

