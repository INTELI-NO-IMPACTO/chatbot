from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

class Message(BaseModel):
    content: str

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

@app.post("/classify_intent", response_model=IntentResponse)
def classify_intent(message: Message):
    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": PROMPT_INTENT_CLASSIFICATION},
                {"role": "user", "content": f"Mensagem do usuário:{message.content}"},
            ],
        )

        raw_text = resp.output_text 
        raw_text = raw_text.strip().strip("`").strip()
        data = json.loads(raw_text)

        intent = str(data.get("intent", "")).strip().upper()
        if intent not in ALLOWED_INTENTS:
            intent = "NAO_ENTENDIDO"

        return {"intent": intent}

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao classificar a intenção: {e}")
