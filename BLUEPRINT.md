# 🏗️ BLUEPRINT DO PROJETO
> Atualizado em: 2026-04-25 (pós-deploy: debug removido, secrets configurados no Streamlit Cloud)

## 1. Visão Geral
- **Nome**: ChatIA
- **Objetivo**: Interface de chat unificada que permite conversar com o Google Gemini (nuvem) ou com modelos locais via Ollama, sem trocar de ferramenta.
- **Stack**: Python 3.12 | Streamlit 1.55 | google-genai 1.73.1 | requests 2.33

---

## 2. Arquitetura Atual

```
ChatIA/
├── app.py                         # Entry point — só chamadas st.*; sem lógica de negócio
├── core/
│   ├── __init__.py
│   ├── gemini_client.py           # GeminiClient: configura e chama a API do Gemini
│   └── ollama_client.py           # OllamaClient: chama o servidor Ollama local
├── config/
│   ├── __init__.py
│   └── settings.py                # get_gemini_api_key() — fonte única de configuração
├── .streamlit/
│   ├── secrets.toml               # ← sua chave real (gitignored)
│   └── secrets.toml.example       # template público (commitado)
├── .githooks/
│   └── pre-commit                 # Bloqueia commits com API keys expostas
├── .gitignore                     # Protege .env e secrets.toml
├── .env                           # Alternativa local para GEMINI_API_KEY (gitignored)
├── .env.example                   # template público (commitado)
├── check.py                       # Script utilitário: lista modelos disponíveis
├── README.md                      # Setup e configuração
└── requirements.txt               # Dependências com versões mínimas
```

**Fluxo de dados:**
```
Usuário digita → app.py coleta prompt + histórico
    → provider == "gemini" → GeminiClient.send_message_stream()  → API Google (SSE)
    → provider == "ollama" → OllamaClient.send_message_stream()  → localhost:11434 (stream)
         ↓
    Iterator[str] → st.write_stream() → tela (token a token)
```

**Decisão de cache:** `@st.cache_resource` em `get_gemini_client()` e `get_ollama_client()` garante que os clientes são instanciados uma única vez por sessão do servidor, evitando reconfigurar a API a cada mensagem.

---

## 3. Status dos Módulos

| Módulo | Arquivo | Status | Observações |
|--------|---------|--------|-------------|
| UI / Chat | `app.py` | ✅ Pronto | Sidebar, histórico, streaming, seletor de modelo, erro 429, usa `is_gemini_configured()` |
| Configuração | `config/settings.py` | ✅ Pronto | `get_gemini_api_key()` — busca em secrets e env, valida placeholders |
| Cliente Gemini | `core/gemini_client.py` | ✅ Pronto | SDK google-genai, streaming, retry 429, gemini-2.5-flash padrão |
| Cliente Ollama | `core/ollama_client.py` | ✅ Pronto | Histórico completo, streaming implementado |
| Diagnóstico de modelos | `check.py` | ✅ Pronto | Script standalone, usa .env |

Legenda: ✅ Pronto | 🔨 Em progresso | ⬜ Não iniciado | 🐛 Com bugs

---

## 4. Débitos Técnicos

- [x] **Streaming de resposta**: `send_message_stream()` em ambos os clientes; `app.py` usa `st.write_stream()` — texto aparece token a token.
- [x] **Seleção de modelo Gemini**: `st.selectbox` na sidebar com `gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-1.5-flash`; cada modelo tem cliente cacheado separado via `@st.cache_resource(model_name)`.
- [x] **Deploy no Streamlit Cloud**: app publicado em produção; secrets configurados via painel web do Streamlit Cloud — chaves nunca commitadas.
- [ ] **Seleção de modelo Ollama**: o modelo `tinyllama` está hardcoded em `OllamaClient`. Expor um `st.selectbox` na sidebar que lista os modelos instalados via `GET /api/tags`.
- [ ] **System prompt configurável**: sem campo para instrução de sistema (persona, idioma, restrições). Adicionar `st.text_area` na sidebar que injeta como primeira mensagem com `role="system"` no Ollama e como instrução no Gemini.
- [ ] **Persistência de histórico**: o histórico vive apenas na sessão Streamlit. Considerar salvar em JSON local ou SQLite para retomar conversas.
- [ ] **Testes unitários**: `GeminiClient` e `OllamaClient` são Python puro e testáveis sem Streamlit — ainda sem cobertura de testes.

---

## 5. Próximos Passos (priorizado)

1. ~~**Streaming de respostas**~~ — ✅ Concluído.
2. ~~**Seleção de modelo Gemini**~~ — ✅ Concluído (Gemini; Ollama ainda pendente).
3. **Seleção dinâmica de modelo Ollama** — listar modelos instalados via `GET /api/tags`.
3. **System prompt configurável** — permite personalizar comportamento sem alterar código.
4. **Persistência de histórico** — necessário para uso produtivo além de testes rápidos.
5. **Testes unitários** — cobertura mínima de `send_message_stream()` em ambos os clientes.

---

## 6. Dependências Críticas

| Lib | Versão mínima | Motivo |
|-----|---------------|--------|
| `streamlit` | 1.55.0 | Framework de UI; `st.cache_resource`, `st.chat_message` |
| `google-genai` | 1.0.0 | SDK oficial do Gemini (substituto do descontinuado `google-generativeai`); `genai.Client`, `generate_content_stream` |
| `requests` | 2.33.0 | Chamadas HTTP ao servidor Ollama local |
| `python-dotenv` | 1.2.2 | Carregar `GEMINI_API_KEY` do `.env` no `check.py` |

---

## 7. Decisões de Design

**Separação `core/` vs `app.py`**
Lógica de negócio (chamadas API, formatação de histórico) foi extraída para `core/` para que seja testável sem inicializar o Streamlit. `app.py` só faz chamadas `st.*`.

**`@st.cache_resource` para clientes de API**
Garante uma única instância de `GeminiClient` / `OllamaClient` por processo do servidor. Sem isso, `configure(api_key=...)` seria chamado a cada mensagem enviada.

**Histórico passado como parâmetro, não como estado global**
`send_message(prompt, history)` recebe o histórico explicitamente. Facilita testes e deixa os clientes sem efeito colateral de estado.

**`config/settings.get_gemini_api_key()` como fonte única de configuração**
Centraliza a leitura da API key: tenta `st.secrets` primeiro (Streamlit), depois `os.environ` (scripts/CI). Valida placeholders (`"cole_sua_chave_aqui"`). Levanta `ValueError` com mensagem clara. Nenhum módulo acessa `st.secrets` ou `os.environ` diretamente — tudo passa por `settings.py`.

**Segurança em 4 camadas (defesa em profundidade)**
- **Camada 1 — `.gitignore`**: exclui `.env`, `.env.*` e `.streamlit/secrets.toml` do tracking git. Proteção passiva — se uma camada falhar, a próxima segura.
- **Camada 2 — templates `.example`**: `.env.example` e `secrets.toml.example` vão para o repositório com valores placeholder, documentando o que o novo colaborador precisa preencher sem expor chaves reais.
- **Camada 3 — pre-commit hook** em `.githooks/pre-commit`: regex detecta padrões de API keys reais (`AIza...`, `sk-...`, `ghp_...`) em todos os arquivos staged e bloqueia o commit antes que o segredo entre no histórico. Ativado via `git config core.hooksPath .githooks`.
- **Camada 4 — `config/settings.py`**: `get_gemini_api_key()` é a única forma de obter a chave no código. Qualquer módulo que tente hardcodar a chave ficaria redundante — a chave já não é necessária em nenhum outro ponto.

**Deploy no Streamlit Cloud com secrets via painel web**
A chave `GEMINI_API_KEY` é configurada diretamente no painel *Settings → Secrets* do Streamlit Cloud, nunca commitada no repositório. O `config/settings.py` já tenta `st.secrets` antes de `os.environ`, portanto zero mudança de código foi necessária para o deploy. Chaves nunca commitadas — segurança garantida end-to-end.

**Exceções específicas no Ollama**
`ConnectionError`, `Timeout` e `Exception` são capturados separadamente para dar mensagens úteis ao usuário em vez de um genérico "algo deu errado".

**`send_message()` mantido junto ao `send_message_stream()`**
O método síncrono original foi preservado. Motivo: `st.write_stream` exige um generator — não é intercambiável com `str`. Manter os dois métodos permite reusar os clientes em contextos sem Streamlit (scripts, testes, CLI).

**Erros de streaming fazem `yield` em vez de `raise`**
Nos generators de stream, exceções são capturadas e entregues como strings de erro (`yield "❌ ..."`). Isso mantém a consistência com `st.write_stream`, que espera um Iterator[str] — uma exceção não capturada quebraria a renderização parcial já exibida na tela.

**Retry com backoff para erro 429 (ResourceExhausted)**
`GeminiClient._call_with_retry()` tenta até 3 vezes com o delay sugerido pela própria API (`retry_delay.seconds` extraído da mensagem de erro via regex, cap de 60s). Fallback de 30s se o campo não estiver presente. O retry protege apenas a chamada inicial — erros mid-stream (raros) viram `yield` de erro. Na 3ª falha, `ResourceExhausted` é relançado para `app.py`, que exibe `st.error()` + `st.info()` com diagnóstico claro (billing, free tier, AI Studio vs GCP key). Mensagens de erro não são salvas no histórico de conversa (`response = None` → append ignorado).

**`@st.cache_resource` parametrizado por `model_name`**
`get_gemini_client(model_name)` gera um cliente cacheado por modelo — trocar de modelo na sidebar não descarta o cliente do modelo anterior. `st.session_state.get("gemini_model", GEMINI_MODELS[0])` garante fallback seguro quando o provider é Ollama (o selectbox não renderiza, a key pode não existir).

**`_build_history()` extraído como método privado**
Eliminada duplicação da conversão de histórico entre `send_message` e `send_message_stream`. Único ponto de mudança se o formato Gemini mudar.

**Migração de `google-generativeai` → `google-genai` (SDK unificado)**
O SDK antigo foi descontinuado pelo Google. O novo SDK (`google-genai`) unifica Gemini API e Vertex AI num único cliente. Mudanças de interface: `configure(api_key)` + `GenerativeModel` + `start_chat` → `genai.Client(api_key)` + `client.models.generate_content()` / `generate_content_stream()`. O histórico agora é passado diretamente no campo `contents` de cada chamada (sem sessão de chat stateful). Exceção de quota mudou de `google.api_core.exceptions.ResourceExhausted` → `google.genai.errors.ClientError` (verificar `e.code == 429`). Modelo padrão atualizado para `gemini-2.5-flash` (confirmado disponível via `client.models.list()`). `check.py` corrigido: chave hardcoded removida, volta a ler do `.env`.
