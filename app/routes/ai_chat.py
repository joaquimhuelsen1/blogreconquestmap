from flask import Blueprint, render_template, jsonify, request, session, flash, current_app, redirect, url_for
from flask_login import current_user, login_required
from app.forms import ChatMessageForm
from app import db
from app.models import User
import random
import time
import json
import os
from openai import OpenAI  # Importar o cliente OpenAI corretamente

# Configuração: desativar modo de simulação (usar API OpenAI)
SIMULATION_MODE = False

# Blueprint para IA de relacionamento
ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/ai_chat')

# Implementar função de fallback para caso de erro na API
def get_fallback_response(error_message):
    """Retorna uma resposta de fallback caso haja erro na API"""
    print(f"Erro na API. Usando resposta de fallback. Erro original: {error_message}")
    return "Desculpe, estou enfrentando dificuldades técnicas no momento. Nossa equipe já foi notificada do problema. Por favor, tente novamente mais tarde."

@ai_chat_bp.route('/ia-relacionamento', methods=['GET', 'POST'])
def ia_relacionamento():
    """Página de IA de Relacionamento"""
    # Verificar se o usuário está autenticado e é premium
    can_access_ai = current_user.is_authenticated and (current_user.is_premium or current_user.is_admin)
    
    # Bloquear acesso para usuários não premium
    if not can_access_ai:
        flash('Este recurso de IA é exclusivo para usuários premium.', 'info')
        return redirect(url_for('main.premium_subscription'))
    
    # Verificar se é uma requisição AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Debug da sessão
    print(f"[DEBUG] SID: {request.cookies.get('session', 'No session cookie')}")
    print(f"[DEBUG] Session no início da requisição: {session}")
    
    # Inicializar formulário
    form = ChatMessageForm()
    
    # Para requisições GET, retornar template normalmente
    if request.method == 'GET' or not is_ajax:
        if 'chat_messages' not in session:
            session['chat_messages'] = []
            session.modified = True
            
        # Como só usuários premium têm acesso, não precisamos mais verificar créditos
        # Definir créditos como ilimitados para usuários premium (-1)
        credits = -1  # -1 representa créditos ilimitados
            
        return render_template('public/ia_relacionamento.html', 
                              form=form, 
                              messages=session.get('chat_messages', []),
                              credits=credits)
    
    # Para requisições POST com AJAX
    if request.method == 'POST' and is_ajax:
        try:
            # Verificar se o usuário está autenticado
            if not current_user.is_authenticated:
                return jsonify({
                    'success': False,
                    'error': "Você precisa estar logado para enviar mensagens.",
                    'redirect': url_for('auth.login')
                })
            
            # Verificar se o usuário é premium (já não deveria chegar aqui se não for)
            if not current_user.is_premium and not current_user.is_admin:
                return jsonify({
                    'success': False,
                    'error': "Este recurso é exclusivo para usuários premium.",
                    'redirect': url_for('main.premium_subscription')
                })
            
            # Obter mensagem do usuário
            user_message = form.message.data
            print(f"Mensagem recebida: {user_message}")
            
            # Verificar se a mensagem é válida
            if user_message is None or user_message.strip() == '':
                # Mensagem inválida ou vazia
                print("Mensagem vazia ou inválida recebida")
                return jsonify({
                    'success': False,
                    'error': "Por favor, digite uma mensagem válida."
                })
            
            # Variável para armazenar a resposta do assistente
            assistant_response = None
            success = True
            error_message = None
            
            try:
                if SIMULATION_MODE:
                    # Resposta fixa para teste
                    assistant_response = "Obrigado por sua mensagem! Esta é uma resposta simulada (modo de teste)."
                    print("Usando modo de simulação - resposta fixa gerada")
                else:
                    # Usar OpenAI API para obter resposta, enviando APENAS a mensagem atual
                    api_response = get_openai_response(user_message)
                    
                    # Verificar se a resposta foi bem-sucedida
                    if api_response["success"]:
                        assistant_response = api_response["message"]
                    else:
                        success = False
                        assistant_response = api_response["message"]
                        print(f"Erro na API: {api_response['debug_info']}")
                    
            except Exception as api_error:
                # Capturar erros específicos da API e usar resposta de fallback
                print(f"Erro na API OpenAI: {str(api_error)}")
                error_message = str(api_error)
                assistant_response = get_fallback_response(error_message)
                success = False  # Marcar como erro, mas ainda retornar uma resposta
            
            # Atualizar sessão (de forma simples)
            if 'chat_messages' not in session:
                session['chat_messages'] = []
            
            # Adicionar mensagem ao histórico
            messages = session.get('chat_messages', [])
            messages.append({"user": user_message, "assistant": assistant_response})
            session['chat_messages'] = messages
            
            # Forçar gravação da sessão
            session.modified = True
            
            print(f"[DEBUG] Sessão após atualização: {session}")
            print(f"[DEBUG] Mensagens na sessão: {len(session.get('chat_messages', []))}")
            
            # Criar e retornar resposta JSON
            response = jsonify({
                'success': True,  # Sempre retorna sucesso para exibir a resposta
                'response': assistant_response,
                'credits_remaining': -1,  # -1 representa créditos ilimitados
                'api_error': error_message  # Incluir detalhes do erro para debug
            })
            response.headers['Content-Type'] = 'application/json'
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin') or '*'
            return response
            
        except Exception as e:
            print(f"ERRO: {str(e)}")
            import traceback
            error_details = traceback.format_exc()
            print(f"Detalhes do erro: {error_details}")
            
            # Retornar erro como JSON
            response = jsonify({
                'success': False,
                'error': f"Erro no servidor: {str(e)}"
            })
            response.headers['Content-Type'] = 'application/json'
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin') or '*'
            return response
            
    # Fallback para qualquer outro caso
    return jsonify({'success': False, 'error': 'Requisição inválida'})

def get_openai_response(user_message):
    """Obtém uma resposta do OpenAI Assistant enviando apenas a mensagem atual"""
    print("Iniciando chamada à API OpenAI - enviando apenas a mensagem atual")
    
    try:
        # Obter chaves da configuração da aplicação
        api_key = current_app.config['OPENAI_API_KEY']
        
        if not api_key:
            raise ValueError("Chave da API OpenAI não configurada. Verifique as variáveis de ambiente.")
        
        # Log detalhado da API key (primeiros 4 caracteres)
        key_preview = api_key[:4] + "..." if api_key else "None"
        print(f"Usando API key: {key_preview}")
        
        # Inicializar o cliente com a API key
        client = OpenAI(api_key=api_key, timeout=60.0)  # Aumentar timeout para 60 segundos
        print(f"Cliente OpenAI configurado com timeout de 60 segundos")
        
        # Criar uma solicitação para a API usando o novo cliente
        print(f"Enviando solicitação ao modelo gpt-3.5-turbo")
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Você é um especialista em relacionamentos e reconquista. Seu objetivo é ajudar pessoas a melhorarem seus relacionamentos amorosos e a reconquistar ex-parceiros de maneira saudável. Forneça conselhos práticos, diretos e personalizados para as situações descritas pelo usuário."
                    },
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            print(f"Resposta recebida da API com sucesso")
            
            # Extrair o texto da resposta (formato diferente com o novo cliente)
            assistant_response = response.choices[0].message.content
            
            return {
                "success": True,
                "message": assistant_response,
                "debug_info": "Resposta gerada com sucesso pela API OpenAI"
            }
        
        except Exception as api_error:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"ERRO NA CHAMADA DA API: {str(api_error)}")
            print(f"Traceback detalhado: {error_traceback}")
            
            # Tentar identificar o tipo de erro
            error_type = type(api_error).__name__
            error_message = str(api_error)
            
            print(f"Tipo de erro: {error_type}")
            print(f"Mensagem de erro: {error_message}")
            
            if "timeout" in error_message.lower():
                return {
                    "success": False,
                    "message": "A solicitação atingiu o tempo limite. Por favor, tente novamente.",
                    "debug_info": f"Timeout error: {error_message}"
                }
            elif "rate limit" in error_message.lower():
                return {
                    "success": False,
                    "message": "Estamos recebendo muitas solicitações no momento. Por favor, tente novamente em alguns minutos.",
                    "debug_info": f"Rate limit error: {error_message}"
                }
            elif "authentication" in error_message.lower() or "api key" in error_message.lower():
                return {
                    "success": False,
                    "message": "Erro de autenticação com o serviço de IA. Nossa equipe foi notificada.",
                    "debug_info": f"Auth error: {error_message}"
                }
            else:
                return {
                    "success": False,
                    "message": get_fallback_response(error_message),
                    "debug_info": f"API error: {error_message}"
                }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERRO NA CONFIGURAÇÃO DO OPENAI: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        return {
            "success": False,
            "message": get_fallback_response(str(e)),
            "debug_info": f"Setup error: {str(e)}"
        }

@ai_chat_bp.route('/limpar-chat', methods=['POST'])
def limpar_chat():
    """Limpa o histórico de chat da sessão atual"""
    try:
        print("Limpando chat. Sessão antes:", dict(session))
        
        # Remover o histórico de mensagens
        if 'chat_messages' in session:
            session.pop('chat_messages')
            print("Chat messages removido da sessão")
        
        # Também remover a thread atual
        if 'openai_thread_id' in session:
            session.pop('openai_thread_id')
            print("Thread ID removido da sessão")
        
        # Forçar a persistência da sessão
        session.modified = True
        print("Sessão após limpeza:", dict(session))
        
        # Resposta de sucesso
        response_data = {"success": True}
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERRO AO LIMPAR CHAT: {str(e)}")
        print(f"Detalhes: {error_details}")
        
        # Mensagem de erro
        response_data = {"success": False, "message": f"Erro ao limpar o histórico: {str(e)}"}
    
    # Garantir que a resposta seja sempre JSON com os cabeçalhos corretos
    response = jsonify(response_data)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin') or '*'
    return response 