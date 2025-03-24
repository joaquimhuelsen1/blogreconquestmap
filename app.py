import sys
import os
from app import create_app, db
from flask import render_template, current_app

# Criação da aplicação principal
app = create_app()

if __name__ == '__main__':
    print("Iniciando servidor na porta 8000...")
    app.run(host='0.0.0.0', port=8000, debug=False)
