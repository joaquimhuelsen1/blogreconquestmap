# Plano de Limpeza e Organização do Projeto

## Problemas Identificados
1. **Muitos arquivos redundantes** - Existem vários scripts com propósitos similares
2. **Múltiplos arquivos .env** - Confusão entre ambientes (.env, .env.local, .env.production, etc.)
3. **Arquivos zip de backup** - Ocupando muito espaço
4. **Scripts de diagnóstico misturados com código principal**
5. **Configuração para MySQL quando SQLite seria suficiente para desenvolvimento**
6. **Confusão entre configuração para Supabase e banco de dados relacional**

## Plano de Reorganização

### 1. Estrutura de Diretórios
```
blog/
  ├── app/                      # Código principal da aplicação
  │    ├── __init__.py          # Inicialização da aplicação
  │    ├── models.py            # Modelos de dados
  │    ├── forms.py             # Formulários WTForms
  │    ├── routes/              # Rotas da aplicação organizadas por módulo
  │    ├── static/              # Arquivos estáticos (CSS, JS, imagens)
  │    └── templates/           # Templates HTML
  │
  ├── config.py                 # Configuração centralizada da aplicação
  ├── requirements.txt          # Dependências do projeto
  ├── run.py                    # Script para executar a aplicação localmente
  ├── passenger_wsgi.py         # Ponto de entrada para hospedagem cPanel
  │
  ├── migrations/               # Migrações de banco de dados
  │
  ├── scripts/                  # Scripts utilitários
  │    ├── init_db.py           # Inicializa o banco de dados
  │    ├── diagnostic.py        # Diagnóstico de problemas
  │    ├── test_supabase.py     # Testa a conexão com o Supabase
  │    └── test_db.py           # Testa a conexão com o banco de dados
  │
  ├── docs/                     # Documentação
  │    ├── SETUP.md             # Instruções de configuração
  │    ├── CPANEL.md            # Instruções para deploy no cPanel
  │    ├── SUPABASE.md          # Instruções para Supabase
  │    └── MYSQL.md             # Instruções para MySQL
  │
  ├── .env.example              # Exemplo de arquivo .env
  ├── .env                      # Ignorado pelo Git, configurações locais
  └── .gitignore                # Arquivos a serem ignorados pelo Git
```

### 2. Arquivos que Devem Ser Mantidos
- **Código Principal**:
  - app/ (diretório completo)
  - config.py
  - run.py
  - passenger_wsgi.py
  - requirements.txt

- **Scripts Essenciais**:
  - init_db.py (renomeado para scripts/init_db.py)
  - diagnostic.py (renomeado para scripts/diagnostic.py)
  - test_supabase_connection.py (renomeado para scripts/test_supabase.py)
  - load_env_variables.py (incluído em scripts/utils.py)

- **Documentação**:
  - README.md
  - CPANEL_README.md (renomeado para docs/CPANEL.md)
  - MIGRATION_GUIDE.md (renomeado para docs/MIGRATION.md)

### 3. Arquivos que Podem Ser Removidos
- Arquivos ZIP:
  - blog_hospedainfo.zip
  - blog_hospedainfo_update.zip
  - blog_hospedainfo_update2.zip
  - blog_hospedainfo_update3.zip
  - blog_supabase.zip

- Scripts redundantes:
  - check_db.py (funcionalidade incluída em diagnostic.py)
  - check_db_structure.py (funcionalidade incluída em diagnostic.py)
  - check_post.py (funcionalidade incluída em diagnostic.py)
  - check_posts.py (funcionalidade incluída em diagnostic.py)
  - debug.py (funcionalidade incluída em diagnostic.py)
  - debug_app.py (funcionalidade incluída em diagnostic.py)
  - dev_run.py (usar run.py é suficiente)
  - run_py312.sh (desnecessário com instruções claras)

- Arquivos de ambiente duplicados:
  - .env.local (manter apenas .env.example)
  - .env.production (manter apenas .env.example com seção para produção)
  - .env.original (desnecessário)

### 4. Otimização do Arquivo .env.example
```
# Configurações do Aplicativo
FLASK_APP=app.py
FLASK_ENV=development  # Mudar para 'production' em produção
FLASK_DEBUG=True       # Mudar para 'False' em produção
SECRET_KEY=chave-secreta-exemplo-mudar-em-producao

# Banco de Dados - Escolha UM dos formatos abaixo:
# SQLite (desenvolvimento local)
DATABASE_URL=sqlite:///database.db

# MySQL (produção/cPanel)
# DATABASE_URL=mysql+pymysql://usuario:senha@localhost/nome_do_banco

# Supabase (opcional)
# SUPABASE_URL=https://seu-projeto.supabase.co
# SUPABASE_KEY=sua-chave-publica
# SUPABASE_SERVICE_KEY=sua-chave-servico

# Configurações da API OpenAI (opcional)
# OPENAI_API_KEY=sua-chave-api
# OPENAI_ASSISTANT_ID=seu-id-assistente
```

### 5. Simplificação do passenger_wsgi.py
```python
import os
import sys

# Adiciona o diretório atual ao path do Python
INTERP = os.path.join(os.environ['HOME'], '.venv', 'bin', 'python3.12')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

# Carrega variáveis de ambiente se existirem
try:
    from scripts.utils import load_env
    load_env()
except Exception as e:
    print(f"Aviso: {str(e)}")

# Importa a aplicação Flask
from app import create_app

# Cria a instância da aplicação
application = create_app()

# Alias para compatibilidade WSGI
app = application
```

## Passos para Implementação

1. **Criar Diretórios**:
   - Criar `scripts/`, `docs/` se não existirem

2. **Mover Arquivos**:
   - Mover scripts para `scripts/`
   - Mover documentação para `docs/`

3. **Limpar Arquivos**:
   - Remover arquivos ZIP
   - Remover scripts redundantes
   - Manter apenas um arquivo `.env.example`

4. **Unificar Configurações**:
   - Simplificar `config.py`
   - Criar um único exemplo de `.env`

5. **Testar a Aplicação**:
   - Confirmar que a aplicação ainda funciona após a reorganização
   - Verificar SQLite como banco padrão para desenvolvimento

## Benefícios

1. **Estrutura Mais Clara** - Fácil de entender onde encontrar arquivos
2. **Redução de Tamanho** - Eliminação de arquivos zip grandes e redundantes
3. **Configuração Simplificada** - Um único arquivo de exemplo para configuração
4. **Manutenção Mais Fácil** - Scripts organizados logicamente
5. **Deploy Simplificado** - Instruções claras para subir em produção 