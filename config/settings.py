import os
from typing import Optional

_PLACEHOLDERS = {"cole_sua_chave_aqui", "sua_chave_aqui", ""}


def _from_streamlit_secrets() -> Optional[str]:
    """Tenta ler GEMINI_API_KEY dos st.secrets do Streamlit.

    Returns:
        Chave encontrada, ou None se indisponível ou placeholder.
    """
    try:
        import streamlit as st
        value = st.secrets.get("GEMINI_API_KEY", "")
        return value if value not in _PLACEHOLDERS else None
    except Exception:
        return None


def _from_env() -> Optional[str]:
    """Tenta ler GEMINI_API_KEY das variáveis de ambiente.

    Returns:
        Chave encontrada, ou None se ausente ou placeholder.
    """
    value = os.environ.get("GEMINI_API_KEY", "")
    return value if value not in _PLACEHOLDERS else None


def get_gemini_api_key() -> str:
    """Retorna a GEMINI_API_KEY de st.secrets ou variáveis de ambiente.

    Ordem de busca:
        1. ``st.secrets["GEMINI_API_KEY"]`` (Streamlit / secrets.toml)
        2. ``os.environ["GEMINI_API_KEY"]`` (variável de ambiente / .env)

    Returns:
        Chave da API Gemini pronta para uso.

    Raises:
        ValueError: Se a chave não for encontrada em nenhuma fonte,
                    ou se o valor for um placeholder.
    """
    key = _from_streamlit_secrets() or _from_env()
    if key:
        return key
    raise ValueError(
        "GEMINI_API_KEY não encontrada ou inválida.\n"
        "Configure em:\n"
        "  • Streamlit: .streamlit/secrets.toml  (copie de secrets.toml.example)\n"
        "  • Scripts:   .env                      (copie de .env.example)"
    )


def is_gemini_configured() -> bool:
    """Retorna True se uma GEMINI_API_KEY válida estiver configurada.

    Returns:
        True se a chave estiver disponível e não for um placeholder.
    """
    try:
        get_gemini_api_key()
        return True
    except ValueError:
        return False
