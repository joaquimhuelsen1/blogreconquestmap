#!/bin/bash

# Ativar o ambiente virtual Python 3.12.4
source venv312/bin/activate

# Exportar variáveis de ambiente (não mais necessárias para execução direta)
# export FLASK_APP=app
# export FLASK_ENV=production

# Iniciar a aplicação
python app.py

# Para sair do ambiente virtual, você pode usar o comando 'deactivate' 