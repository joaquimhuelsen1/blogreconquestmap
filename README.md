# Blog com Supabase

Uma aplicação de blog simples utilizando Flask e Supabase como banco de dados.

## Requisitos

- Python 3.9+
- [Supabase](https://supabase.com/) (conta gratuita)
- [Flask](https://flask.palletsprojects.com/)

## Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 2. Configure o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure o Supabase

1. Crie uma conta no [Supabase](https://supabase.com/)
2. Crie um novo projeto
3. Copie as credenciais da aba "Settings" > "API"
4. Crie um arquivo `.env` a partir do `.env.example`:

```bash
cp .env.example .env
```

5. Edite o arquivo `.env` com suas credenciais do Supabase:

```
SUPABASE_URL=https://seu-id-de-projeto.supabase.co
SUPABASE_KEY=sua-chave-publica-supabase
SUPABASE_SERVICE_KEY=sua-chave-service-key-supabase
```

### 4. Configure o banco de dados

Execute o script de configuração do Supabase para criar as tabelas e dados iniciais:

```bash
python supabase_setup.py
```

### 5. Execute a aplicação

```bash
flask run
```

A aplicação estará disponível em `http://127.0.0.1:5000/`.

## Estrutura do Projeto

```
├── app/                  # Código principal da aplicação
│   ├── models/           # Modelos de dados
│   ├── routes/           # Rotas da aplicação
│   ├── static/           # Arquivos estáticos (CSS, JS, imagens)
│   ├── templates/        # Templates HTML
│   └── __init__.py       # Inicialização da aplicação
├── migrations/           # Migrações do banco de dados
├── .env.example          # Exemplo de variáveis de ambiente
├── .gitignore            # Arquivos ignorados pelo Git
├── app.py                # Ponto de entrada da aplicação
├── config.py             # Configurações da aplicação
├── requirements.txt      # Dependências do projeto
├── supabase_models.py    # Modelos adaptados para Supabase
└── supabase_setup.py     # Script de configuração do Supabase
```

## Usuários padrão

- Administrador:
  - Usuário: `admin`
  - Senha: `admin123`

- Usuário comum:
  - Usuário: `usuario`
  - Senha: `usuario123`

- Usuário premium:
  - Usuário: `premium`
  - Senha: `premium123`

## Funcionalidades

- Sistema de autenticação (login/cadastro)
- Publicação de posts (texto e imagens)
- Comentários em posts
- Conteúdo premium para assinantes
- Painel de administração

## Tecnologias utilizadas

- [Flask](https://flask.palletsprojects.com/): Framework web
- [Supabase](https://supabase.com/): Banco de dados e autenticação
- [Flask-Login](https://flask-login.readthedocs.io/): Gerenciamento de sessões
- [Bootstrap](https://getbootstrap.com/): Framework CSS para interface 