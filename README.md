# ChatIA — Gemini & Ollama

Interface de chat unificada para conversar com Google Gemini (nuvem) ou modelos locais via Ollama.

## Pré-requisitos

- Python 3.12+
- [Ollama](https://ollama.ai) instalado localmente (opcional, para o provider local)

## Configuração

### 1. Clone e instale dependências

```bash
git clone <url-do-repositorio>
cd ChatIA
pip install -r requirements.txt
```

### 2. Configure sua API Key do Gemini

Obtenha sua chave em: **https://aistudio.google.com/app/apikey**

**Para rodar via Streamlit** (recomendado):

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite secrets.toml e substitua "cole_sua_chave_aqui" pela sua chave real
```

**Para scripts standalone** (como `check.py`):

```bash
cp .env.example .env
# Edite .env e substitua "cole_sua_chave_aqui" pela sua chave real
```

> ⚠️ **Nunca commite** `.env` ou `secrets.toml` — ambos estão no `.gitignore`.

### 3. Rode o app

```bash
streamlit run app.py
```

## Providers disponíveis

| Provider | Requisito | Modelos |
|----------|-----------|---------|
| Gemini | API Key do Google | gemini-2.5-flash, gemini-2.0-flash, gemini-2.0-flash-lite |
| Ollama | Servidor local rodando | tinyllama (padrão) |

## Utilitários

```bash
# Listar modelos disponíveis na sua conta Gemini
python check.py
```

## Estrutura

```
ChatIA/
├── app.py                  # Interface Streamlit
├── core/
│   ├── gemini_client.py    # Cliente Gemini (streaming, retry)
│   └── ollama_client.py    # Cliente Ollama (streaming)
├── config/
│   └── settings.py         # Carregamento seguro de API keys
├── .streamlit/
│   └── secrets.toml        # ← sua chave aqui (gitignored)
└── .env                    # ← alternativa para scripts (gitignored)
```
