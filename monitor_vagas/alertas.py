"""Formas de avisar sobre vagas novas: terminal e Telegram."""
from __future__ import annotations

import json
import urllib.request

from .models import Vaga


def montar_mensagem(vagas: list[Vaga]) -> str:
    linhas = [f"{len(vagas)} vaga(s) nova(s):", ""]
    for i, vaga in enumerate(vagas, 1):
        linhas.append(f"{i}. {vaga.resumo()}")
    return "\n".join(linhas)


def avisar_terminal(vagas: list[Vaga]) -> None:
    print(montar_mensagem(vagas))


def avisar_telegram(vagas: list[Vaga], token: str, chat_id: str) -> None:
    """Manda a lista por um bot do Telegram (crie o bot com o @BotFather)."""
    corpo = json.dumps(
        {"chat_id": chat_id, "text": montar_mensagem(vagas), "disable_web_page_preview": True}
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=corpo,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20):
        pass
