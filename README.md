# ChatIA v1.0

**Interface Unificada de Chat Multi-Provider com Streaming em Tempo Real.**

O ChatIA é uma interface conversacional que permite alternar entre o **Google Gemini** (nuvem) e **modelos locais via Ollama** sem trocar de ferramenta. Construído sobre o princípio de separação absoluta entre UI e lógica de negócio, com 4 camadas de proteção de segredos.

---

## 🚀 Engenharia de Destaque (Os 4 Pilares)

### 🔀 Multi-Provider Transparente
O usuário escolhe o provider na sidebar e conversa normalmente. A troca entre Gemini (nuvem) e Ollama (local) é instantânea, sem reconfiguração. O histórico é mantido por sessão independente do provider.

### ⚡ Streaming Token a Token (SSE)
As respostas aparecem em tempo real conforme são geradas, não após o processamento completo. Implementado via `generate_content_stream` (Gemini) e `iter_lines` (Ollama), renderizado com `st.write_stream`.

### 🏗️ Arquitetura Limpa (Core vs UI)
Separação cirúrgica: `core/` contém Python puro testável sem Streamlit. `app.py` só faz chamadas `st.*`. Os clientes são stateless — recebem histórico como parâmetro, sem efeitos colaterais.

### 🔐 Defesa em Profundidade (4 Camadas de Segurança)
1. **`.gitignore`** — Arquivos de segredo nunca entram no repositório.
2. **Templates `.example`** — Documentam o que preencher sem expor chaves reais.
3. **Pre-commit hook** — Detecta padrões de API keys (`AIza...`, `sk-...`, `ghp_...`) e bloqueia o commit.
4. **`config/settings.py`** — Única via de acesso à chave no código. Busca em `st.secrets` → `os.environ` → erro claro.

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Motivo |
|--------|-----------|--------|
| **UI** | Streamlit 1.55+ | `st.chat_message`, `st.write_stream`, `st.cache_resource` |
| **IA Nuvem** | Google Gemini via `google-genai` ≥1.0 | SDK oficial atualizado, streaming nativo |
| **IA Local** | Ollama (localhost:11434) | Modelos open-source rodando na máquina |
| **HTTP** | Requests 2.33+ | Chamadas REST ao servidor Ollama |
| **Config** | python-dotenv 1.2+ | Carregar variáveis do `.env` em scripts standalone |

---

## 📐 Arquitetura

```
ChatIA/
├── app.py                         # Entry point — só chamadas st.*
├── core/
│   ├── __init__.py
│   ├── gemini_client.py           # GeminiClient: SDK google-genai + retry + streaming
│   └── ollama_client.py           # OllamaClient: REST API + streaming + 3 exceções
├── config/
│   ├── __init__.py
│   └── settings.py                # get_gemini_api_key() — fonte única de verdade
├── .githooks/
│   └── pre-commit                 # Bloqueia commits com API keys vazadas
├── .streamlit/
│   ├── secrets.toml               # 🔒 Chaves reais (gitignored)
│   └── secrets.toml.example       # 📋 Template público
├── .env                           # 🔒 Alternativa local (gitignored)
├── .env.example                   # 📋 Template público
├── .gitignore                     # Proteção de arquivos sensíveis
├── check.py                       # Script diagnóstico: lista modelos disponíveis
├── requirements.txt               # Dependências com versões mínimas
├── BLUEPRINT.md                   # Mapa de estado do projeto (vivo)
└── README.md                      # Este arquivo
```

**Fluxo de dados:**
```
Usuário digita → app.py coleta prompt + histórico
    → provider == "gemini" → GeminiClient.send_message_stream() → API Google
    → provider == "ollama" → OllamaClient.send_message_stream() → localhost:11434
         ↓
    generator de chunks → st.write_stream() → texto aparece token a token
```

---

## 💻 Como Executar

### Pré-requisitos
- Python 3.10+
- Conta no Google AI Studio (para Gemini) e/ou Ollama instalado (para modelos locais)

### 1. Clone o repositório

```bash
git clone git clone https://github.com/dsantos-science/ChatIA.git
cd ChatIA
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as chaves

```bash
# Copie os templates
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edite com sua chave real do Gemini
# Pegue em: https://aistudio.google.com → Get API key
```

### 4. (Opcional) Instale o Ollama

```bash
# Baixe em https://ollama.com
# Depois instale um modelo:
ollama pull tinyllama
```

### 5. Rode

```bash
streamlit run app.py
```

---

## 🗺️ Roadmap

| Prioridade | Feature | Status |
|:---:|---------|:---:|
| 1 | Streaming de respostas | ✅ Implementado |
| 2 | Seleção dinâmica de modelo Ollama | ⬜ Planejado |
| 3 | System prompt configurável | ⬜ Planejado |
| 4 | Persistência de histórico (JSON/SQLite) | ⬜ Planejado |
| 5 | Testes unitários dos clientes | ⬜ Planejado |

---

## 📄 Licença

MIT

---

> **Nota de segurança:** Nunca commite arquivos `.env` ou `secrets.toml` com chaves reais. O pre-commit hook bloqueia padrões conhecidos de API keys, mas a primeira linha de defesa é sempre o `.gitignore`.