# 🏳️‍⚧️ Projeto: Chatbot Inclusivo de Orientação para Pessoas Trans

## 🤖 Sistema de Processamento de Linguagem Natural para Suporte e Acolhimento

Um assistente inteligente especializado em fornecer informações acessíveis e acolhedoras sobre retificação de nome, terapia hormonal e prevenção de ISTs para a comunidade trans.

---

# 👥 Equipe: INTELI-NO-IMPACTO

| Integrante 1 | Integrante 2 | Integrante 3 | Integrante 4 |
| :----------: | :----------: | :----------: | :----------: |
| <img src="https://media.licdn.com/dms/image/v2/D4D03AQFpuCHH7zRE6w/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1678716198904?e=1762992000&v=beta&t=RLdzg-MCyoqVbXLt6OSLU6LigBP3GfagPndLGp9gPmI" width="150" alt="Fernando Machado"> <br> [**Fernando Machado**](https://www.linkedin.com/in/fernando-machado-santos) | <img src="https://media.licdn.com/dms/image/v2/D4D03AQFEWbbQZVzBTA/profile-displayphoto-scale_400_400/B4DZl9519rH4Ak-/0/1758753940232?e=1762992000&v=beta&t=7O3oUlf2K3jwN66gi32vdRYfCjPyceCP_qCtPS9WVbQ" width="150" alt="Gabriel Pelinsari"> <br> [**Gabriel Pelinsari**](https://www.linkedin.com/in/gabriel-pelinsari) | <img src="https://media.licdn.com/dms/image/v2/D4D03AQF9VYDA7dTAkw/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1678714840944?e=1762992000&v=beta&t=v8BNYFBASek__LV44Ie1DkBWZEUaIwizMEeOHB7eUDI" width="150" alt="João Paulo Silva"> <br> [**João Paulo Silva**](https://www.linkedin.com/in/joão-paulo-da-silva-a45229215) | <img src="https://media.licdn.com/dms/image/v2/D4D03AQHprrQcSOWJ_w/profile-displayphoto-crop_800_800/B4DZlo.DN1JgAI-/0/1758402722996?e=1762992000&v=beta&t=0vmN2_Ec3DzEdHvQoUnycjyhaNHGDTUWSRJztYcC-Cc" width="150" alt="Matheus Ribeiro"> <br> [**Matheus Ribeiro**](https://www.linkedin.com/in/omatheusrsantos) |


---

# 📖 Descrição

Este projeto nasceu da necessidade de criar um **assistente virtual acolhedor e inclusivo** para a comunidade trans brasileira. O chatbot utiliza **Processamento de Linguagem Natural (PLN)** e **Inteligência Artificial** para fornecer informações precisas, respeitosas e personalizadas sobre três áreas principais:

- 🏥 **Retificação de Nome e Gênero**: Orientações sobre documentação, processos legais e cartórios
- 💊 **Hormonização**: Informações sobre terapia hormonal, acompanhamento médico e locais de atendimento
- 🩺 **Prevenção de ISTs**: Testagem, tratamento, PrEP, PEP e cuidados com saúde sexual

### 🎯 Diferenciais do Projeto

- **Personalização por Pronomes**: Sistema de reconhecimento e uso correto de pronomes (ele/ela/elu)
- **Priorização de Nome Social**: Respeita a identidade de gênero usando nome social quando disponível
- **Múltiplas Plataformas**: Disponível via API REST e Telegram Bot
- **Base de Conhecimento Dinâmica**: Conteúdo atualizado através de arquivos markdown no Supabase
- **Histórico Contextual**: Mantém coerência em conversas de múltiplas mensagens
- **Linguagem Inclusiva**: Tom acolhedor, emojis apropriados e terminologia respeitosa

---

# 📂 Estrutura de Pastas

```
📁 chatbot/
├── 📂 app/                          # Aplicação principal
│   ├── 📄 main.py                   # API REST FastAPI com endpoints de chat
│   ├── 📄 telegram_bot.py           # Bot do Telegram com integração completa
│
├── 📄 requirements.txt              # Dependências Python
├── 📄 .gitignore                    # Arquivos ignorados pelo Git
└── 📄 README.md                     # Este arquivo
```

---

# 🏗️ Arquitetura do Sistema

## Componentes Principais

### 1. 🚀 API REST (FastAPI)
- **Endpoint `/chat`**: Recebe mensagens e retorna respostas da IA
- **Endpoint `/classify_intent`**: Classifica a intenção da mensagem do usuário
- **Endpoint `/concatenate_artigos`**: Gerencia a base de conhecimento
- **Autenticação**: Suporta usuários autenticados (`user_id`) e anônimos (`session_id`)
- **Personalização**: Busca nome social e pronome do banco de dados

### 2. 🤖 Telegram Bot
- **Comandos**:
  - `/start` - Inicia conversa com mensagem de boas-vindas
  - `/ajuda` - Mostra informações de ajuda
  - `/novo` - Inicia uma nova conversa (reseta histórico)
- **Features**:
  - Compartilhamento inteligente de link da aplicação web (após 5 mensagens)
  - Indicador de "digitando..." para melhor UX
  - Logs detalhados para monitoramento
  - Gerenciamento de sessão por usuário do Telegram

### 3. 🗄️ Banco de Dados (Supabase)
- **Tabela `users`**: Armazena informações dos usuários (name, social_name, pronoun)
- **Tabela `chats`**: Gerencia conversas (user_id, session_id, is_active)
- **Tabela `chat_messages`**: Histórico de mensagens (role, content, timestamps)
- **Storage Bucket**: Armazena artigos markdown (.md) da base de conhecimento

### 4. 🧠 Inteligência Artificial
- **Modelo**: OpenAI GPT-4o-mini
- **Temperatura**: 0.7 (equilíbrio entre criatividade e precisão)
- **Max Tokens**: 1000
- **Prompt Estruturado**: 3 seções claramente definidas (conhecimento, histórico, pergunta atual)

---

# 🔧 Tecnologias Utilizadas

## Backend
- **FastAPI** (0.120.0) - Framework web moderno e assíncrono
- **Uvicorn** (0.38.0) - Servidor ASGI de alta performance
- **Python 3.8+** - Linguagem de programação

## Inteligência Artificial
- **OpenAI API** (2.0.0+) - Processamento de linguagem natural
- **GPT-4o-mini** - Modelo de linguagem avançado

## Banco de Dados & Storage
- **Supabase** (2.0.0+) - Backend-as-a-Service (PostgreSQL + Storage)
- **PostgreSQL** - Banco de dados relacional

## Integrações
- **python-telegram-bot** (21.0+) - SDK oficial do Telegram
- **python-dotenv** (1.1.1) - Gerenciamento de variáveis de ambiente
- **httpx** (0.26-0.28) - Cliente HTTP assíncrono

## DevOps & Ferramentas
- **Pydantic** (2.12.3) - Validação de dados
- **Git** - Controle de versão
- **Conventional Commits** - Padrão de commits

---

# ⚙️ Requisitos

## Hardware Mínimo
- **Processador**: Dual-core 2.0 GHz ou superior
- **Memória RAM**: Mínimo 4GB (recomendado 8GB+)
- **Armazenamento**: 500MB de espaço livre
- **Conexão Internet**: Necessária para APIs externas

## Software
- **Python**: Versão 3.8 ou superior
- **pip**: Gerenciador de pacotes Python
- **Git**: Para clonar o repositório
- **Navegador Web**: Chrome, Firefox, Edge ou Safari (versões atualizadas)
- **Sistema Operacional**: Windows 10/11, macOS 10.14+, ou Linux (Ubuntu 20.04+)

## Contas e Chaves Necessárias
- **Conta OpenAI** com API Key
- **Conta Supabase** (projeto configurado)
- **Bot do Telegram** (token obtido via @BotFather) - opcional

---

# 🚀 Instruções para Execução

## 1. Clone o Repositório

```bash
git clone https://github.com/INTELI-NO-IMPACTO/chatbot.git
cd chatbot
```

## 2. Configure o Ambiente Virtual

### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

## 4. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-api-key-here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET=knowledge-base

# Telegram Bot (opcional)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

### Como Obter as Chaves:

**OpenAI API Key:**
1. Acesse [platform.openai.com](https://platform.openai.com/)
2. Faça login ou crie uma conta
3. Vá em "API Keys" e clique em "Create new secret key"

**Supabase:**
1. Acesse [supabase.com](https://supabase.com/)
2. Crie um novo projeto
3. Vá em Settings > API
4. Copie a URL e a Service Role Key

**Telegram Bot Token:**
1. Abra o Telegram e busque por @BotFather
2. Envie `/newbot` e siga as instruções
3. Copie o token fornecido

## 5. Configure o Banco de Dados

### Estrutura das Tabelas (SQL)

Execute no SQL Editor do Supabase:

```sql
-- Tabela de usuários
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    social_name VARCHAR(255),
    pronoun VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de chats
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(255),
    title VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de mensagens
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_chats_session_id ON chats(session_id);
CREATE INDEX idx_chat_messages_chat_id ON chat_messages(chat_id);
```

### Configuração do Storage Bucket

1. No Supabase, vá em **Storage**
2. Crie um bucket chamado `knowledge-base`
3. Configure como **público** ou **privado** (conforme necessidade)
4. Faça upload dos arquivos `.md` com o conteúdo informativo

**Exemplo de estrutura de arquivo .md:**
```markdown
# Retificação de Nome

## O que é?
A retificação de nome é o processo legal para alterar...

## Documentos Necessários
- Certidão de nascimento
- RG e CPF
- Comprovante de residência...
```

## 6. Execute a Aplicação

### Opção A: API REST (FastAPI)

```bash
cd app
uvicorn main:app --reload --port 8000
```

A API estará disponível em: `http://localhost:8000`

**Documentação Interativa:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Opção B: Telegram Bot

```bash
cd app
python telegram_bot.py
```

O bot começará a responder mensagens no Telegram!

### Opção C: Executar Ambos (Produção)

Em terminais separados:

```bash
# Terminal 1 - API REST
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Telegram Bot
python app/telegram_bot.py
```

---

# 📡 Endpoints da API

## 🔹 POST `/chat`

Envia uma mensagem e recebe resposta do chatbot.

**Request Body:**
```json
{
  "message": "Como faço para retificar meu nome?",
  "user_id": 123,           // Opcional: usuário autenticado
  "session_id": "abc-123"   // Opcional: sessão anônima
}
```

**Response:**
```json
{
  "response": "Para retificar seu nome, você precisa...",
  "contexto_utilizado": true,
  "chat_id": 45,
  "historico_usado": true
}
```

## 🔹 POST `/classify_intent`

Classifica a intenção da mensagem do usuário.

**Request Body:**
```json
{
  "content": "Quero saber sobre hormonização"
}
```

**Response:**
```json
{
  "intent": "HORMONIZACAO"
}
```

**Intenções Possíveis:**
- `RETIFICACAO_NOME`
- `HORMONIZACAO`
- `PREVENCAO_IST`
- `BOAS_VINDAS`
- `DESPEDIDA`
- `OUTROS`
- `NAO_ENTENDIDO`

## 🔹 GET `/concatenate_artigos`

Retorna todos os artigos da base de conhecimento concatenados.

**Response:**
```json
{
  "success": true,
  "total_artigos": 5,
  "arquivos": ["retificacao.md", "hormonizacao.md", "ists.md"],
  "contexto": "Conteúdo concatenado dos artigos..."
}
```

---

# 🤖 Comandos do Telegram Bot

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `/start` | Inicia o bot e mostra mensagem de boas-vindas |
| `/ajuda` | Exibe informações de ajuda e tópicos disponíveis |
| `/novo` | Inicia uma nova conversa (limpa histórico) |

## Funcionalidades Especiais

### 🎯 Compartilhamento Inteligente de Link
- Após **5 mensagens**, o bot automaticamente compartilha o link da aplicação web
- Mensagem natural e não-invasiva
- Enviado apenas **uma vez por conversa**
- Reseta ao usar `/novo`

### 💬 Experiência de Usuário
- Indicador "digitando..." enquanto processa a resposta
- Respostas em até 4 parágrafos para facilitar leitura no mobile
- Emojis para melhor visualização
- Tom acolhedor e inclusivo

---

# 🧪 Testando o Sistema

## Teste da API REST

### Usando cURL:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Como funciona a retificação de nome?",
    "user_id": 1
  }'
```

### Usando Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "Onde fazer hormonização?",
        "user_id": 1
    }
)

print(response.json())
```

## Teste do Telegram Bot

1. Abra o Telegram
2. Busque pelo seu bot (nome definido no @BotFather)
3. Envie `/start`
4. Faça perguntas sobre os tópicos disponíveis
5. Após 5 mensagens, verifique o compartilhamento do link

---

# 📊 Processamento de Dados e Fluxo

## 1. Recebimento da Mensagem
```
Usuário → [API/Telegram] → Validação
```

## 2. Identificação do Usuário
```
user_id? → Busca no BD → [Nome Social, Pronome]
    ↓ não
session_id → Modo Anônimo
```

## 3. Busca de Contexto
```
[Supabase Storage] → Baixa arquivos .md → Concatena contexto
[Banco de Dados] → Busca últimas 30 mensagens → Histórico
```

## 4. Montagem do Prompt
```
┌─────────────────────────────────────┐
│ 👤 INFORMAÇÕES DO USUÁRIO           │
│ - Nome: [social_name ou name]       │
│ - Pronome: [ele/ela/elu]            │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ 📚 BASE DE CONHECIMENTO             │
│ - Artigos concatenados (.md files)  │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ 💬 HISTÓRICO DA CONVERSA            │
│ - Últimas 30 mensagens              │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ ❓ PERGUNTA ATUAL                   │
│ - Mensagem do usuário               │
└─────────────────────────────────────┘
```

## 5. Processamento pela IA
```
GPT-4o-mini (temperature=0.7, max_tokens=1000)
    ↓
Gera resposta personalizada e contextual
```

## 6. Salvamento e Resposta
```
Resposta → Salva no BD → Retorna ao usuário
    ↓
[Telegram] Verifica contador → Envia link (se aplicável)
```

---

# 🎨 Features de Personalização

## Sistema de Pronomes

O chatbot identifica e usa corretamente os pronomes:

| Pronome | Exemplo de Uso |
|---------|----------------|
| `ele` | "João, você está bem-vindo aqui!" |
| `ela` | "Maria, você está bem-vinda aqui!" |
| `elu` | "Alex, você está bem-vinde aqui!" |
| `null` | "Olá! Você está bem-vinde aqui!" (neutro) |

## Priorização de Nome Social

```sql
-- Lógica de seleção de nome
preferred_name = social_name OR name

-- Exemplo:
-- name: "João Silva"
-- social_name: "Maria Silva"
-- ✅ Usa: "Maria Silva"
```

---

# 📈 Métricas e Logs

## Logs Disponíveis

### API REST (`main.py`)
```
================================================================================
💬 CHAT ID: 7
👤 NOME DO USUÁRIO: Maria Silva (ela)
📊 HISTÓRICO USADO: 10 mensagens
❓ PERGUNTA DO USUÁRIO: Como funciona a hormonização?
🤖 RESPOSTA: [resposta gerada]
================================================================================
```

### Telegram Bot (`telegram_bot.py`)
```
INFO - Usuário 123456789 iniciou o bot
INFO - Mensagem recebida de 123456789: Como retificar o nome?
INFO - Link da aplicação enviado para usuário 123456789 após 5 mensagens
INFO - Resposta enviada para 123456789
```

---

# 🔐 Segurança e Privacidade

## Boas Práticas Implementadas

- ✅ **Variáveis de ambiente** para credenciais sensíveis
- ✅ **Service Role Key** do Supabase (não exposta ao frontend)
- ✅ **HTTPS recomendado** para produção
- ✅ **Validação de entrada** com Pydantic
- ✅ **Rate limiting** (implementar em produção)
- ✅ **Logs sanitizados** (sem informações pessoais sensíveis)

## Proteção de Dados

- Dados de usuários armazenados com segurança no Supabase
- Histórico de conversas isolado por `chat_id`
- Sessões anônimas suportadas (`session_id`)
- Conformidade com LGPD (Lei Geral de Proteção de Dados)

---

# 🚀 Deploy em Produção

## Opções de Hospedagem

### 1. Railway / Render
- Deploy automático via Git
- Suporte nativo para FastAPI
- Configuração de variáveis de ambiente

### 2. AWS EC2 / Google Cloud
- Maior controle e escalabilidade
- Configuração manual necessária

### 3. Docker (Recomendado)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build e Run:**
```bash
docker build -t chatbot-trans .
docker run -p 8000:8000 --env-file .env chatbot-trans
```

---

# 🛠️ Troubleshooting

## Problemas Comuns

### ❌ Erro: "OPENAI_API_KEY não encontrada"
**Solução:** Verifique se o arquivo `.env` está na raiz do projeto e contém a chave válida.

### ❌ Erro: "ModuleNotFoundError"
**Solução:** Ative o ambiente virtual e reinstale as dependências:
```bash
pip install -r requirements.txt
```

### ❌ Bot do Telegram não responde
**Solução:** 
1. Verifique se o `TELEGRAM_BOT_TOKEN` está correto
2. Certifique-se que o bot está rodando (`python app/telegram_bot.py`)
3. Verifique os logs para identificar erros

### ❌ Erro ao conectar no Supabase
**Solução:**
1. Verifique se `SUPABASE_URL` e `SUPABASE_KEY` estão corretos
2. Confirme que o projeto Supabase está ativo
3. Teste a conexão via Supabase Dashboard

---

# 📚 Documentação Adicional

- [PR_DESCRIPTION.md](./PR_DESCRIPTION.md) - Features de personalização do chat
- [TELEGRAM_PR_DESCRIPTION.md](./TELEGRAM_PR_DESCRIPTION.md) - Sistema de compartilhamento de links
- [FastAPI Docs](https://fastapi.tiangolo.com/) - Documentação oficial do FastAPI
- [python-telegram-bot](https://docs.python-telegram-bot.org/) - Documentação do SDK do Telegram

---

# 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'feat: add amazing feature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

**Padrão de Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação
- `refactor:` - Refatoração de código
- `test:` - Testes
- `chore:` - Manutenção

---

# 📄 Licença

<p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
  <a property="dct:title" rel="cc:attributionURL" href="https://github.com/INTELI-NO-IMPACTO/chatbot">
    Chatbot Inclusivo Trans
  </a> by 
  <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://www.inteli.edu.br/">
    Inteli - Instituto de Tecnologia e Liderança
  </a> is licensed under 
  <a href="https://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">
    CC BY 4.0
    <img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1" alt="">
    <img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1" alt="">
  </a>
</p>

---

# 📞 Contato e Suporte

- **GitHub**: [INTELI-NO-IMPACTO](https://github.com/INTELI-NO-IMPACTO)
- **Email Fernando Machado**: fernando.machado.ismart@gmail.com
- **Email Gabriel Pelinsari**: gabriel.pelinsari.projetos@gmail.com
- **Email João Paulo da Silva**: joaopaulo.silva.ismart@gmail.com
- **Email Matheus Ribeiro**: matheus.ribeiro@sou.inteli.edu.br
---

<p align="center">
  Feito com 💜 pela equipe <strong>INTELI-NO-IMPACTO</strong>
  <br>
  <em>Tecnologia com propósito, acolhimento e respeito</em>
</p>
