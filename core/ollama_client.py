import json
from collections.abc import Iterator

import requests


class OllamaClient:
    """Encapsula a comunicação com a API local do Ollama."""

    def __init__(self, model_name: str = "tinyllama", base_url: str = "http://localhost:11434") -> None:
        """Args:
            model_name: Modelo Ollama a usar.
            base_url: Endereço base do servidor Ollama.
        """
        self._model_name = model_name
        self._url = f"{base_url}/api/chat"

    def send_message(self, prompt: str, history: list[dict]) -> str:
        """Envia mensagem ao Ollama com histórico de conversa.

        Args:
            prompt: Mensagem atual do usuário.
            history: Lista de mensagens anteriores no formato
                     [{"role": "user"|"assistant", "content": "..."}].

        Returns:
            Texto da resposta do modelo, ou mensagem de erro.
        """
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in history
        ]
        messages.append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                self._url,
                json={"model": self._model_name, "messages": messages, "stream": False},
                timeout=90,
            )
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "Resposta vazia do modelo.")
        except requests.exceptions.ConnectionError:
            return "❌ Ollama não disponível: verifique se o serviço está rodando localmente."
        except requests.exceptions.Timeout:
            return "❌ Ollama demorou demais para responder (timeout de 90s)."
        except Exception as e:
            return f"❌ Erro inesperado no Ollama: {e}"

    def send_message_stream(self, prompt: str, history: list[dict]) -> Iterator[str]:
        """Envia mensagem ao Ollama e retorna um generator de chunks de texto.

        Args:
            prompt: Mensagem atual do usuário.
            history: Lista de mensagens anteriores no formato
                     [{"role": "user"|"assistant", "content": "..."}].

        Yields:
            Fragmentos de texto conforme chegam do servidor Ollama.
        """
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                self._url,
                json={"model": self._model_name, "messages": messages, "stream": True},
                stream=True,
                timeout=90,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
        except requests.exceptions.ConnectionError:
            yield "❌ Ollama não disponível: verifique se o serviço está rodando localmente."
        except requests.exceptions.Timeout:
            yield "❌ Ollama demorou demais para responder (timeout de 90s)."
        except Exception as e:
            yield f"❌ Erro inesperado no Ollama: {e}"
