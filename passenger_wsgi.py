import os
import sys

# Adiciona o diretório atual ao path do Python
INTERP = os.path.join(os.environ['HOME'], 'blog', '.venv', 'bin', 'python3.12')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

# Carrega variáveis de ambiente antes de importar a aplicação
try:
    from load_env_variables import load_env
    # Tenta carregar do .env e depois do .env.production se existir
    load_env('.env')
    load_env('.env.production')
    print("Variáveis de ambiente carregadas com sucesso")
except Exception as e:
    print(f"Erro ao carregar variáveis de ambiente: {str(e)}")
    # Continua mesmo se falhar, pois as variáveis podem estar configuradas no cPanel

# Verifica as variáveis do Supabase
for var in ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY']:
    if os.environ.get(var):
        print(f"{var} está configurado")
    else:
        print(f"AVISO: {var} não está configurado!")

# Importa a aplicação Flask
from app import create_app

# Cria a instância da aplicação
application = create_app()

# Alias 'application' como 'app' para compatibilidade com diferentes servidores WSGI
app = application 