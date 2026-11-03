# Monitor de Vagas

Script em Python que busca vagas de emprego, filtra pelo que interessa e **avisa só das vagas novas**, no terminal ou no Telegram.

Fiz para a minha própria busca de emprego: em vez de abrir os sites todo dia, deixo rodando e recebo a lista pronta.

## Como funciona

1. **Busca** vagas no portal da Gupy (um termo por busca) e, opcionalmente, em feeds RSS.
2. **Filtra** pelo título: precisa ter uma palavra da lista `incluir` e nenhuma da lista `excluir` (ignora acento e maiúscula, e compara palavra inteira).
3. **Filtra pelo local**: aceita vagas remotas e, das presenciais/híbridas, só as das cidades configuradas.
4. **Guarda** num SQLite as vagas já vistas, para não avisar duas vezes.
5. **Avisa** das novas no terminal e, se configurado, por um bot do Telegram.

## Como rodar

Precisa só do Python 3.11+ (sem dependências externas).

```bash
cp config.exemplo.toml config.toml   # ajuste termos, palavras e cidades
python -m monitor_vagas              # roda uma vez
python -m monitor_vagas --a-cada 60  # repete a cada 60 minutos
```

Para receber no Telegram, crie um bot com o @BotFather e defina:

```bash
export TELEGRAM_TOKEN="token-do-bot"
export TELEGRAM_CHAT_ID="seu-chat-id"
```

## Estrutura

```
monitor_vagas/fontes.py         leitura da Gupy e de feeds RSS
monitor_vagas/filtros.py        regras de palavras-chave, modalidade e cidade
monitor_vagas/armazenamento.py  histórico de vagas vistas (SQLite)
monitor_vagas/alertas.py        mensagem no terminal e no Telegram
monitor_vagas/__main__.py       linha de comando
tests/                          testes com respostas salvas (não acessam a internet)
```

## Testes

```bash
pip install pytest
python -m pytest
```

## Tecnologias

Python · SQLite · urllib · pytest
