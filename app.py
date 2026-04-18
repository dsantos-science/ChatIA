import streamlit as st
import requests
import json

# Configuração da Página - Foco em Eficiência e Sobriedade
st.set_page_config(
    page_title="OdontoFlow AI - Local (TinyLlama)",
    page_icon="⚡",
    layout="centered"
)

# Estilização para um ambiente de desenvolvimento limpo
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

def gerar_resposta(prompt):
    """
    Comunicação direta com o Ollama utilizando o modelo TinyLlama.
    Consumo de memória estimado: ~800MB a 1.1GB.
    """
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "tinyllama",
        "prompt": f"Instrução: Responda de forma concisa e técnica.\nUsuário: {prompt}",
        "stream": False
    }
    
    try:
        # Timeout estendido para garantir que o modelo carregue na memória
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.ConnectionError:
        return "❌ Erro: O serviço Ollama não foi encontrado. Inicie o Ollama no Windows."
    except Exception as e:
        return f"❌ Erro no processamento: {str(e)}"

# --- INTERFACE ---
st.title("🤖 Assistente Local (Low-Memory)")
st.caption("Modelo: TinyLlama | Status: Ativo (Zero Cota API)")

# Inicialização do Histórico de Mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibição do Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Campo de entrada de texto
if prompt := st.chat_input("Como posso ajudar com o seu código ou projeto?"):
    
    # Adiciona pergunta do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Processamento da resposta
    with st.chat_message("assistant"):
        with st.spinner("Pensando com TinyLlama..."):
            resposta = gerar_resposta(prompt)
            st.markdown(resposta)
    
    # Salva no histórico
    st.session_state.messages.append({"role": "assistant", "content": resposta})

# Barra lateral com utilitários
with st.sidebar:
    st.header("Configurações")
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.markdown("""
    **Diretriz de Execução:**
    - Modelo: TinyLlama (1.1B)
    - Hardware: Otimizado para 2.5GB RAM
    - Objetivo: Eficiência Radical
    """)