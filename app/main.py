from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

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

class ChatResponse(BaseModel):
    response: str
    contexto_utilizado: bool

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
    Busca todos os documentos chamados 'ARTIGO' no bucket knowledge-base
    e concatena o conteúdo de todos eles.
    """
    try:
        # Lista todos os arquivos do bucket
        files = supabase.storage.from_(SUPABASE_BUCKET).list()
        
        contexto = ""
        artigos_encontrados = []
        
        # Filtra e processa apenas arquivos que contenham "ARTIGO" no nome
        for file in files:
            file_name = file.get('name', '')
            
            # Verifica se o arquivo contém "ARTIGO" no nome (case insensitive)
            if "artigo" in file_name.lower():
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
    Função auxiliar para buscar e concatenar todos os artigos.
    Retorna o contexto como string.
    """
    try:
        files = supabase.storage.from_(SUPABASE_BUCKET).list()
        contexto = ""
        
        for file in files:
            file_name = file.get('name', '')
            
            if "artigo" in file_name.lower():
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

@app.post("/chat", response_model=ChatResponse)
def chat_with_context(request: ChatRequest):
    """
    Endpoint para conversar com o ChatGPT usando o contexto dos artigos.
    
    O contexto é automaticamente adicionado antes da mensagem do usuário.
    """
    try:
        # Busca o contexto dos artigos
        contexto = get_contexto_artigos()
        
        if not contexto:
            raise HTTPException(status_code=500, detail="Não foi possível carregar o contexto dos artigos")
        
        # Monta o prompt com contexto + instrução + mensagem
        prompt_sistema = f"""{contexto}

Com base no texto acima, responda de forma sucinta, acolhedora e respeitosa às perguntas do usuário.
Você é um assistente especializado em orientar pessoas trans sobre:
- Retificação de nome e gênero
- Terapia hormonal (hormonização)
- Prevenção e tratamento de ISTs

Seja empático, claro e objetivo nas suas respostas."""
        
        # Chama a API do OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        resposta = response.choices[0].message.content
        
        # Print para debug
        print("\n" + "="*80)
        print(f"PERGUNTA DO USUÁRIO: {request.message}")
        print(f"RESPOSTA: {resposta}")
        print("="*80 + "\n")
        
        return {
            "response": resposta,
            "contexto_utilizado": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar chat: {str(e)}")
