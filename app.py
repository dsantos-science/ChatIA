import streamlit as st
from google.genai.errors import ClientError as GeminiError

from config.settings import get_gemini_api_key, is_gemini_configured
from core.gemini_client import GeminiClient
from core.ollama_client import OllamaClient

st.set_page_config(page_title="ChatIA - Gemini & Ollama", page_icon="🤖", layout="centered")

st.write("DEBUG secrets:", list(st.secrets.keys()))

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stChatMessage"] { border: 1px solid #333; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]


@st.cache_resource
def get_gemini_client(model_name: str) -> GeminiClient:
    return GeminiClient(api_key=get_gemini_api_key(), model_name=model_name)


@st.cache_resource
def get_ollama_client() -> OllamaClient:
    return OllamaClient()


# --- ESTADO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")

    gemini_available = is_gemini_configured()

    provider = st.radio(
        "Escolha o Provider:",
        ["ollama", "gemini"],
        index=1 if gemini_available else 0,
    )
    st.session_state.provider = provider

    st.divider()

    if provider == "gemini":
        if gemini_available:
            selected_model = st.selectbox("Modelo Gemini:", GEMINI_MODELS, key="gemini_model")
            st.success(f"✅ Gemini configurado ({selected_model})")
        else:
            st.error("⚠️ Chave Gemini não encontrada em .streamlit/secrets.toml")
    else:
        st.info("🤖 Usando hardware local via Ollama")

    st.divider()

    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# --- CHAT ---
st.title("🤖 Chat IA")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    history = st.session_state.messages.copy()
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            if st.session_state.provider == "gemini":
                gemini_model = st.session_state.get("gemini_model", GEMINI_MODELS[0])
                response = st.write_stream(
                    get_gemini_client(gemini_model).send_message_stream(prompt, history)
                )
            else:
                response = st.write_stream(get_ollama_client().send_message_stream(prompt, history))
        except GeminiError as e:
            if e.code == 429:
                st.error("⚠️ Limite da API Gemini atingido.")
                st.info(
                    "**Possíveis causas:**\n"
                    "1. Sua API key está no tier gratuito — ative o billing no Google Cloud Console.\n"
                    "2. A key foi gerada no AI Studio em vez do GCP Console.\n"
                    "3. Cota diária do free tier esgotada — tente novamente em 24h ou ative billing.\n\n"
                    "**Para verificar:** acesse https://console.cloud.google.com/billing"
                )
            else:
                st.error(f"❌ Erro na API Gemini (HTTP {e.code}): {e.message}")
            response = None

    if response is not None:
        st.session_state.messages.append({"role": "assistant", "content": response})
