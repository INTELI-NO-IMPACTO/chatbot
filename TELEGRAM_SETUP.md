# Configuração do Bot do Telegram

Este documento explica como configurar e executar o bot do Telegram para integração com a IA.

## 1. Criar o Bot no Telegram

1. Abra o Telegram e procure por **@BotFather**
2. Envie o comando `/newbot`
3. Escolha um nome para o bot (ex: "Assistente Para Pessoas Transgênero AI")
4. Escolha um username (deve terminar com "bot", ex: "assistente_trans_ai_bot")
5. O BotFather vai te enviar um **TOKEN** - guarde-o com cuidado!

Exemplo de token:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890
```

## 2. Configurar o Token no Projeto

1. Abra o arquivo `.env` na raiz do projeto
2. Localize a linha `TELEGRAM_BOT_TOKEN=SEU_TOKEN_DO_TELEGRAM_AQUI`
3. Substitua `SEU_TOKEN_DO_TELEGRAM_AQUI` pelo token que você recebeu do BotFather

Exemplo:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890
```

## 3. Instalar as Dependências

Execute o comando para instalar as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

## 4. Executar o Bot

Execute o bot com o seguinte comando:

```bash
python app/telegram_bot.py
```

Você deve ver a mensagem:
```
Bot iniciado com sucesso! Aguardando mensagens...
```

## 5. Testar o Bot

1. Abra o Telegram
2. Procure pelo username do seu bot (ex: @assistente_trans_ai_bot)
3. Clique em **Iniciar** ou envie `/start`
4. O bot deve responder com uma mensagem de boas-vindas!

## Comandos Disponíveis

O bot suporta os seguintes comandos:

- `/start` - Mostra a mensagem de boas-vindas
- `/ajuda` - Mostra informações de ajuda
- `/novo` - Inicia uma nova conversa (limpa o histórico)

## Funcionalidades

✅ **Conversação Contextualizada**: O bot mantém o histórico de conversas no banco de dados Supabase
✅ **Base de Conhecimento**: Utiliza os artigos em Markdown armazenados no Supabase
✅ **Múltiplos Usuários**: Cada usuário do Telegram tem sua própria sessão de chat
✅ **Persistência**: Todo o histórico é salvo no banco de dados

## Como Funciona

1. Quando um usuário envia uma mensagem:
   - O bot cria ou busca uma sessão de chat existente
   - Recupera o histórico das últimas 30 mensagens
   - Busca o contexto dos artigos no Supabase
   - Envia tudo para a API do OpenAI (GPT-4o-mini)
   - Salva a pergunta e resposta no banco de dados
   - Retorna a resposta para o usuário

2. A identificação do usuário é feita pelo Telegram User ID
3. Cada usuário tem um `session_id` único no formato: `telegram_{user_id}`

## Estrutura do Banco de Dados

O bot utiliza as seguintes tabelas do Supabase:

### Tabela `chats`
- `id`: ID único do chat
- `user_id`: ID do usuário (null para usuários do Telegram)
- `session_id`: ID da sessão (ex: "telegram_123456789")
- `title`: Título do chat
- `is_active`: Se o chat está ativo
- `created_at`: Data de criação
- `updated_at`: Data de última atualização

### Tabela `chat_messages`
- `id`: ID único da mensagem
- `chat_id`: Referência ao chat
- `role`: "user" ou "assistant"
- `content`: Conteúdo da mensagem
- `created_at`: Data de criação

## Executar em Produção

### Opção 1: Executar em Background (Linux/Mac)

```bash
nohup python app/telegram_bot.py > telegram_bot.log 2>&1 &
```

### Opção 2: Usar um Gerenciador de Processos (Recomendado)

Instale o `supervisor` ou `pm2`:

**Com PM2 (Node.js):**
```bash
npm install -g pm2
pm2 start app/telegram_bot.py --name telegram-bot --interpreter python3
pm2 save
pm2 startup
```

**Com Supervisor:**
```bash
sudo apt-get install supervisor
```

Crie um arquivo de configuração em `/etc/supervisor/conf.d/telegram_bot.conf`:

```ini
[program:telegram_bot]
directory=/caminho/para/seu/projeto/chatbot
command=/usr/bin/python3 app/telegram_bot.py
autostart=true
autorestart=true
stderr_logfile=/var/log/telegram_bot.err.log
stdout_logfile=/var/log/telegram_bot.out.log
```

Depois execute:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram_bot
```

### Opção 3: Deploy em Servidor (Heroku, Railway, etc.)

1. Crie um arquivo `Procfile` na raiz do projeto:
```
bot: python app/telegram_bot.py
```

2. Configure as variáveis de ambiente no painel do serviço
3. Faça o deploy do projeto

## Logs e Monitoramento

O bot gera logs com informações importantes:
- Mensagens recebidas
- Respostas enviadas
- Erros e exceções

Para ver os logs em tempo real:
```bash
# Se estiver usando PM2
pm2 logs telegram-bot

# Se estiver rodando diretamente
tail -f telegram_bot.log
```

## Segurança

⚠️ **IMPORTANTE**:
- Nunca compartilhe seu token do bot
- Nunca commite o arquivo `.env` no git
- Use variáveis de ambiente em produção
- Mantenha suas chaves de API seguras

## Troubleshooting

### Bot não responde
1. Verifique se o token está correto no `.env`
2. Verifique se o bot está rodando (`python app/telegram_bot.py`)
3. Veja os logs para identificar erros

### Erro "TELEGRAM_BOT_TOKEN não configurado"
- O arquivo `.env` não foi carregado corretamente
- Verifique se o token está no arquivo `.env`

### Erro ao conectar com Supabase
- Verifique as credenciais do Supabase no `.env`
- Confirme se as tabelas `chats` e `chat_messages` existem

### Erro ao conectar com OpenAI
- Verifique se a chave `OPENAI_API_KEY` está correta
- Confirme se você tem créditos disponíveis na sua conta OpenAI

## Próximos Passos

Possíveis melhorias futuras:
- [ ] Adicionar botões inline para navegação
- [ ] Implementar comando para feedback
- [ ] Adicionar suporte a áudio/voz
- [ ] Implementar rate limiting
- [ ] Adicionar analytics de uso
- [ ] Criar menu de comandos personalizado

## Suporte

Se tiver dúvidas ou problemas, consulte:
- [Documentação da python-telegram-bot](https://docs.python-telegram-bot.org/)
- [Documentação do Telegram Bot API](https://core.telegram.org/bots/api)
- [Documentação do Supabase](https://supabase.com/docs)
