"""Decide se uma vaga interessa, com base nas palavras-chave da configuração."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .models import Vaga


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para comparar 'Júnior' com 'junior'."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.lower()


def _contem(texto: str, termo: str) -> bool:
    """Procura o termo como palavra inteira (evita achar 'pl' dentro de 'aplicação')."""
    termo = normalizar(termo)
    padrao = r"(?<![a-z0-9])" + re.escape(termo) + r"(?![a-z0-9])"
    return re.search(padrao, texto) is not None


@dataclass
class Filtro:
    incluir: list[str] = field(default_factory=list)   # o título precisa ter pelo menos um
    excluir: list[str] = field(default_factory=list)   # se o título tiver algum, descarta
    modalidades: list[str] = field(default_factory=list)  # vazio = qualquer uma
    cidades: list[str] = field(default_factory=list)   # aceitas além das vagas remotas

    def aceita(self, vaga: Vaga) -> bool:
        titulo = normalizar(vaga.titulo)
        if self.incluir and not any(_contem(titulo, t) for t in self.incluir):
            return False
        if any(_contem(titulo, t) for t in self.excluir):
            return False
        if vaga.modalidade == "remoto":
            return not self.modalidades or "remoto" in self.modalidades
        if self.modalidades and vaga.modalidade not in self.modalidades:
            return False
        if self.cidades:
            local = normalizar(vaga.local)
            return any(normalizar(c) in local for c in self.cidades)
        return True
