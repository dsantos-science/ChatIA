import streamlit as st
from google.generativeai import configure, GenerativeModel
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="ChatIA - Gemini & Ollama",
    page_icon="🤖",
    layout="centered"
)

# Estética Sóbria (Modo Dark)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stChatMessage"] { border: 1px solid #333; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORES DE RESPOSTA ---

def get_gemini_response(prompt, history):
    try:
        configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = GenerativeModel("gemini-2.0-flash")
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"❌ Erro Gemini: {str(e)}"

def get_ollama_response(prompt, model_name="tinyllama"):
    try:
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        response = requests.post(url, json=payload, timeout=90)
        return response.json().get("message", {}).get("content", "Erro na resposta")
    except Exception as e:
        return f"❌ Ollama não disponível: Verifique se o serviço está rodando localmente."

# --- GERENCIAMENTO DE ESTADO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Busca a chave nos Secrets do Streamlit
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    gemini_available = True if api_key else False
    
    provider = st.radio(
        "Escolha o Provider:",
        ["ollama", "gemini"],
        index=1 if gemini_available else 0
    )
    st.session_state.provider = provider
    
    st.divider()
    
    if provider == "gemini":
        if gemini_available:
            st.success("✅ Gemini configurado")
        else:
            st.error("⚠️ Chave Gemini não encontrada!")
    else:
        st.info("🤖 Usando Hardware Local")
    
    st.divider()
    
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACE PRINCIPAL ---
st.title("🤖 Chat IA")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("🤔 Processando..."):
            try:
                if st.session_state.provider == "gemini":
                    history_gemini = []
                    for m in st.session_state.messages[:-1]:
                        role = "user" if m["role"] == "user" else "model"
                        history_gemini.append({"role": role, "parts": [m["content"]]})
                    
                    response = get_gemini_response(prompt, history_gemini)
                else:
                    response = get_ollama_response(prompt)
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"Erro crítico: {str(e)}")