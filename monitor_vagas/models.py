from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Vaga:
    """Uma vaga encontrada em alguma fonte."""

    id: str
    titulo: str
    empresa: str
    local: str
    modalidade: str  # "remoto", "híbrido", "presencial" ou ""
    link: str
    publicada_em: str = ""
    fonte: str = ""

    def resumo(self) -> str:
        onde = self.local or self.modalidade or "local não informado"
        if self.modalidade and self.local:
            onde = f"{self.local} ({self.modalidade})"
        return f"{self.titulo} · {self.empresa} · {onde}\n{self.link}"
