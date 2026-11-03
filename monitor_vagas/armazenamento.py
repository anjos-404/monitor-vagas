"""Guarda as vagas já vistas num SQLite, para só avisar das novas."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Vaga


class Historico:
    def __init__(self, caminho: str | Path = "vagas.db"):
        self.conn = sqlite3.connect(str(caminho))
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS vistas (
                   id TEXT PRIMARY KEY,
                   titulo TEXT, empresa TEXT, link TEXT,
                   vista_em TEXT DEFAULT CURRENT_TIMESTAMP
               )"""
        )

    def novas(self, vagas: list[Vaga]) -> list[Vaga]:
        """Devolve só as vagas que ainda não estavam no histórico e as registra."""
        resultado = []
        for vaga in vagas:
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO vistas (id, titulo, empresa, link) VALUES (?, ?, ?, ?)",
                (vaga.id, vaga.titulo, vaga.empresa, vaga.link),
            )
            if cur.rowcount:
                resultado.append(vaga)
        self.conn.commit()
        return resultado

    def total(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM vistas").fetchone()[0]

    def fechar(self) -> None:
        self.conn.close()
