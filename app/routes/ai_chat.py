from flask import Blueprint, render_template, jsonify, request, session, flash, current_app, redirect, url_for
from flask_login import current_user, login_required
from app.forms import ChatMessageForm
from app import db
from app.models import User
import random
import time
import json
from openai import OpenAI
import os

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
                    assistant_response = get_openai_response(user_message)
                    
                    # Não precisamos mais consumir créditos para usuários premium
                    
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
        assistant_id = current_app.config['OPENAI_ASSISTANT_ID']
        
        if not api_key or not assistant_id:
            raise ValueError("Chaves da API OpenAI não configuradas. Verifique as variáveis de ambiente.")
        
        client = OpenAI(api_key=api_key)
        print(f"Cliente OpenAI inicializado")
        
        # Criar uma nova thread para cada conversa (não mantém contexto entre mensagens)
        thread = client.beta.threads.create()
        thread_id = thread.id
        print(f"Nova thread criada: {thread_id[:8]}...")
        
        # Adicionar apenas a mensagem atual do usuário à thread
        print(f"Adicionando mensagem à thread")
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        print(f"Mensagem adicionada: {message.id[:8]}...")
        
        # Executar o assistente na nova thread
        print(f"Executando assistente na thread...")
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        print(f"Execução iniciada: {run.id[:8]}...")
        
        # Aguardar a conclusão
        timeout = 60  # segundos
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            print(f"Status: {run_status.status}")
            
            if run_status.status == 'completed':
                print("✓ Execução concluída com sucesso!")
                # Obter a resposta
                messages = client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                
                print(f"Número de mensagens: {len(messages.data)}")
                
                # A primeira mensagem (mais recente) deve ser a resposta
                if messages.data and len(messages.data) > 0:
                    assistant_message = messages.data[0]
                    if assistant_message.role == "assistant" and assistant_message.content:
                        response = assistant_message.content[0].text.value
                        print(f"Resposta do assistente: {response[:50]}...")
                        return response
                
                return "Não foi possível obter uma resposta clara do assistente."
            
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                error_msg = f"OpenAI falhou: {run_status.status}"
                if hasattr(run_status, 'last_error'):
                    error_msg += f" - {run_status.last_error}"
                print(f"Erro na execução: {error_msg}")
                raise Exception(error_msg)
            
            # Aguardar antes de verificar novamente
            time.sleep(1)
        
        # Se chegou aqui, é timeout
        print("Tempo limite excedido!")
        raise Exception("Tempo limite excedido para obter resposta do OpenAI")
        
    except Exception as e:
        print(f"Erro em get_openai_response: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

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