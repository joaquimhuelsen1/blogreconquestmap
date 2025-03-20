# Blog de Reconquista

Um blog especializado em conteúdo sobre relacionamentos e reconquista, com estratégias para melhorar relacionamentos e atrair pessoas.

## Funcionalidades

- Artigos gratuitos e premium sobre relacionamentos
- Sistema de usuários com níveis: normal, premium e administrador
- Interface amigável e responsiva
- Comentários nos artigos
- Chat com IA para aconselhamento (para usuários premium)

## Tecnologias Utilizadas

- Python 3.12
- Flask (Framework web)
- SQLAlchemy (ORM)
- Flask-Login (Autenticação)
- Bootstrap (Frontend)
- SQLite (Banco de dados em desenvolvimento)
- OpenAI API (Recursos de IA)

## Como Instalar

1. Clone o repositório
   ```
   git clone https://github.com/seu-usuario/blog.git
   cd blog
   ```

2. Crie um ambiente virtual e instale as dependências
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente
   ```
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

4. Inicialize o banco de dados
   ```
   python -m flask db upgrade
   ```

5. Execute a aplicação
   ```
   python run.py
   ```

## Contas de Usuário

Para testar a aplicação, foram criadas as seguintes contas:

- Administrador: username: `admin`, senha: `adminsenha`
- Premium: username: `premium`, senha: `premiumsenha`
- Normal: username: `usuario`, senha: `usuariosenha`

## Licença

Este projeto é privado e não possui licença para distribuição. 