import re
import time
from collections.abc import Callable, Iterator
from typing import Any

from google import genai
from google.genai.errors import ClientError

_MAX_ATTEMPTS = 3
_MAX_RETRY_DELAY_SECONDS = 60


def _extract_retry_delay(error: ClientError) -> int:
    """Extrai segundos de espera sugeridos pelo erro 429.

    Args:
        error: ClientError retornado pela API Gemini.

    Returns:
        Segundos para aguardar, limitados a _MAX_RETRY_DELAY_SECONDS.
        Retorna 30 como fallback se o campo não estiver presente.
    """
    match = re.search(r"retry_delay\s*\{?\s*seconds:\s*(\d+)", str(error))
    if match:
        return min(int(match.group(1)), _MAX_RETRY_DELAY_SECONDS)
    return 30


class GeminiClient:
    """Encapsula a comunicação com a API do Google Gemini via SDK google-genai."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        """Args:
            api_key: Chave da API Gemini.
            model_name: Nome do modelo a usar.
        """
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def _build_contents(self, history: list[dict], prompt: str) -> list[dict]:
        """Formata histórico + prompt atual no formato esperado pelo SDK.

        Args:
            history: Mensagens anteriores com role "user" ou "assistant".
            prompt: Mensagem atual do usuário.

        Returns:
            Lista de dicts no formato [{"role": ..., "parts": [{"text": ...}]}].
        """
        contents = [
            {"role": "user" if m["role"] == "user" else "model",
             "parts": [{"text": m["content"]}]}
            for m in history
        ]
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        return contents

    def _call_with_retry(self, fn: Callable[[], Any]) -> Any:
        """Executa fn com retry automático em caso de erro 429 (quota excedida).

        Args:
            fn: Callable sem argumentos que executa a chamada à API.

        Returns:
            Resultado de fn em caso de sucesso.

        Raises:
            ClientError: Se todos os _MAX_ATTEMPTS falharem ou o erro não for 429.
        """
        for attempt in range(_MAX_ATTEMPTS):
            try:
                return fn()
            except ClientError as e:
                if e.code == 429 and attempt < _MAX_ATTEMPTS - 1:
                    time.sleep(_extract_retry_delay(e))
                else:
                    raise

    def send_message(self, prompt: str, history: list[dict]) -> str:
        """Envia mensagem ao Gemini com histórico de conversa.

        Args:
            prompt: Mensagem atual do usuário.
            history: Lista de mensagens no formato
                     [{"role": "user"|"assistant", "content": "..."}].

        Returns:
            Texto da resposta do modelo.

        Raises:
            ClientError: Se a cota for excedida após todas as tentativas.
        """
        contents = self._build_contents(history, prompt)
        response = self._call_with_retry(
            lambda: self._client.models.generate_content(
                model=self._model_name, contents=contents
            )
        )
        return response.text

    def send_message_stream(self, prompt: str, history: list[dict]) -> Iterator[str]:
        """Envia mensagem ao Gemini e retorna um generator de chunks de texto.

        Retry com backoff protege a chamada inicial — só reexecuta se nenhum
        chunk foi entregue ainda, evitando conteúdo duplicado em retentativas.

        Args:
            prompt: Mensagem atual do usuário.
            history: Lista de mensagens no formato
                     [{"role": "user"|"assistant", "content": "..."}].

        Yields:
            Fragmentos de texto conforme chegam da API.

        Raises:
            ClientError: Se quota 429 for excedida após todas as tentativas
                         antes de qualquer chunk ser entregue.
        """
        contents = self._build_contents(history, prompt)

        for attempt in range(_MAX_ATTEMPTS):
            yielded_anything = False
            try:
                for chunk in self._client.models.generate_content_stream(
                    model=self._model_name, contents=contents
                ):
                    if chunk.text:
                        yielded_anything = True
                        yield chunk.text
                return
            except ClientError as e:
                if e.code == 429 and not yielded_anything and attempt < _MAX_ATTEMPTS - 1:
                    time.sleep(_extract_retry_delay(e))
                elif e.code == 429 and not yielded_anything:
                    raise
                else:
                    yield f"❌ Erro Gemini: {e.message}"
                    return
            except Exception as e:
                yield f"❌ Erro Gemini inesperado: {e}"
                return
