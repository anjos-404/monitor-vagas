"""Uso: python -m monitor_vagas [--config config.toml] [--a-cada 60]"""
from __future__ import annotations

import argparse
import os
import sys
import time
import tomllib

from . import alertas, fontes
from .armazenamento import Historico
from .filtros import Filtro


def carregar_config(caminho: str) -> dict:
    with open(caminho, "rb") as f:
        return tomllib.load(f)


def coletar(config: dict) -> list:
    vagas = []
    for termo in config.get("gupy", {}).get("termos", []):
        try:
            vagas += fontes.buscar_gupy(termo)
        except Exception as erro:  # uma fonte fora do ar não derruba as outras
            print(f"[aviso] Gupy '{termo}': {erro}", file=sys.stderr)
    for feed in config.get("rss", []):
        try:
            vagas += fontes.buscar_rss(feed["url"], feed.get("nome", "RSS"))
        except Exception as erro:
            print(f"[aviso] RSS {feed.get('nome')}: {erro}", file=sys.stderr)
    return vagas


def rodar_uma_vez(config: dict, historico: Historico) -> list:
    filtro = Filtro(**config.get("filtro", {}))
    encontradas = [v for v in coletar(config) if filtro.aceita(v)]
    novas = historico.novas(encontradas)
    if novas:
        alertas.avisar_terminal(novas)
        token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
        if token and chat:
            alertas.avisar_telegram(novas, token, chat)
    else:
        print("Nenhuma vaga nova.")
    return novas


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Monitora vagas e avisa das novas.")
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--banco", default="vagas.db")
    parser.add_argument("--a-cada", type=int, default=0, help="repete a cada N minutos")
    args = parser.parse_args(argv)

    config = carregar_config(args.config)
    historico = Historico(args.banco)
    try:
        while True:
            rodar_uma_vez(config, historico)
            if not args.a_cada:
                break
            time.sleep(args.a_cada * 60)
    finally:
        historico.fechar()


if __name__ == "__main__":
    main()
