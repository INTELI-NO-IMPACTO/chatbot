"""
Bot do Telegram para integração com o sistema de AI
Permite que usuários conversem diretamente com a IA através do Telegram
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from openai import OpenAI
from supabase import create_client, Client
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Configurações
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

# Clientes
openai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurações do sistema
LINK_APLICACAO = "http://localhost:5173"  # Link da aplicação web
MENSAGENS_ANTES_LINK = 5  # Número de mensagens antes de enviar o link

# Armazena os chat_ids e contadores em memória (pode ser substituído por banco de dados)
user_sessions = {}
message_counters = {}  # Contador de mensagens por usuário
link_sent = {}  # Controla se o link já foi enviado para o usuário

def get_contexto_artigos():
    """
    Busca e concatena todos os arquivos .md do bucket Supabase.
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
                    logger.error(f"Erro ao processar arquivo {file_name}: {e}")

        return contexto
    except Exception as e:
        logger.error(f"Erro ao buscar contexto: {e}")
        return ""

def get_or_create_chat(telegram_user_id: int):
    """
    Busca ou cria um chat ativo para o usuário do Telegram.
    Retorna o ID do chat.
    """
    try:
        # Usa o Telegram user_id como session_id
        session_id = f"telegram_{telegram_user_id}"

        # Busca um chat ativo existente
        result = supabase.table('chats').select('id').eq('session_id', session_id).eq('is_active', True).order('created_at', desc=True).limit(1).execute()

        # Se encontrou um chat ativo, retorna o ID
        if result and result.data:
            return result.data[0]['id']

        # Caso contrário, cria um novo chat
        new_chat = {
            'user_id': None,  # Usuários do Telegram não têm user_id no sistema
            'session_id': session_id,
            'title': f'Telegram Chat - User {telegram_user_id}',
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        result = supabase.table('chats').insert(new_chat).execute()
        return result.data[0]['id']

    except Exception as e:
        logger.error(f"Erro ao buscar/criar chat: {e}")
        raise

def get_chat_history(chat_id: int, limit: int = 30):
    """
    Busca as últimas mensagens de um chat.
    Retorna lista de mensagens no formato [{"role": "user/assistant", "content": "..."}]
    """
    try:
        result = supabase.table('chat_messages').select('role, content').eq('chat_id', chat_id).order('created_at', desc=False).limit(limit).execute()

        if not result.data:
            return []

        messages = []
        for msg in result.data:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        return messages

    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
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
        logger.error(f"Erro ao salvar mensagem: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /start"""
    welcome_message = """
👋 Olá! Eu sou um assistente especializado em ajudar pessoas trans!

Posso te orientar sobre:
✅ Retificação de nome e gênero
✅ Terapia hormonal (hormonização)
✅ Prevenção e tratamento de ISTs

Comandos disponíveis:
/start - Mostra esta mensagem
/novo - Inicia uma nova conversa
/ajuda - Mostra informações de ajuda

Pode me perguntar o que quiser! Estou aqui para ajudar 💜
"""
    await update.message.reply_text(welcome_message)
    logger.info(f"Usuário {update.effective_user.id} iniciou o bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /ajuda"""
    help_message = """
📚 Como posso te ajudar:

Você pode me fazer perguntas sobre:

🏥 Retificação de nome:
- Como mudar meu nome no RG/CPF
- Documentos necessários
- Onde fazer a retificação

💊 Hormonização:
- Como iniciar terapia hormonal
- Locais de atendimento
- Acompanhamento médico

🩺 Prevenção de ISTs:
- Testagem e tratamento
- PrEP e PEP
- Cuidados com saúde sexual

Basta enviar sua pergunta que eu respondo! 💜
"""
    await update.message.reply_text(help_message)

async def new_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /novo - inicia uma nova conversa"""
    telegram_user_id = update.effective_user.id
    session_id = f"telegram_{telegram_user_id}"

    try:
        # Desativa o chat atual
        supabase.table('chats').update({'is_active': False}).eq('session_id', session_id).eq('is_active', True).execute()

        # Remove da sessão em memória e reseta contadores
        if telegram_user_id in user_sessions:
            del user_sessions[telegram_user_id]
        if telegram_user_id in message_counters:
            del message_counters[telegram_user_id]
        if telegram_user_id in link_sent:
            del link_sent[telegram_user_id]

        await update.message.reply_text("✨ Nova conversa iniciada! Como posso te ajudar?")
        logger.info(f"Usuário {telegram_user_id} iniciou nova conversa")

    except Exception as e:
        logger.error(f"Erro ao iniciar nova conversa: {e}")
        await update.message.reply_text("Desculpe, ocorreu um erro ao iniciar nova conversa. Tente novamente.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto"""
    telegram_user_id = update.effective_user.id
    user_message = update.message.text

    logger.info(f"Mensagem recebida de {telegram_user_id}: {user_message}")

    # Envia indicação de "digitando..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # 1. Busca ou cria um chat para o usuário
        chat_id = get_or_create_chat(telegram_user_id)
        user_sessions[telegram_user_id] = chat_id

        # 2. Busca o histórico de mensagens
        historico = get_chat_history(chat_id, limit=30)

        # 3. Busca o contexto dos artigos
        contexto = get_contexto_artigos()

        if not contexto:
            await update.message.reply_text("Desculpe, estou com problemas para acessar minha base de conhecimento. Tente novamente mais tarde.")
            return

        # 4. Monta o prompt do sistema
        prompt_sistema = f"""
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
- Use emojis e linguagem inclusiva quando apropriado
- Se não souber algo que não está na base de conhecimento, seja honesto
- Suas respostas devem ser diretas e objetivas (máximo 4 parágrafos)

════════════════════════════════════════════════════════════════════════════════
"""

        # 5. Monta a lista de mensagens
        messages = [{"role": "system", "content": prompt_sistema}]

        # 6. Adiciona o histórico
        if historico:
            historico_formatado = "\n════════════════════════════════════════════════════════════════════════════════\n"
            historico_formatado += f"💬 SEÇÃO 2: HISTÓRICO DA CONVERSA ({len(historico)} mensagens anteriores)\n"
            historico_formatado += "════════════════════════════════════════════════════════════════════════════════\n\n"

            for i, msg in enumerate(historico, 1):
                role_label = "USUÁRIO" if msg['role'] == 'user' else "ASSISTENTE"
                historico_formatado += f"[Mensagem {i} - {role_label}]:\n{msg['content']}\n\n"

            historico_formatado += "════════════════════════════════════════════════════════════════════════════════\n"

            messages.append({"role": "system", "content": historico_formatado})

        # 7. Adiciona a pergunta atual
        mensagem_atual = f"""
════════════════════════════════════════════════════════════════════════════════
❓ SEÇÃO 3: PERGUNTA ATUAL DO USUÁRIO
════════════════════════════════════════════════════════════════════════════════

{user_message}

════════════════════════════════════════════════════════════════════════════════
"""

        messages.append({"role": "user", "content": mensagem_atual})

        # 8. Chama a API do OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        resposta = response.choices[0].message.content

        # 9. Salva a mensagem do usuário e a resposta no banco
        save_message(chat_id, "user", user_message)
        save_message(chat_id, "assistant", resposta)

        # 10. Envia a resposta
        await update.message.reply_text(resposta)

        # 11. Incrementa o contador de mensagens do usuário
        if telegram_user_id not in message_counters:
            message_counters[telegram_user_id] = 0
        message_counters[telegram_user_id] += 1

        # 12. Verifica se deve enviar o link da aplicação
        should_send_link = (
            message_counters[telegram_user_id] >= MENSAGENS_ANTES_LINK and
            telegram_user_id not in link_sent
        )

        if should_send_link:
            link_message = f"""
💡 Vejo que você está interessado em saber mais!

Se preferir, temos uma aplicação web completa onde você pode:
✨ Navegar por todo o conteúdo de forma organizada
📱 Ter uma experiência mais visual e interativa
💬 Continuar suas conversas em qualquer dispositivo

🔗 Acesse aqui: {LINK_APLICACAO}

Mas fique à vontade para continuar conversando aqui no Telegram também! 💜
"""
            await update.message.reply_text(link_message)
            link_sent[telegram_user_id] = True
            logger.info(f"Link da aplicação enviado para usuário {telegram_user_id} após {message_counters[telegram_user_id]} mensagens")

        logger.info(f"Resposta enviada para {telegram_user_id}")

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        await update.message.reply_text(
            "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para erros"""
    logger.error(f"Erro: {context.error}")

def main():
    """Função principal para iniciar o bot"""

    # Verifica se o token foi configurado
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN não configurado no .env")
        return

    logger.info("Iniciando bot do Telegram...")

    # Cria a aplicação
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Registra os handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ajuda", help_command))
    application.add_handler(CommandHandler("novo", new_chat_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Registra o error handler
    application.add_error_handler(error_handler)

    # Inicia o bot
    logger.info("Bot iniciado com sucesso! Aguardando mensagens...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
