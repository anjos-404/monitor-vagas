"""Fontes de vagas. Cada fonte transforma a resposta de um site em objetos Vaga."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Callable

from .models import Vaga

USER_AGENT = "monitor-vagas/1.0 (+https://github.com/anjos-404/monitor-vagas)"
MODALIDADES_GUPY = {"remote": "remoto", "hybrid": "híbrido", "on-site": "presencial"}

Baixar = Callable[[str], str] | None


def baixar(url: str, timeout: float = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def ler_gupy(dados: dict) -> list[Vaga]:
    """Converte a resposta do portal de vagas da Gupy em vagas."""
    vagas = []
    for item in dados.get("data", []):
        cidade = ", ".join(p for p in (item.get("city"), item.get("state")) if p)
        vagas.append(
            Vaga(
                id=f"gupy-{item['id']}",
                titulo=item.get("name", "").strip(),
                empresa=item.get("careerPageName", "").strip(),
                local=cidade,
                modalidade=MODALIDADES_GUPY.get(item.get("workplaceType", ""), ""),
                link=item.get("jobUrl", ""),
                publicada_em=item.get("publishedDate", "")[:10],
                fonte="Gupy",
            )
        )
    return vagas


def buscar_gupy(termo: str, limite: int = 50, baixar_fn: Baixar = None) -> list[Vaga]:
    baixar_fn = baixar_fn or baixar
    url = "https://portal.gupy.io/api/job-search/jobs?" + urllib.parse.urlencode(
        {"jobName": termo, "limit": limite, "offset": 0}
    )
    return ler_gupy(json.loads(baixar_fn(url)))


def ler_rss(xml: str, fonte: str = "RSS") -> list[Vaga]:
    """Lê um feed RSS de vagas (muitos sites e agregadores oferecem um)."""
    raiz = ET.fromstring(xml)
    vagas = []
    for item in raiz.iter("item"):
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        vagas.append(
            Vaga(
                id=f"rss-{guid}",
                titulo=(item.findtext("title") or "").strip(),
                empresa=(item.findtext("author") or "").strip(),
                local="",
                modalidade="remoto" if "remot" in (item.findtext("title") or "").lower() else "",
                link=link,
                publicada_em=(item.findtext("pubDate") or "").strip(),
                fonte=fonte,
            )
        )
    return vagas


def buscar_rss(url: str, fonte: str, baixar_fn: Baixar = None) -> list[Vaga]:
    baixar_fn = baixar_fn or baixar
    return ler_rss(baixar_fn(url), fonte)
