import os
import sys

# Adiciona o diretório atual ao path do Python
INTERP = os.path.join(os.environ['HOME'], 'blog', '.venv', 'bin', 'python3.12')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

# Importa a aplicação Flask
from app import create_app

# Cria a instância da aplicação
application = create_app()

# Alias 'application' como 'app' para compatibilidade com diferentes servidores WSGI
app = application 