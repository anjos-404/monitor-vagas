import json
from pathlib import Path

import pytest

from monitor_vagas import __main__ as cli
from monitor_vagas import fontes
from monitor_vagas.alertas import montar_mensagem
from monitor_vagas.armazenamento import Historico
from monitor_vagas.filtros import Filtro, normalizar
from monitor_vagas.models import Vaga

FIXTURES = Path(__file__).parent / "fixtures"
GUPY = (FIXTURES / "gupy.json").read_text(encoding="utf-8")
RSS = (FIXTURES / "vagas.rss").read_text(encoding="utf-8")


def vaga(titulo, modalidade="remoto", local="", id_="x"):
    return Vaga(id=id_, titulo=titulo, empresa="E", local=local, modalidade=modalidade, link="https://x")


def test_normalizar_tira_acento_e_maiuscula():
    assert normalizar("Desenvolvedor JÚNIOR") == "desenvolvedor junior"


def test_le_resposta_da_gupy():
    vagas = fontes.ler_gupy(json.loads(GUPY))
    assert len(vagas) == 5
    primeira = vagas[0]
    assert primeira.id == "gupy-101"
    assert primeira.modalidade == "remoto"
    assert primeira.publicada_em == "2026-10-30"
    assert vagas[2].local == "Curitiba, Paraná"
    assert vagas[4].modalidade == "híbrido"


def test_busca_gupy_monta_url_com_o_termo():
    urls = []

    def falso(url):
        urls.append(url)
        return GUPY

    fontes.buscar_gupy("desenvolvedor junior", baixar_fn=falso)
    assert "jobName=desenvolvedor+junior" in urls[0]


def test_le_feed_rss():
    vagas = fontes.ler_rss(RSS, "Teste")
    assert [v.titulo for v in vagas] == ["Desenvolvedor C# Júnior (Remoto)", "Tech Lead .NET"]
    assert vagas[0].modalidade == "remoto"
    assert vagas[0].fonte == "Teste"


@pytest.fixture
def filtro():
    return Filtro(
        incluir=["junior", "jr", "desenvolvedor", "programador"],
        excluir=["pleno", "senior", "sr"],
        cidades=["Curitiba", "São José dos Pinhais"],
    )


@pytest.mark.parametrize(
    "titulo,modalidade,local,esperado",
    [
        ("Desenvolvedor .NET Júnior", "remoto", "", True),
        ("Desenvolvedor Back-end Pleno", "remoto", "", False),
        ("Programador Jr", "presencial", "Curitiba, Paraná", True),
        ("Desenvolvedor Júnior", "presencial", "Recife, Pernambuco", False),
        ("Analista Financeiro", "remoto", "", False),
        ("Analista de Aplicações Júnior", "híbrido", "São José dos Pinhais", True),
    ],
)
def test_filtro(filtro, titulo, modalidade, local, esperado):
    assert filtro.aceita(vaga(titulo, modalidade, local)) is esperado


def test_filtro_compara_palavra_inteira():
    # "sr" não pode descartar uma vaga só porque aparece dentro de outra palavra
    f = Filtro(incluir=["desenvolvedor"], excluir=["sr"])
    assert f.aceita(vaga("Desenvolvedor de Sistemas Srvless"))
    assert not f.aceita(vaga("Desenvolvedor Sr"))


def test_filtro_por_modalidade():
    f = Filtro(modalidades=["remoto"])
    assert f.aceita(vaga("Dev", "remoto"))
    assert not f.aceita(vaga("Dev", "presencial", "Curitiba"))


def test_historico_so_devolve_vagas_novas(tmp_path):
    h = Historico(tmp_path / "v.db")
    a, b = vaga("A", id_="1"), vaga("B", id_="2")
    assert h.novas([a, b]) == [a, b]
    assert h.novas([a, b]) == []
    assert h.novas([vaga("C", id_="3"), a]) == [vaga("C", id_="3")]
    assert h.total() == 3
    h.fechar()


def test_mensagem_lista_as_vagas():
    msg = montar_mensagem([vaga("Dev Jr", "presencial", "Curitiba")])
    assert msg.startswith("1 vaga(s) nova(s):")
    assert "Dev Jr · E · Curitiba (presencial)" in msg


def test_rodada_completa_avisa_so_uma_vez(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(fontes, "baixar", lambda url, timeout=20: GUPY)
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    config = {
        "gupy": {"termos": ["desenvolvedor"]},
        "filtro": {
            "incluir": ["junior", "jr"],
            "excluir": ["pleno"],
            "cidades": ["Curitiba", "São José dos Pinhais"],
        },
    }
    h = Historico(tmp_path / "v.db")
    novas = cli.rodar_uma_vez(config, h)
    assert sorted(v.id for v in novas) == ["gupy-101", "gupy-103", "gupy-105"]
    assert "3 vaga(s) nova(s)" in capsys.readouterr().out
    assert cli.rodar_uma_vez(config, h) == []
    assert "Nenhuma vaga nova." in capsys.readouterr().out
    h.fechar()


def test_fonte_com_erro_nao_derruba_as_outras(monkeypatch, capsys):
    def quebra(termo, limite=50, baixar_fn=None):
        raise OSError("fora do ar")

    monkeypatch.setattr(fontes, "buscar_gupy", quebra)
    assert cli.coletar({"gupy": {"termos": ["dev"]}}) == []
    assert "fora do ar" in capsys.readouterr().err
