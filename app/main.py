from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Literal, Optional, List
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path
from datetime import datetime

# Carrega o .env do diretório raiz do projeto
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)  # override=True força sobrescrever variáveis do sistema

app = FastAPI()

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class Message(BaseModel):
    content: str

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None  # ID do usuário logado (opcional para compatibilidade)
    session_id: Optional[str] = None  # ID da sessão para usuários não logados

class ChatResponse(BaseModel):
    response: str
    contexto_utilizado: bool
    chat_id: Optional[int] = None  # ID do chat criado/usado
    historico_usado: bool = False  # Indica se usou histórico anterior

IntentLiteral = Literal[
    "RETIFICACAO_NOME",
    "HORMONIZACAO",
    "PREVENCAO_IST",
    "DESPEDIDA",
    "BOAS_VINDAS",
    "NAO_ENTENDIDO",
    "OUTROS",
]

class IntentResponse(BaseModel):
    intent: IntentLiteral

ALLOWED_INTENTS = {
    "RETIFICACAO_NOME",
    "HORMONIZACAO",
    "PREVENCAO_IST",
    "DESPEDIDA",
    "BOAS_VINDAS",
    "NAO_ENTENDIDO",
    "OUTROS",
}

PROMPT_INTENT_CLASSIFICATION = """
Você é um classificador de intenção para um chatbot acolhedor voltado para pessoas trans, focado em orientar sobre retificação de nome, acesso à hormonização e prevenção a ISTs.

Sua tarefa é analisar a mensagem do usuário e identificar qual intenção ela representa, escolhendo apenas UMA das categorias abaixo:

INTENÇÕES DISPONÍVEIS:
- RETIFICACAO_NOME
- HORMONIZACAO
- PREVENCAO_IST
- DESPEDIDA
- BOAS_VINDAS
- OUTROS
- NAO_ENTENDIDO  (use se a mensagem for vaga ou não se encaixar em nenhuma das categorias acima)

Regras importantes:

• RETIFICACAO_NOME: menções a retificação/troca de nome, certidão, RG, registro civil, cartório, Defensoria Pública, alteração de gênero em documentos.
• HORMONIZACAO: menções a hormonização (HRT), hormônios, acompanhamento médico, ambulatório trans, endocrinologista, consultas relacionadas à hormonização.
• PREVENCAO_IST: menções a prevenção a IST, testagem, PEP, PrEP, preservativos, saúde sexual, acompanhamento sexual seguro.
• DESPEDIDA: apenas encerramento (“obrigado”, “valeu”, “até mais”, “tchau”, “só isso”). Se houver despedida + pedido, ignore a despedida e classifique pelo pedido.
• BOAS_VINDAS: apenas saudação (“oi”, “olá”, “boa tarde”, “e aí”). Se houver saudação + pergunta, ignore a saudação e classifique pela pergunta.
• NAO_ENTENDIDO: quando a intenção da mensagem não ficar claro.
• OUTROS: quando a mensagem for sobre temas que tanganciem o escopo principal, como dúvidas sobre outros assuntos não abordados nessas intenções.

FORMATO DE SAÍDA (OBRIGATÓRIO):
Responda exatamente em JSON, sem crases e sem texto extra:
{"intent":"<UMA_DAS_INTENCOES_EM_MAIUSCULAS>"}
""".strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Debug: verifica se as variáveis foram carregadas
print("\n" + "="*80)
print("🔍 VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE")
print("="*80)
print(f"✅ OPENAI_API_KEY carregada: {OPENAI_API_KEY[:20]}..." if OPENAI_API_KEY else "❌ OPENAI_API_KEY NÃO encontrada")
print(f"✅ SUPABASE_URL: {SUPABASE_URL}" if SUPABASE_URL else "❌ SUPABASE_URL NÃO encontrada")
print(f"✅ SUPABASE_BUCKET: {SUPABASE_BUCKET}" if SUPABASE_BUCKET else "❌ SUPABASE_BUCKET NÃO encontrada")
print("="*80 + "\n")

@app.post("/classify_intent", response_model=IntentResponse)
def classify_intent(message: Message):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_INTENT_CLASSIFICATION},
                {"role": "user", "content": f"Mensagem do usuário:{message.content}"},
            ],
            temperature=0.3
        )

        raw_text = resp.choices[0].message.content
        raw_text = raw_text.strip().strip("`").strip()
        data = json.loads(raw_text)

        intent = str(data.get("intent", "")).strip().upper()
        if intent not in ALLOWED_INTENTS:
            intent = "NAO_ENTENDIDO"

        return {"intent": intent}

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao classificar a intenção: {e}")

@app.get("/concatenate_artigos")
def concatenate_artigos():
    """
    Busca todos os documentos .md do bucket knowledge-base
    e concatena o conteúdo de todos eles.
    """
    try:
        # Lista todos os arquivos do bucket
        files = supabase.storage.from_(SUPABASE_BUCKET).list()
        
        contexto = ""
        artigos_encontrados = []
        
        # Filtra e processa apenas arquivos .md
        for file in files:
            file_name = file.get('name', '')
            
            # Verifica se o arquivo termina com .md (case insensitive)
            if file_name.lower().endswith('.md'):
                artigos_encontrados.append(file_name)
                
                # Faz o download do conteúdo do arquivo
                try:
                    response = supabase.storage.from_(SUPABASE_BUCKET).download(file_name)
                    
                    # Decodifica o conteúdo (assumindo que são arquivos de texto)
                    conteudo = response.decode('utf-8')
                    
                    # Adiciona ao contexto com separador
                    contexto += f"\n\n{'='*50}\n"
                    contexto += f"CONTEÚDO DO ARQUIVO: {file_name}\n"
                    contexto += f"{'='*50}\n\n"
                    contexto += conteudo
                    
                except Exception as e:
                    print(f"Erro ao processar arquivo {file_name}: {e}")
                    contexto += f"\n\n[ERRO ao processar {file_name}: {e}]\n\n"
        
        # Print no console para verificação
        print("\n" + "="*80)
        print(f"TOTAL DE ARTIGOS ENCONTRADOS: {len(artigos_encontrados)}")
        print(f"ARQUIVOS: {artigos_encontrados}")
        print("="*80)
        print("\nCONTEXTO CONCATENADO:")
        print(contexto)
        print("\n" + "="*80)
        
        return {
            "success": True,
            "total_artigos": len(artigos_encontrados),
            "arquivos": artigos_encontrados,
            "contexto": contexto
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar artigos: {str(e)}")

def get_contexto_artigos():
    """
    Função auxiliar para buscar e concatenar todos os arquivos .md.
    Retorna o contexto como string.
    """
    try:
        files = supabase.storage.from_(SUPABASE_BUCKET).list()
        contexto = ""
        
        for file in files:
            file_name = file.get('name', '')
            
            if file_name.lower().endswith('.md'):
                try:
                    response = supabase.storage.from_(SUPABASE_BUCKET).download(file_name)
                    conteudo = response.decode('utf-8')
                    contexto += f"\n\n{'='*50}\n"
                    contexto += f"CONTEÚDO DO ARQUIVO: {file_name}\n"
                    contexto += f"{'='*50}\n\n"
                    contexto += conteudo
                except Exception as e:
                    print(f"Erro ao processar arquivo {file_name}: {e}")
        
        return contexto
    except Exception as e:
        print(f"Erro ao buscar contexto: {e}")
        return ""

def get_or_create_chat(user_id: Optional[int], session_id: Optional[str]):
    """
    Busca ou cria um chat ativo para o usuário ou sessão.
    Retorna o ID do chat.
    """
    try:
        # Se não tiver nem user_id nem session_id, cria um temporário
        if not user_id and not session_id:
            session_id = f"temp_{datetime.now().timestamp()}"
        
        # Busca um chat ativo existente
        if user_id:
            # Verifica se o usuário existe na tabela users
            user_check = supabase.table('users').select('id').eq('id', user_id).execute()
            
            # Se o usuário não existir, usa session_id ao invés
            if not user_check.data:
                print(f"⚠️ User ID {user_id} não encontrado, usando session_id")
                session_id = f"user_{user_id}_temp"
                user_id = None
                result = supabase.table('chats').select('id').eq('session_id', session_id).eq('is_active', True).order('created_at', desc=True).limit(1).execute()
            else:
                result = supabase.table('chats').select('id').eq('user_id', user_id).eq('is_active', True).order('created_at', desc=True).limit(1).execute()
        elif session_id:
            result = supabase.table('chats').select('id').eq('session_id', session_id).eq('is_active', True).order('created_at', desc=True).limit(1).execute()
        else:
            result = None
        
        # Se encontrou um chat ativo, retorna o ID
        if result and result.data:
            return result.data[0]['id']
        
        # Caso contrário, cria um novo chat
        new_chat = {
            'user_id': user_id,  # Pode ser None
            'session_id': session_id,
            'title': 'Nova conversa',
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table('chats').insert(new_chat).execute()
        return result.data[0]['id']
        
    except Exception as e:
        print(f"Erro ao buscar/criar chat: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerenciar chat: {str(e)}")

def get_chat_history(chat_id: int, limit: int = 30):
    """
    Busca as últimas mensagens de um chat.
    Retorna lista de mensagens no formato [{"role": "user/assistant", "content": "..."}]
    """
    try:
        result = supabase.table('chat_messages').select('role, content').eq('chat_id', chat_id).order('created_at', desc=False).limit(limit).execute()
        
        if not result.data:
            return []
        
        # Converte para o formato esperado pela OpenAI
        messages = []
        for msg in result.data:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        return messages
        
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return []

def save_message(chat_id: int, role: str, content: str):
    """
    Salva uma mensagem no banco de dados.
    """
    try:
        message = {
            'chat_id': chat_id,
            'role': role,
            'content': content,
            'created_at': datetime.now().isoformat()
        }
        
        supabase.table('chat_messages').insert(message).execute()
        
        # Atualiza o timestamp do chat
        supabase.table('chats').update({'updated_at': datetime.now().isoformat()}).eq('id', chat_id).execute()
        
    except Exception as e:
        print(f"Erro ao salvar mensagem: {e}")
        # Não lança exceção para não quebrar o fluxo

def get_user_info(user_id: int) -> Optional[dict]:
    """
    Busca as informações do usuário (nome, nome social e pronome) da tabela users.
    Retorna um dict com 'name', 'social_name' e 'pronoun', ou None se não encontrado.
    """
    try:
        result = supabase.table('users').select('name, social_name, pronoun').eq('id', user_id).single().execute()
        if result.data:
            return {
                'name': result.data.get('name'),
                'social_name': result.data.get('social_name'),
                'pronoun': result.data.get('pronoun')
            }
        return None
    except Exception as e:
        print(f"Erro ao buscar informações do usuário: {e}")
        return None

def get_preferred_name_and_pronoun(user_id: Optional[int]) -> Optional[dict]:
    """
    Retorna o nome preferido e pronome do usuário.
    Prioriza nome social sobre nome.
    Retorna: {'name': str, 'pronoun': str} ou None
    """
    if not user_id:
        return None
    
    user_info = get_user_info(user_id)
    if not user_info:
        return None
    
    # Prioriza o nome social, se disponível
    preferred_name = user_info.get('social_name') or user_info.get('name')
    pronoun = user_info.get('pronoun')
    
    if not preferred_name:
        return None
    
    return {
        'name': preferred_name,
        'pronoun': pronoun if pronoun else None
    }

@app.post("/chat", response_model=ChatResponse)
def chat_with_context(request: ChatRequest):
    """
    Endpoint para conversar com o ChatGPT usando o contexto dos artigos e histórico de conversas.
    
    O contexto dos artigos é automaticamente adicionado.
    O histórico das últimas 30 mensagens é recuperado do banco de dados.
    Se o usuário estiver autenticado (user_id), busca o nome social ou nome da tabela users.
    """
    try:
        # 1. Busca ou cria um chat para o usuário/sessão
        chat_id = get_or_create_chat(request.user_id, request.session_id)
        
        # 2. Busca o histórico de mensagens (últimas 30)
        historico = get_chat_history(chat_id, limit=30)
        historico_usado = len(historico) > 0
        
        # 3. Busca o nome e pronome do usuário (se estiver autenticado)
        user_info = get_preferred_name_and_pronoun(request.user_id)
        user_name = user_info.get('name') if user_info else None
        user_pronoun = user_info.get('pronoun') if user_info else None
        
        # 4. Busca o contexto dos artigos
        contexto = get_contexto_artigos()
        
        if not contexto:
            raise HTTPException(status_code=500, detail="Não foi possível carregar o contexto dos artigos")
        
        # 5. Monta o prompt do sistema com divisões claras
        # Adiciona seção do nome e pronome se disponível
        nome_section = ""
        if user_name:
            pronoun_text = f"\n🗣️ PRONOME PREFERIDO: {user_pronoun}" if user_pronoun else ""
            nome_section = f"""
════════════════════════════════════════════════════════════════════════════════
👤 INFORMAÇÕES DO(A) INTERLOCUTOR(A)
════════════════════════════════════════════════════════════════════════════════

📛 NOME: {user_name}{pronoun_text}

INSTRUÇÕES DE USO:
- Use o nome de forma respeitosa e acolhedora durante a conversa
- Personalize suas respostas chamando a pessoa pelo nome quando apropriado
- {"Use o pronome '" + user_pronoun + "' nas conjugações e referências" if user_pronoun else "Use linguagem neutra quando não souber o pronome"}
- Exemplos de linguagem inclusiva: "bem-vinde", "queride" (quando aplicável)

════════════════════════════════════════════════════════════════════════════════
"""
        
        prompt_sistema = f"""{nome_section}
════════════════════════════════════════════════════════════════════════════════
📚 SEÇÃO 1: BASE DE CONHECIMENTO (Artigos de Referência)
════════════════════════════════════════════════════════════════════════════════

{contexto}

════════════════════════════════════════════════════════════════════════════════
🎯 INSTRUÇÕES PARA O ASSISTENTE
════════════════════════════════════════════════════════════════════════════════

Você é um assistente especializado em orientar pessoas trans sobre:
- Retificação de nome e gênero
- Terapia hormonal (hormonização)
- Prevenção e tratamento de ISTs

IMPORTANTE:
- Use APENAS as informações da BASE DE CONHECIMENTO acima
- Se houver HISTÓRICO DE CONVERSAS abaixo, mantenha coerência com elas
- Responda de forma sucinta, acolhedora e respeitosa
- Use emojis quando apropriado, mas de forma moderada
- Não use termos muito técnicos e evite reforçar esteriótipos
- Se não souber algo que não está na base de conhecimento, seja honesto
- Use linguagem neutra e inclusiva sempre

════════════════════════════════════════════════════════════════════════════════
"""
        
        # 6. Monta a lista de mensagens
        messages = [{"role": "system", "content": prompt_sistema}]
        
        # 7. Adiciona o histórico com marcação clara
        if historico:
            historico_formatado = "\n════════════════════════════════════════════════════════════════════════════════\n"
            historico_formatado += f"💬 SEÇÃO 2: HISTÓRICO DA CONVERSA ({len(historico)} mensagens anteriores)\n"
            historico_formatado += "════════════════════════════════════════════════════════════════════════════════\n\n"
            
            for i, msg in enumerate(historico, 1):
                role_label = "USUÁRIO" if msg['role'] == 'user' else "ASSISTENTE"
                historico_formatado += f"[Mensagem {i} - {role_label}]:\n{msg['content']}\n\n"
            
            historico_formatado += "════════════════════════════════════════════════════════════════════════════════\n"
            
            # Adiciona como mensagem do sistema para contexto
            messages.append({"role": "system", "content": historico_formatado})
        
        # 7. Adiciona separador e a pergunta atual
        mensagem_atual = f"""
════════════════════════════════════════════════════════════════════════════════
❓ SEÇÃO 3: PERGUNTA ATUAL DO USUÁRIO
════════════════════════════════════════════════════════════════════════════════

{request.message}

════════════════════════════════════════════════════════════════════════════════
"""
        
        messages.append({"role": "user", "content": mensagem_atual})
        
        # 8. Chama a API do OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        resposta = response.choices[0].message.content
        
        # 7. Salva a mensagem do usuário e a resposta no banco
        save_message(chat_id, "user", request.message)
        save_message(chat_id, "assistant", resposta)
        
        # Print para debug
        print("\n" + "="*80)
        print(f"💬 CHAT ID: {chat_id}")
        if user_name:
            pronoun_display = f" ({user_pronoun})" if user_pronoun else ""
            print(f"👤 NOME DO USUÁRIO: {user_name}{pronoun_display}")
        else:
            print(f"👤 NOME DO USUÁRIO: Anônimo")
        print(f"� HISTÓRICO USADO: {len(historico)} mensagens")
        print(f"❓ PERGUNTA DO USUÁRIO: {request.message}")
        print(f"🤖 RESPOSTA: {resposta}")
        print("="*80 + "\n")
        
        return {
            "response": resposta,
            "contexto_utilizado": True,
            "chat_id": chat_id,
            "historico_usado": historico_usado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar chat: {str(e)}")

@app.get("/chat/history/{chat_id}")
def get_chat_history_endpoint(chat_id: int, limit: int = 50):
    """
    Busca o histórico de mensagens de um chat específico.
    """
    try:
        messages = get_chat_history(chat_id, limit)
        return {
            "chat_id": chat_id,
            "total_messages": len(messages),
            "messages": messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {str(e)}")

@app.get("/chats/user/{user_id}")
def get_user_chats(user_id: int):
    """
    Lista todos os chats de um usuário.
    """
    try:
        result = supabase.table('chats').select('id, title, created_at, updated_at, is_active').eq('user_id', user_id).order('updated_at', desc=True).execute()
        
        return {
            "user_id": user_id,
            "total_chats": len(result.data),
            "chats": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar chats: {str(e)}")

@app.delete("/chat/{chat_id}")
def delete_chat(chat_id: int):
    """
    Desativa um chat (soft delete).
    """
    try:
        supabase.table('chats').update({'is_active': False}).eq('id', chat_id).execute()
        return {"success": True, "message": f"Chat {chat_id} desativado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desativar chat: {str(e)}")

@app.post("/chat/{chat_id}/new")
def start_new_chat(user_id: Optional[int] = None, session_id: Optional[str] = None):
    """
    Inicia um novo chat para o usuário (desativa o atual e cria um novo).
    """
    try:
        # Desativa chats antigos
        if user_id:
            supabase.table('chats').update({'is_active': False}).eq('user_id', user_id).eq('is_active', True).execute()
        elif session_id:
            supabase.table('chats').update({'is_active': False}).eq('session_id', session_id).eq('is_active', True).execute()
        
        # Cria novo chat
        chat_id = get_or_create_chat(user_id, session_id)
        
        return {
            "success": True,
            "chat_id": chat_id,
            "message": "Novo chat criado com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar novo chat: {str(e)}")
