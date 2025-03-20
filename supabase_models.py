"""
Modelos para interagir com o Supabase.
Este arquivo substitui o SQLAlchemy com funções de acesso direto ao Supabase.
"""
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json

# Configuração do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # Chave anônima (pública)
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")  # Chave de serviço (privada)

class SupabaseClient:
    """Cliente para interagir com o Supabase."""
    
    def __init__(self, url=None, key=None, service_key=None):
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY
        self.service_key = service_key or SUPABASE_SERVICE_KEY
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem ser definidos")
    
    def _get_headers(self, use_service_key=False):
        """Retorna os cabeçalhos para as requisições."""
        key = self.service_key if use_service_key else self.key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def from_table(self, table_name):
        """Retorna um objeto para interagir com uma tabela específica."""
        return SupabaseTable(self, table_name)
    
    def auth(self):
        """Retorna um objeto para interagir com a API de autenticação."""
        return SupabaseAuth(self)

class SupabaseTable:
    """Classe para interagir com uma tabela específica no Supabase."""
    
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.base_url = f"{client.url}/rest/v1/{table_name}"
        self.filters = []
    
    def select(self, columns="*"):
        """Seleciona colunas específicas da tabela."""
        result = self.copy()
        result._select = columns
        return result
    
    def filter(self, column, operator, value):
        """Adiciona um filtro à consulta."""
        result = self.copy()
        result.filters.append((column, operator, value))
        return result
    
    def eq(self, column, value):
        """Filtro de igualdade."""
        return self.filter(column, "eq", value)
    
    def order(self, column, ascending=True):
        """Ordena os resultados."""
        result = self.copy()
        direction = "asc" if ascending else "desc"
        result._order = f"{column}.{direction}"
        return result
    
    def limit(self, count):
        """Limita o número de resultados."""
        result = self.copy()
        result._limit = count
        return result
    
    def offset(self, count):
        """Define um deslocamento para os resultados."""
        result = self.copy()
        result._offset = count
        return result
    
    def copy(self):
        """Cria uma cópia da instância atual."""
        result = SupabaseTable(self.client, self.table_name)
        result.filters = self.filters.copy()
        if hasattr(self, '_select'):
            result._select = self._select
        if hasattr(self, '_order'):
            result._order = self._order
        if hasattr(self, '_limit'):
            result._limit = self._limit
        if hasattr(self, '_offset'):
            result._offset = self._offset
        return result
    
    def _build_query_params(self):
        """Constrói os parâmetros de consulta a partir dos filtros."""
        params = {}
        
        # Adicionar seleção de colunas
        if hasattr(self, '_select'):
            params["select"] = self._select
        
        # Adicionar filtros
        for column, operator, value in self.filters:
            params[f"{column}"] = f"{operator}.{value}"
        
        # Adicionar ordenação
        if hasattr(self, '_order'):
            params["order"] = self._order
        
        # Adicionar limite
        if hasattr(self, '_limit'):
            params["limit"] = self._limit
        
        # Adicionar deslocamento
        if hasattr(self, '_offset'):
            params["offset"] = self._offset
        
        return params
    
    def execute(self, use_service_key=False):
        """Executa a consulta e retorna os resultados."""
        headers = self.client._get_headers(use_service_key)
        params = self._build_query_params()
        
        # Construir a URL com os parâmetros
        url = self.base_url
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{query_string}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao executar consulta: {response.status_code} - {response.text}")
    
    def get(self, id, use_service_key=False):
        """Obtém um registro específico pelo ID."""
        headers = self.client._get_headers(use_service_key)
        url = f"{self.base_url}?id=eq.{id}"
        
        if hasattr(self, '_select'):
            url = f"{url}&select={self._select}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            if response.json():
                return response.json()[0]
            return None
        else:
            raise Exception(f"Erro ao obter registro: {response.status_code} - {response.text}")
    
    def insert(self, data, use_service_key=False):
        """Insere um novo registro na tabela."""
        headers = self.client._get_headers(use_service_key)
        response = requests.post(self.base_url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Erro ao inserir registro: {response.status_code} - {response.text}")
    
    def update(self, id, data, use_service_key=False):
        """Atualiza um registro existente."""
        headers = self.client._get_headers(use_service_key)
        url = f"{self.base_url}?id=eq.{id}"
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao atualizar registro: {response.status_code} - {response.text}")
    
    def delete(self, id, use_service_key=False):
        """Exclui um registro específico."""
        headers = self.client._get_headers(use_service_key)
        url = f"{self.base_url}?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        
        if response.status_code in [200, 204]:
            return True
        else:
            raise Exception(f"Erro ao excluir registro: {response.status_code} - {response.text}")

class SupabaseAuth:
    """Classe para interagir com a API de autenticação do Supabase."""
    
    def __init__(self, client):
        self.client = client
        self.auth_url = f"{client.url}/auth/v1"
    
    def sign_up(self, email, password, data=None):
        """Registra um novo usuário."""
        headers = self.client._get_headers()
        url = f"{self.auth_url}/signup"
        
        payload = {
            "email": email,
            "password": password,
            "data": data or {}
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Erro ao registrar usuário: {response.status_code} - {response.text}")
    
    def sign_in(self, email, password):
        """Autentica um usuário existente."""
        headers = self.client._get_headers()
        url = f"{self.auth_url}/token?grant_type=password"
        
        payload = {
            "email": email,
            "password": password
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao autenticar usuário: {response.status_code} - {response.text}")
    
    def sign_out(self, jwt):
        """Encerra a sessão de um usuário."""
        headers = self.client._get_headers()
        headers["Authorization"] = f"Bearer {jwt}"
        url = f"{self.auth_url}/logout"
        
        response = requests.post(url, headers=headers)
        
        if response.status_code in [200, 204]:
            return True
        else:
            raise Exception(f"Erro ao encerrar sessão: {response.status_code} - {response.text}")

# Inicializar o cliente Supabase
try:
    supabase = SupabaseClient()
except ValueError as e:
    print(f"Erro ao inicializar cliente Supabase: {str(e)}")
    supabase = None

class User:
    """Modelo de usuário para interagir com a tabela 'users' no Supabase."""
    
    def __init__(self, id=None, username=None, email=None, password_hash=None, age=None, 
                 is_admin=False, is_premium=False, ai_credits=1, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.age = age
        self.is_admin = is_admin
        self.is_premium = is_premium
        self.ai_credits = ai_credits
        self.created_at = created_at or datetime.utcnow()
        self._authenticated = False
    
    @classmethod
    def get_by_id(cls, user_id):
        """Obtém um usuário pelo ID."""
        if not supabase:
            return None
        
        try:
            result = supabase.from_table("users").get(user_id)
            if result:
                return cls._from_dict(result)
            return None
        except Exception as e:
            print(f"Erro ao obter usuário por ID: {str(e)}")
            return None
    
    @classmethod
    def get_by_username(cls, username):
        """Obtém um usuário pelo nome de usuário."""
        if not supabase:
            return None
        
        try:
            results = supabase.from_table("users").eq("username", username).execute()
            if results and len(results) > 0:
                return cls._from_dict(results[0])
            return None
        except Exception as e:
            print(f"Erro ao obter usuário por nome de usuário: {str(e)}")
            return None
    
    @classmethod
    def get_by_email(cls, email):
        """Obtém um usuário pelo email."""
        if not supabase:
            return None
        
        try:
            results = supabase.from_table("users").eq("email", email).execute()
            if results and len(results) > 0:
                return cls._from_dict(results[0])
            return None
        except Exception as e:
            print(f"Erro ao obter usuário por email: {str(e)}")
            return None
    
    @classmethod
    def _from_dict(cls, data):
        """Cria uma instância de User a partir de um dicionário."""
        return cls(
            id=data.get("id"),
            username=data.get("username"),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            age=data.get("age"),
            is_admin=data.get("is_admin", False),
            is_premium=data.get("is_premium", False),
            ai_credits=data.get("ai_credits", 1),
            created_at=data.get("created_at")
        )
    
    def to_dict(self):
        """Converte a instância para um dicionário."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "age": self.age,
            "is_admin": self.is_admin,
            "is_premium": self.is_premium,
            "ai_credits": self.ai_credits,
            "created_at": self.created_at
        }
    
    def save(self):
        """Salva o usuário no banco de dados."""
        if not supabase:
            return False
        
        data = self.to_dict()
        
        if "id" in data and data["id"]:
            # Atualizar usuário existente
            try:
                result = supabase.from_table("users").update(self.id, {
                    k: v for k, v in data.items() if k != "id" and k != "created_at"
                }, use_service_key=True)
                return bool(result)
            except Exception as e:
                print(f"Erro ao atualizar usuário: {str(e)}")
                return False
        else:
            # Inserir novo usuário
            try:
                result = supabase.from_table("users").insert({
                    k: v for k, v in data.items() if k != "id"
                }, use_service_key=True)
                
                if result and len(result) > 0:
                    self.id = result[0].get("id")
                    return True
                return False
            except Exception as e:
                print(f"Erro ao inserir usuário: {str(e)}")
                return False
    
    def delete(self):
        """Exclui o usuário do banco de dados."""
        if not supabase or not self.id:
            return False
        
        try:
            return supabase.from_table("users").delete(self.id, use_service_key=True)
        except Exception as e:
            print(f"Erro ao excluir usuário: {str(e)}")
            return False
    
    def set_password(self, password):
        """Define a senha do usuário."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta."""
        return check_password_hash(self.password_hash, password)
    
    def update_ai_credits(self):
        """Atualiza os créditos da IA baseado no status premium do usuário."""
        if self.ai_credits is None or self.ai_credits == 0:
            credits_antes = self.ai_credits
            if self.is_premium:
                self.ai_credits = 5  # 5 créditos para usuários premium
            else:
                self.ai_credits = 1  # 1 crédito para usuários padrão
            
            # Salvar as alterações
            return self.save()
        return False
    
    def use_ai_credit(self):
        """Usa um crédito de IA e retorna True se o crédito foi consumido com sucesso."""
        if self.ai_credits > 0:
            self.ai_credits -= 1
            if self.save():
                return True
        return False
    
    # Métodos requeridos pelo Flask-Login
    def is_authenticated(self):
        """Verifica se o usuário está autenticado."""
        return self._authenticated
    
    def is_active(self):
        """Verifica se o usuário está ativo."""
        return True
    
    def is_anonymous(self):
        """Verifica se o usuário é anônimo."""
        return False
    
    def get_id(self):
        """Retorna o ID do usuário."""
        return str(self.id)

class Post:
    """Modelo de post para interagir com a tabela 'posts' no Supabase."""
    
    def __init__(self, id=None, title=None, content=None, summary=None, image_url=None,
                 premium_only=False, created_at=None, updated_at=None, user_id=None):
        self.id = id
        self.title = title
        self.content = content
        self.summary = summary
        self.image_url = image_url or "https://via.placeholder.com/1200x400"
        self.premium_only = premium_only
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.user_id = user_id
        self._author = None
    
    @classmethod
    def get_by_id(cls, post_id):
        """Obtém um post pelo ID."""
        if not supabase:
            return None
        
        try:
            result = supabase.from_table("posts").get(post_id)
            if result:
                return cls._from_dict(result)
            return None
        except Exception as e:
            print(f"Erro ao obter post por ID: {str(e)}")
            return None
    
    @classmethod
    def get_all(cls, premium_user=False, limit=None, offset=None):
        """Obtém todos os posts, com filtro para conteúdo premium."""
        if not supabase:
            return []
        
        try:
            query = supabase.from_table("posts")
            
            if not premium_user:
                query = query.eq("premium_only", False)
            
            query = query.order("created_at", ascending=False)
            
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
            
            results = query.execute()
            return [cls._from_dict(item) for item in results]
        except Exception as e:
            print(f"Erro ao obter todos os posts: {str(e)}")
            return []
    
    @classmethod
    def get_by_user_id(cls, user_id, limit=None, offset=None):
        """Obtém posts de um usuário específico."""
        if not supabase:
            return []
        
        try:
            query = supabase.from_table("posts").eq("user_id", user_id).order("created_at", ascending=False)
            
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
            
            results = query.execute()
            return [cls._from_dict(item) for item in results]
        except Exception as e:
            print(f"Erro ao obter posts do usuário: {str(e)}")
            return []
    
    @classmethod
    def _from_dict(cls, data):
        """Cria uma instância de Post a partir de um dicionário."""
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            content=data.get("content"),
            summary=data.get("summary"),
            image_url=data.get("image_url"),
            premium_only=data.get("premium_only", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            user_id=data.get("user_id")
        )
    
    def to_dict(self):
        """Converte a instância para um dicionário."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "image_url": self.image_url,
            "premium_only": self.premium_only,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_id": self.user_id
        }
    
    def save(self):
        """Salva o post no banco de dados."""
        if not supabase:
            return False
        
        data = self.to_dict()
        
        if "id" in data and data["id"]:
            # Atualizar post existente
            try:
                result = supabase.from_table("posts").update(self.id, {
                    k: v for k, v in data.items() if k != "id" and k != "created_at"
                }, use_service_key=True)
                return bool(result)
            except Exception as e:
                print(f"Erro ao atualizar post: {str(e)}")
                return False
        else:
            # Inserir novo post
            try:
                result = supabase.from_table("posts").insert({
                    k: v for k, v in data.items() if k != "id" and k != "updated_at"
                }, use_service_key=True)
                
                if result and len(result) > 0:
                    self.id = result[0].get("id")
                    return True
                return False
            except Exception as e:
                print(f"Erro ao inserir post: {str(e)}")
                return False
    
    def delete(self):
        """Exclui o post do banco de dados."""
        if not supabase or not self.id:
            return False
        
        try:
            return supabase.from_table("posts").delete(self.id, use_service_key=True)
        except Exception as e:
            print(f"Erro ao excluir post: {str(e)}")
            return False
    
    @property
    def author(self):
        """Obtém o autor do post."""
        if self._author is None and self.user_id:
            self._author = User.get_by_id(self.user_id)
        return self._author
    
    def get_comments(self, include_unapproved=False, limit=None, offset=None):
        """Obtém os comentários do post."""
        if not supabase or not self.id:
            return []
        
        try:
            query = supabase.from_table("comments").eq("post_id", self.id)
            
            if not include_unapproved:
                query = query.eq("approved", True)
            
            query = query.order("created_at", ascending=True)
            
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
            
            results = query.execute()
            return [Comment._from_dict(item) for item in results]
        except Exception as e:
            print(f"Erro ao obter comentários do post: {str(e)}")
            return []
    
    def get_reading_time(self):
        """
        Calcula o tempo estimado de leitura com base no tamanho do conteúdo.
        Velocidade média de leitura: 200-250 palavras por minuto.
        Retorna o tempo de leitura em minutos.
        """
        if not self.content:
            return 1
        
        # Remover tags HTML, se presentes (abordagem simplificada)
        import re
        text = re.sub(r'<.*?>', '', self.content)
        
        # Contar palavras
        word_count = len(text.split())
        
        # Calcular tempo de leitura (usando 225 palavras por minuto como média)
        reading_time_minutes = max(1, round(word_count / 225))
        
        return reading_time_minutes

class Comment:
    """Modelo de comentário para interagir com a tabela 'comments' no Supabase."""
    
    def __init__(self, id=None, content=None, created_at=None, approved=False,
                 user_id=None, post_id=None):
        self.id = id
        self.content = content
        self.created_at = created_at or datetime.utcnow()
        self.approved = approved
        self.user_id = user_id
        self.post_id = post_id
        self._author = None
        self._post = None
    
    @classmethod
    def get_by_id(cls, comment_id):
        """Obtém um comentário pelo ID."""
        if not supabase:
            return None
        
        try:
            result = supabase.from_table("comments").get(comment_id)
            if result:
                return cls._from_dict(result)
            return None
        except Exception as e:
            print(f"Erro ao obter comentário por ID: {str(e)}")
            return None
    
    @classmethod
    def get_all(cls, include_unapproved=False, limit=None, offset=None):
        """Obtém todos os comentários."""
        if not supabase:
            return []
        
        try:
            query = supabase.from_table("comments")
            
            if not include_unapproved:
                query = query.eq("approved", True)
            
            query = query.order("created_at", ascending=False)
            
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
            
            results = query.execute()
            return [cls._from_dict(item) for item in results]
        except Exception as e:
            print(f"Erro ao obter todos os comentários: {str(e)}")
            return []
    
    @classmethod
    def get_by_user_id(cls, user_id, include_unapproved=False, limit=None, offset=None):
        """Obtém comentários de um usuário específico."""
        if not supabase:
            return []
        
        try:
            query = supabase.from_table("comments").eq("user_id", user_id)
            
            if not include_unapproved:
                query = query.eq("approved", True)
            
            query = query.order("created_at", ascending=False)
            
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
            
            results = query.execute()
            return [cls._from_dict(item) for item in results]
        except Exception as e:
            print(f"Erro ao obter comentários do usuário: {str(e)}")
            return []
    
    @classmethod
    def _from_dict(cls, data):
        """Cria uma instância de Comment a partir de um dicionário."""
        return cls(
            id=data.get("id"),
            content=data.get("content"),
            created_at=data.get("created_at"),
            approved=data.get("approved", False),
            user_id=data.get("user_id"),
            post_id=data.get("post_id")
        )
    
    def to_dict(self):
        """Converte a instância para um dicionário."""
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at,
            "approved": self.approved,
            "user_id": self.user_id,
            "post_id": self.post_id
        }
    
    def save(self):
        """Salva o comentário no banco de dados."""
        if not supabase:
            return False
        
        data = self.to_dict()
        
        if "id" in data and data["id"]:
            # Atualizar comentário existente
            try:
                result = supabase.from_table("comments").update(self.id, {
                    k: v for k, v in data.items() if k != "id" and k != "created_at"
                }, use_service_key=True)
                return bool(result)
            except Exception as e:
                print(f"Erro ao atualizar comentário: {str(e)}")
                return False
        else:
            # Inserir novo comentário
            try:
                result = supabase.from_table("comments").insert({
                    k: v for k, v in data.items() if k != "id"
                }, use_service_key=True)
                
                if result and len(result) > 0:
                    self.id = result[0].get("id")
                    return True
                return False
            except Exception as e:
                print(f"Erro ao inserir comentário: {str(e)}")
                return False
    
    def delete(self):
        """Exclui o comentário do banco de dados."""
        if not supabase or not self.id:
            return False
        
        try:
            return supabase.from_table("comments").delete(self.id, use_service_key=True)
        except Exception as e:
            print(f"Erro ao excluir comentário: {str(e)}")
            return False
    
    @property
    def author(self):
        """Obtém o autor do comentário."""
        if self._author is None and self.user_id:
            self._author = User.get_by_id(self.user_id)
        return self._author
    
    @property
    def post(self):
        """Obtém o post do comentário."""
        if self._post is None and self.post_id:
            self._post = Post.get_by_id(self.post_id)
        return self._post

# Função para carregamento de usuário, usada pelo Flask-Login
def load_user(user_id):
    """Carrega um usuário pelo ID."""
    return User.get_by_id(user_id) 