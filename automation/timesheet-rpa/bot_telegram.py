"""
Bot do Telegram para lançar horas no Timesheet por mensagem.

Fluxo:
- Você manda uma mensagem tipo "4h ADM Marketing" ou "3h AGA CT 15140" -
  pode ser bem mais livre/narrado se a IA estiver configurada (veja abaixo).
- Padrão recomendado pra ditar por áudio: tempo (horas), centro de custo,
  rateio (se tiver - senão fala "sem rateio"), observação - cada parte
  separada por uma pausa/vírgula, ex: "6 horas, ADM Marketing, sem
  rateio, revisão de slides". Isso vale tanto pro modo com IA quanto pro
  modo de regras (sem IA) - ambos foram ajustados pra entender essa
  ordem, incluindo erros comuns de transcrição de áudio (ex: Whisper
  ouvindo "rateio" como "raterio"/"rateiro"/"ratejo").
- Se `openai_api_key.txt` existir, o bot usa IA (OpenAI) pra interpretar a
  mensagem inteira - entende frases soltas, narradas, com rateio no meio,
  minutos por extenso, etc, e ainda calcula uma confiança de verdade pro
  centro de custo/rateio (não força mais cópia exata do catálogo). Sem
  esse arquivo, ou se a IA falhar (sem internet, chave inválida etc - te
  aviso no Telegram quando isso acontece), usa as regras de texto fixas.
- Ele já grava direto (sem esperar confirmação) e te mostra o que entendeu
  - dia, centro de custo, rateio, horas e observação - numa nova linha em
  lancamentos_timesheet.csv, o mesmo arquivo que o robo_timesheet_v7.py lê
  para preencher o Timesheet de verdade. Nao espera "sim" porque nem
  sempre a pessoa olha o Telegram na hora. Nada disso vai pro Timesheet
  de verdade até você mandar "preencher" - antes disso dá pra conferir
  tudo com "pendentes" e corrigir um lançamento específico com "editar N
  campo valor" (funciona local, sem precisar de internet/IA), ou "desfazer"
  pra tirar só o último.

Manda "preencher" (ou "atualizar") pro bot quando quiser que ele abra o
navegador (escondido) e lance no Timesheet de verdade tudo que estiver
pendente no CSV. Roda no mesmo processo do bot - so' um programa rodando,
sempre ligado, recebendo mensagens e preenchendo quando voce mandar.

Tambem aceita audio: manda um audio tipo "4 horas ontem ADM Marketing"
que o bot transcreve (Whisper local, sem custo) e processa igual a uma
mensagem de texto. Cada audio processa no seu proprio arquivo temporario
(nao se atrapalham entre si se voce mandar varios em sequencia). Na
primeira vez que usar audio, ele baixa o modelo de voz (uns 150MB) - pode
demorar um pouco.

Ao ligar (ou reconectar depois de ficar offline), o bot espera um pouco
pra receber qualquer mensagem que ficou em espera no Telegram e depois
preenche automaticamente o que estiver confirmado no CSV - nao precisa
mandar "preencher" toda vez que o PC ligar.

Limitações desta primeira versão (MVP):
- O lembrete (se passar 24h sem nenhum lançamento novo) e o preenchimento
  só funcionam enquanto este script estiver rodando no seu PC (use
  INSTALAR_INICIO_AUTOMATICO.bat pra ele ligar sozinho com o Windows).
- Só um preenchimento por vez - se mandar "preencher" de novo enquanto
  o anterior ainda esta rodando, ele avisa e ignora.

Configuração (arquivos locais, fora do git - veja README.md):
- telegram_token.txt: token do bot, do @BotFather
- telegram_chat_id.txt: seu chat_id, do @userinfobot (só esse numero usa o bot)
- openai_api_key.txt (opcional): chave da API da OpenAI, pra usar IA em vez
  de só regras de texto. Sem esse arquivo, o bot funciona normalmente, só
  com as regras.

Rodar:
    python bot_telegram.py
"""

import csv
import json
import re
import time as time_module
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import telebot
from faster_whisper import WhisperModel
from openai import OpenAI

from matching import limpar, melhor_correspondencia, melhores_correspondencias, termo_busca_padrao, LIMIAR_CONFIANCA
import robo_timesheet_v7

ARQUIVO_TOKEN = "telegram_token.txt"
ARQUIVO_CHAT_ID = "telegram_chat_id.txt"
ARQUIVO_OPENAI_KEY = "openai_api_key.txt"
ARQUIVO_CATALOGO = "catalogo_opcoes.csv"
ARQUIVO_LANCAMENTOS = "lancamentos_timesheet.csv"

MODELO_IA = "gpt-4o-mini"  # barato e rapido, suficiente pra esse tipo de extracao

LIMITE_HORAS_SEM_LANCAR = 24  # avisa se passar desse tempo sem nenhum lançamento novo
ESPERA_AO_LIGAR_SEGUNDOS = 45  # tempo pra receber mensagens em espera antes de preencher sozinho

MODELO_WHISPER = "base"  # troque para "small" se quiser mais precisao (mais lento)
ARQUIVO_AUDIO_TEMP = "audio_temp.ogg"

_modelo_whisper = None  # carregado so' na primeira vez que um audio chegar

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def ler_arquivo_config(caminho: str, nome_amigavel: str) -> str:
    p = Path(caminho)
    if not p.exists():
        raise SystemExit(
            f"Falta o arquivo {caminho} com {nome_amigavel}. Crie esse arquivo "
            f"(so' com o valor dentro, sem espacos/linhas extras) na mesma pasta do bot."
        )
    # utf-8-sig: no Windows/PowerShell, arquivos de texto costumam ser
    # salvos com um BOM (marca invisivel no inicio); sem isso aqui, o token
    # vinha com esse caractere colado na frente e quebrava o bot.
    return limpar(p.read_text(encoding="utf-8-sig"))


def ler_arquivo_opcional(caminho: str) -> str:
    """Igual ler_arquivo_config, mas nao quebra o bot se o arquivo nao existir."""
    p = Path(caminho)
    if not p.exists():
        return ""
    return limpar(p.read_text(encoding="utf-8-sig"))


def carregar_catalogo() -> Dict[str, List[Dict[str, str]]]:
    catalogo: Dict[str, List[Dict[str, str]]] = {"centro_custo": [], "rateio": []}
    with open(ARQUIVO_CATALOGO, "r", encoding="utf-8-sig", newline="") as f:
        for linha in csv.DictReader(f):
            tipo = limpar(linha.get("tipo", ""))
            if tipo in catalogo:
                catalogo[tipo].append({
                    "nome": limpar(linha.get("nome", "")),
                    "busca": limpar(linha.get("busca", "")),
                })
    return catalogo


def nomes_do_tipo(catalogo: Dict[str, List[Dict[str, str]]], tipo: str) -> List[str]:
    return [item["nome"] for item in catalogo.get(tipo, [])]


def busca_para_nome(catalogo: Dict[str, List[Dict[str, str]]], tipo: str, nome: str) -> str:
    for item in catalogo.get(tipo, []):
        if item["nome"] == nome:
            return item["busca"] or termo_busca_padrao(nome)
    return termo_busca_padrao(nome)


UNIDADES_EXTENSO = {
    "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9,
    "dez": 10, "onze": 11, "doze": 12, "treze": 13, "catorze": 14, "quatorze": 14,
    "quinze": 15, "dezesseis": 16, "dezessete": 17, "dezoito": 18, "dezenove": 19,
    "vinte": 20,
}
DEZENAS_EXTENSO = {"trinta": 30, "quarenta": 40, "cinquenta": 50}
_PADRAO_NUM_EXTENSO = "|".join(list(DEZENAS_EXTENSO.keys()) + list(UNIDADES_EXTENSO.keys()))


def numero_extenso_para_int(texto: str) -> Optional[int]:
    """Converte "quarenta e cinco", "trinta" ou "quinze" pro numero. Cobre so' 0-59."""
    texto = limpar(texto).lower()

    if texto in DEZENAS_EXTENSO:
        return DEZENAS_EXTENSO[texto]
    if texto in UNIDADES_EXTENSO:
        return UNIDADES_EXTENSO[texto]

    m = re.match(rf"^({'|'.join(DEZENAS_EXTENSO)})\s+e\s+({'|'.join(UNIDADES_EXTENSO)})$", texto)
    if m:
        return DEZENAS_EXTENSO[m.group(1)] + UNIDADES_EXTENSO[m.group(2)]

    return None


def extrair_horas(texto: str) -> Optional[str]:
    """
    Acha uma quantidade de horas na mensagem: "4h", "4:30", "04h30", "8
    horas" ou "3 horas e quarenta e cinco minutos". Retorna no formato
    "HHMM" (o mesmo que o robo espera), ou None se nao achar.
    """
    m = re.search(
        rf"(\d{{1,2}})\s*horas?\s+e\s+({_PADRAO_NUM_EXTENSO})(?:\s+e\s+({_PADRAO_NUM_EXTENSO}))?\s*minutos?\b",
        texto, re.IGNORECASE,
    )
    if m:
        texto_min = m.group(2) + (f" e {m.group(3)}" if m.group(3) else "")
        minutos = numero_extenso_para_int(texto_min)
        if minutos is not None:
            return f"{int(m.group(1)):02d}{minutos:02d}"

    m = re.search(r"(\d{1,2})\s*[:h]\s*(\d{2})\b", texto, re.IGNORECASE)
    if m:
        return f"{int(m.group(1)):02d}{m.group(2)}"

    m = re.search(r"(\d{1,2})\s*h(?:oras?)?\b", texto, re.IGNORECASE)
    if m:
        return f"{int(m.group(1)):02d}00"

    return None


def remover_horas(texto: str) -> str:
    texto = re.sub(
        rf"\d{{1,2}}\s*horas?\s+e\s+(?:{_PADRAO_NUM_EXTENSO})(?:\s+e\s+(?:{_PADRAO_NUM_EXTENSO}))?\s*minutos?\b",
        " ", texto, flags=re.IGNORECASE,
    )
    texto = re.sub(r"\d{1,2}\s*[:h]\s*\d{2}\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\d{1,2}\s*h(?:oras?)?\b", " ", texto, flags=re.IGNORECASE)
    return limpar(re.sub(r"\s+", " ", texto))


# O Whisper (transcrição de áudio) às vezes ouve errado a palavra "rateio"
# (ex: "raterio", "rateiro", "ratejo") - aceitamos essas variantes pra não
# perder o rateio só por causa de um erro de transcrição.
_PALAVRA_RATEIO = r"(?:rateio|raterio|rateiro|ratejo)"


def _tem_negacao_rateio(segmento: str) -> bool:
    """Detecta "sem rateio", "não tem rateio", "nenhum rateio", etc."""
    return bool(re.search(
        rf"\b(?:sem|n[ãa]o|nenhum\w*)\b[^,.;\n]{{0,20}}\b{_PALAVRA_RATEIO}\b"
        rf"|\b{_PALAVRA_RATEIO}\b[^,.;\n]{{0,20}}\b(?:nenhum\w*)\b",
        segmento, re.IGNORECASE,
    ))


def extrair_rateio(texto: str) -> Tuple[str, str]:
    """
    Se a mensagem mencionar "rateio" (ex: "... rateio state grid" ou
    "... rateio, proposta acompanhamento..."), extrai o texto depois dessa
    palavra como a descrição do rateio - so' ate' a proxima pontuação
    (vírgula/ponto), pra não pegar o resto da frase inteira quando a
    pessoa continua falando depois. Aceita virgula/pontuação logo depois
    da palavra "rateio" (comum quando a pessoa faz uma pausa ao falar).
    Se a pessoa disser que não tem rateio ("sem rateio", "não tem rateio"),
    retorna vazio sem tentar achar nada (isso é uma resposta válida, não
    uma falha). Retorna (texto_do_rateio_ou_vazio, texto_sem_esse_trecho).
    """
    m_neg = re.search(
        rf"\b(?:sem|n[ãa]o|nenhum\w*)\b[^,.;\n]{{0,20}}\b{_PALAVRA_RATEIO}\b"
        rf"|\b{_PALAVRA_RATEIO}\b[^,.;\n]{{0,20}}\b(?:nenhum\w*)\b",
        texto, re.IGNORECASE,
    )
    if m_neg:
        return "", limpar(texto[:m_neg.start()] + " " + texto[m_neg.end():])

    m = re.search(
        rf"\b{_PALAVRA_RATEIO}\b[\s,:;]*(?:é|eh|seria|foi)?[\s,:;]*([^,.;\n]{{1,60}})",
        texto, re.IGNORECASE,
    )
    if m and limpar(m.group(1)):
        return limpar(m.group(1)), limpar(texto[:m.start()] + " " + texto[m.end():])
    return "", texto


def mes_ano_de(d: date) -> str:
    return f"{d.year} - {MESES[d.month - 1]}"


NOMES_MES_NUM = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}
_PADRAO_NOMES_MES = "|".join(NOMES_MES_NUM.keys())


def extrair_data(texto: str) -> Tuple[str, str, str]:
    """
    Acha uma data mencionada na mensagem: "ontem", "anteontem", "hoje",
    "dia 3", "dia 3 de julho", "3 de julho", "03/07" ou "03/07/2026". Se
    nao achar nada (ou a data for invalida), usa hoje. Retorna
    (mes_ano, dia, texto_sem_a_data_mencionada) - a parte da data e'
    sempre removida do texto que sobra, pra nao vazar na Observação.

    Nao entende datas por extenso tipo "cinco de julho" (so' digitos).
    """
    hoje = date.today()

    def cortar(m: re.Match) -> str:
        return limpar(re.sub(r"\s+", " ", texto[:m.start()] + " " + texto[m.end():]))

    m = re.search(r"\bante ?ontem\b", texto, re.IGNORECASE)
    if m:
        d = hoje - timedelta(days=2)
        return mes_ano_de(d), f"{d.day:02d}", cortar(m)

    m = re.search(r"\bontem\b", texto, re.IGNORECASE)
    if m:
        d = hoje - timedelta(days=1)
        return mes_ano_de(d), f"{d.day:02d}", cortar(m)

    m = re.search(r"\bhoje\b", texto, re.IGNORECASE)
    if m:
        return mes_ano_de(hoje), f"{hoje.day:02d}", cortar(m)

    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", texto)
    if m:
        try:
            ano = int(m.group(3)) if m.group(3) else hoje.year
            if ano < 100:
                ano += 2000
            d = date(ano, int(m.group(2)), int(m.group(1)))
            return mes_ano_de(d), f"{d.day:02d}", cortar(m)
        except ValueError:
            pass  # data invalida (ex: 31/02) - ignora e tenta os outros formatos

    # "dia 5 de julho" ou "5 de julho" (com ou sem a palavra "dia") - comum
    # em audio, onde a pessoa fala o mes por extenso.
    m = re.search(rf"\b(?:dia\s+)?(\d{{1,2}})\s+de\s+({_PADRAO_NOMES_MES})\b", texto, re.IGNORECASE)
    if m:
        try:
            d = date(hoje.year, NOMES_MES_NUM[m.group(2).lower()], int(m.group(1)))
            return mes_ano_de(d), f"{d.day:02d}", cortar(m)
        except ValueError:
            pass

    m = re.search(r"\bdia\s+(\d{1,2})\b", texto, re.IGNORECASE)
    if m:
        try:
            d = date(hoje.year, hoje.month, int(m.group(1)))
            return mes_ano_de(d), f"{d.day:02d}", cortar(m)
        except ValueError:
            pass  # dia invalido pro mes atual (ex: dia 31 em fevereiro)

    return mes_ano_de(hoje), f"{hoje.day:02d}", texto


def gravar_lancamento(mes: str, dia: str, centro_custo: str, centro_custo_busca: str,
                       rateio: str, rateio_busca: str, horas: str, observacao: str) -> None:
    novo = not Path(ARQUIVO_LANCAMENTOS).exists()
    with open(ARQUIVO_LANCAMENTOS, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if novo:
            w.writerow([
                "mes", "dia", "centro_custo", "centro_custo_busca",
                "rateio", "rateio_busca", "horas", "observacao",
            ])
        w.writerow([mes, dia, centro_custo, centro_custo_busca, rateio, rateio_busca, horas, observacao])


def obter_modelo_whisper() -> WhisperModel:
    global _modelo_whisper
    if _modelo_whisper is None:
        print(f"Carregando modelo de voz (Whisper '{MODELO_WHISPER}') - so' na primeira vez...")
        _modelo_whisper = WhisperModel(MODELO_WHISPER, device="cpu", compute_type="int8")
    return _modelo_whisper


def transcrever_audio(caminho: str) -> str:
    modelo = obter_modelo_whisper()
    segmentos, _ = modelo.transcribe(caminho, language="pt")
    return limpar(" ".join(seg.text for seg in segmentos))


def horas_desde_ultimo_lancamento() -> Optional[float]:
    """
    Usa a data de modificacao do proprio CSV como "ultima vez que alguem
    lancou algo" - toda confirmacao no bot acrescenta uma linha nele, entao
    o mtime do arquivo sempre reflete o lancamento mais recente.
    """
    p = Path(ARQUIVO_LANCAMENTOS)
    if not p.exists():
        return None

    ultima_modificacao = datetime.fromtimestamp(p.stat().st_mtime)
    return (datetime.now() - ultima_modificacao).total_seconds() / 3600


TOKEN = ler_arquivo_config(ARQUIVO_TOKEN, "o token do bot (@BotFather)")
CHAT_ID_PERMITIDO = ler_arquivo_config(ARQUIVO_CHAT_ID, "seu chat_id (@userinfobot)")

# Opcional: se nao existir, o bot funciona so' com as regras de texto (sem IA).
OPENAI_API_KEY = ler_arquivo_opcional(ARQUIVO_OPENAI_KEY)
_cliente_ia = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

bot = telebot.TeleBot(TOKEN)
catalogo = carregar_catalogo()

# Trava simples pra nao rodar dois preenchimentos ao mesmo tempo.
preenchendo = threading.Lock()


def usuario_autorizado(message) -> bool:
    return str(message.chat.id) == CHAT_ID_PERMITIDO


def preencher_timesheet(chat_id: int) -> None:
    if not preenchendo.acquire(blocking=False):
        bot.send_message(chat_id, "Já tem um preenchimento rodando, aguenta ele terminar.")
        return

    try:
        bot.send_message(chat_id, "Beleza, abrindo o Timesheet e preenchendo (escondido). Aguenta um pouco...")
        resumo = robo_timesheet_v7.executar(headless=True, modo_automatico=True)
    except robo_timesheet_v7.LoginNaoDetectado:
        bot.send_message(
            chat_id,
            "Não consegui confirmar o login na intranet (sessão pode ter expirado). "
            "Roda o RODAR_ROBO.bat manualmente uma vez pra logar de novo.",
        )
        return
    except Exception as erro:
        bot.send_message(chat_id, f"Deu erro rodando o robô: {erro}")
        return
    finally:
        preenchendo.release()

    if resumo.get("falha_login"):
        bot.send_message(
            chat_id,
            "Não consegui confirmar o login na intranet (sessão pode ter expirado). "
            "Roda o RODAR_ROBO.bat manualmente uma vez pra logar de novo.",
        )
        return

    total = resumo["total"]
    lancados = resumo["lancados"]
    erros = resumo["erros"]

    if total == 0:
        bot.send_message(chat_id, "Não tinha nada pendente pra lançar.")
        return

    texto = f"Pronto! Lançados {lancados}/{total}."
    if erros:
        texto += f"\nCom erro: {len(erros)}"
        for item in erros[:5]:
            texto += f"\n  - Dia {item['dia']} ({item['centro_custo']}): {item['erro']}"

    bot.send_message(chat_id, texto)


@bot.message_handler(commands=["start", "ajuda"])
def start(message):
    if not usuario_autorizado(message):
        return
    bot.reply_to(
        message,
        "Manda assim: \"4h ADM Marketing\" ou \"3h AGA CT 15140\".\n"
        "Eu já lanço direto (sem precisar confirmar) e te mostro o que "
        "entendi.\n\n"
        "Também aceito áudio - dita na ordem tempo, centro de custo, "
        "rateio (se tiver, senão fala \"sem rateio\"), observação - ex: "
        "\"6 horas, ADM Marketing, sem rateio, revisão de slides\". Eu "
        "transcrevo e processo igual a uma mensagem de texto.\n\n"
        "Nada disso vai pro Timesheet de verdade na hora - fica só "
        "guardado localmente até você mandar \"preencher\". Antes disso, "
        "você pode conferir e corrigir:\n"
        "- \"pendentes\" mostra tudo que ainda não foi mandado (funciona "
        "mesmo sem internet).\n"
        "- \"editar N campo valor\" corrige um lançamento específico - "
        "ex: \"editar 2 centro_custo ADM Marketing\" ou \"editar 2 rateio "
        "sem\".\n"
        "- \"desfazer\" tira o último lançamento inteiro.\n\n"
        "Se não disser o dia, lanço pra hoje. Pra outro dia, inclua na "
        "mensagem: \"ontem\", \"anteontem\", \"hoje\", \"dia 3\", \"dia 3 "
        "de julho\" ou uma data tipo \"03/07\".\n\n"
        "Quando quiser mandar tudo pro Timesheet de verdade, manda "
        "\"preencher\" - eu abro o navegador escondido e faço sozinho "
        "(também faço isso sozinho uns segundos depois de eu ligar)."
    )


@bot.message_handler(func=lambda m: True, content_types=["text"])
def receber_mensagem(message):
    if not usuario_autorizado(message):
        return

    texto = limpar(message.text)
    texto_lower = texto.lower()

    if texto_lower in ("desfazer", "desfaz", "/desfazer", "não", "nao", "n", "cancela", "cancelar"):
        desfazer_ultimo(message)
        return

    if texto_lower in ("sim", "s", "confirma", "confirmar"):
        bot.reply_to(message, "Já lanço tudo direto, não precisa confirmar. Manda \"desfazer\" se algum sair errado.")
        return

    if texto_lower in ("preencher", "atualizar", "/preencher", "/atualizar"):
        threading.Thread(target=preencher_timesheet, args=(message.chat.id,), daemon=True).start()
        return

    if texto_lower in ("pendentes", "relatorio", "relatório", "lista", "listar", "/pendentes", "/relatorio"):
        listar_pendentes(message)
        return

    if texto_lower.startswith("editar"):
        editar_lancamento(message, texto)
        return

    processar_texto_lancamento(message, texto)


@bot.message_handler(content_types=["voice", "audio"])
def receber_audio(message):
    if not usuario_autorizado(message):
        return

    arquivo_id = message.voice.file_id if message.content_type == "voice" else message.audio.file_id

    try:
        info_arquivo = bot.get_file(arquivo_id)
        dados = bot.download_file(info_arquivo.file_path)

        # Nome unico por mensagem (nao so' por chat) - se a pessoa mandar
        # varios audios em sequencia, cada um processa no seu proprio
        # arquivo, sem um apagar/sobrescrever o do outro no meio do caminho.
        caminho_temp = Path(f"{message.chat.id}_{message.message_id}_{ARQUIVO_AUDIO_TEMP}")
        caminho_temp.write_bytes(dados)

        texto = transcrever_audio(str(caminho_temp))
        caminho_temp.unlink(missing_ok=True)
    except Exception as erro:
        bot.reply_to(message, f"Não consegui processar o áudio: {erro}")
        return

    if not texto:
        bot.reply_to(message, "Não consegui entender nada no áudio. Tenta falar de novo ou manda por texto.")
        return

    bot.reply_to(message, f"Entendi do áudio: \"{texto}\"")
    processar_texto_lancamento(message, texto)


def processar_texto_lancamento(message, texto: str) -> None:
    """
    Ponto de entrada pra interpretar uma mensagem/audio. Tenta a IA
    primeiro (se configurada) - ela entende frases livres/narradas bem
    melhor que as regras de texto. Se a IA nao estiver configurada, falhar
    (sem internet, chave invalida) ou nao identificar tudo com confianca,
    cai pras regras de texto (extrair_data/extrair_horas/etc) como reserva.
    """
    if _cliente_ia:
        dados_ia = interpretar_com_ia(message, texto)
        resultado = montar_lancamento_da_ia(dados_ia) if dados_ia else None

        if resultado:
            mes, dia, centro_custo, score_centro, rateio, rateio_aviso, horas, observacao = resultado
            salvar_lancamento(message, mes, dia, centro_custo, score_centro, horas, observacao, rateio, rateio_aviso)
            return

    processar_texto_lancamento_regras(message, texto)


def interpretar_com_ia(message, texto: str) -> Optional[dict]:
    opcoes_centro = nomes_do_tipo(catalogo, "centro_custo")
    opcoes_rateio = nomes_do_tipo(catalogo, "rateio")
    hoje = date.today()

    prompt_sistema = (
        "Você extrai lançamentos de timesheet de mensagens em português, "
        "faladas ou escritas. A pessoa dita SEMPRE nesta ordem: tempo "
        "(horas) -> centro de custo -> rateio (se tiver, senão fala 'sem "
        "rateio' ou não fala nada) -> observação. Ex: \"6 horas, ADM "
        "Marketing, sem rateio, revisão de slides\" ou \"4 horas, "
        "proposta state grid, rateio state grid, visita técnica\". As "
        "mensagens vêm de áudio transcrito por outra IA (Whisper), então "
        "podem ter erros de transcrição - a palavra \"rateio\" às vezes "
        "vira \"raterio\"/\"rateiro\"/\"ratejo\", e nomes de centro de "
        "custo podem vir com grafia/acentuação levemente diferentes "
        "(ex: \"adem marketing\" em vez de \"ADM Marketing\") ou com "
        "letras trocadas. Use o contexto e a lista de opções abaixo pra "
        "identificar a opção mais parecida mesmo com esses erros - não "
        "precisa ser uma cópia perfeita, escolha a mais próxima da lista. "
        "Responda APENAS com um JSON (sem texto antes/depois, sem "
        "markdown), no formato exato:\n"
        '{"dia": <numero ou null>, "mes_numero": <1 a 12 ou null>, '
        '"ano": <numero ou null>, "horas": "<HHMM ou null>", '
        '"centro_custo": <string ou null>, "rateio": <string ou null>, '
        '"observacao": "<string>"}\n\n'
        f"Hoje é dia {hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}. "
        "Se a mensagem não disser a data, retorne dia/mes_numero/ano como "
        "null (o sistema assume hoje).\n\n"
        "\"horas\" no formato 24h de 4 dígitos, ex: 3 horas e 45 minutos "
        "vira \"0345\", 4 horas vira \"0400\".\n\n"
        "\"centro_custo\" deve ser o nome mais parecido (mesmo que não "
        "seja cópia exata) desta lista, ou null se não achar nada "
        f"remotamente parecido:\n{json.dumps(opcoes_centro, ensure_ascii=False)}\n\n"
        "\"rateio\" deve ser o nome mais parecido desta lista, ou null se "
        "a pessoa disser que não tem rateio (\"sem rateio\", \"não tem "
        f"rateio\") ou não mencionar rateio:\n{json.dumps(opcoes_rateio, ensure_ascii=False)}\n\n"
        "\"observacao\" é só a parte que vem DEPOIS do rateio (ou depois "
        "do centro de custo, se não houver rateio) - um resumo curto e "
        "limpo do que foi feito, sem repetir data/horas/centro de "
        "custo/rateio."
    )

    try:
        resposta = _cliente_ia.chat.completions.create(
            model=MODELO_IA,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": texto},
            ],
            timeout=20,
        )
        return json.loads(resposta.choices[0].message.content)
    except Exception as erro:
        print(f"Falha ao interpretar com IA (caindo pras regras de texto): {erro}")
        try:
            bot.send_message(
                message.chat.id,
                f"⚠️ IA não respondeu agora ({erro}) - usando o modo de regras de texto pra esse lançamento.",
            )
        except Exception:
            pass
        return None


def montar_lancamento_da_ia(dados: dict) -> Optional[Tuple[str, str, str, float, str, str, str, str]]:
    """
    Valida/finaliza o JSON que a IA devolveu. Em vez de exigir que
    centro_custo/rateio sejam cópia exata do catálogo (a IA às vezes
    normaliza acentos/maiúsculas ou herda erros de transcrição do áudio),
    faz fuzzy-match do que ela devolveu contra o catálogo - assim a gente
    aproveita o entendimento da IA (que já lida bem com "adem marketing"
    -> ADM Marketing) e ainda mostra uma confiança de verdade pro usuário,
    em vez de sempre 100%. Retorna None só se não tiver hora válida ou
    nenhum centro de custo nem remotamente parecido.
    """
    horas = dados.get("horas")
    if not horas or not re.match(r"^\d{4}$", str(horas)):
        return None

    opcoes_centro = nomes_do_tipo(catalogo, "centro_custo")
    centro_bruto = limpar(dados.get("centro_custo") or "")
    centro_custo, score_centro = melhor_correspondencia(opcoes_centro, centro_bruto) if centro_bruto else (None, 0.0)
    if not centro_custo:
        return None

    opcoes_rateio = nomes_do_tipo(catalogo, "rateio")
    rateio_bruto = limpar(dados.get("rateio") or "")
    rateio, rateio_aviso = resolver_rateio(rateio_bruto)

    hoje = date.today()
    try:
        d = date(
            int(dados.get("ano") or hoje.year),
            int(dados.get("mes_numero") or hoje.month),
            int(dados.get("dia") or hoje.day),
        )
    except (ValueError, TypeError):
        d = hoje

    mes = mes_ano_de(d)
    dia = f"{d.day:02d}"
    observacao = limpar(dados.get("observacao") or "")

    return mes, dia, centro_custo, score_centro, rateio, rateio_aviso, str(horas), observacao


def processar_texto_lancamento_regras(message, texto: str) -> None:
    """
    Reserva pra quando a IA não está configurada (ou falhou). Segue o
    padrão de ditado combinado: tempo, centro de custo, rateio (se
    houver), observação - cada parte separada por vírgula/pausa. Quando a
    mensagem tem vírgulas (comum em áudio narrado), usa só o primeiro
    trecho pra achar o centro de custo (em vez da frase toda, que dilui a
    confiança do fuzzy-match). Mensagens curtas sem vírgula (ex: "4h ADM
    Marketing") continuam funcionando como antes.
    """
    mes, dia, texto_sem_data = extrair_data(texto)

    horas = extrair_horas(texto_sem_data)
    if not horas:
        bot.reply_to(
            message,
            "Não achei a quantidade de horas na mensagem. Dita na ordem: "
            "tempo, centro de custo, rateio (se tiver), observação - ex: "
            "\"4 horas, ADM Marketing, sem rateio, reunião de slides\"."
        )
        return

    resto = remover_horas(texto_sem_data)
    if not resto:
        bot.reply_to(message, "Entendi as horas, mas não achei o centro de custo. Manda de novo com o nome dele.")
        return

    segmentos = [s for s in (limpar(p) for p in resto.split(",")) if s]

    if len(segmentos) >= 2:
        centro_bruto = segmentos[0]
        demais = segmentos[1:]

        rateio_texto = ""
        indice_rateio: Optional[int] = None
        for i, seg in enumerate(demais):
            if _tem_negacao_rateio(seg):
                indice_rateio = i
                break
            if re.search(rf"\b{_PALAVRA_RATEIO}\b", seg, re.IGNORECASE):
                valor, _ = extrair_rateio(seg)
                if valor:
                    rateio_texto = valor
                    indice_rateio = i
                elif i + 1 < len(demais):
                    # "rateio" sozinho no proprio trecho - o valor deve
                    # estar no proximo (pausa logo apos falar a palavra).
                    rateio_texto = demais[i + 1]
                    indice_rateio = i + 1
                else:
                    indice_rateio = i
                break

        observacao = ", ".join(
            seg for i, seg in enumerate(demais)
            if i != indice_rateio and not re.search(rf"\b{_PALAVRA_RATEIO}\b", seg, re.IGNORECASE)
        )
    else:
        rateio_texto, resto_sem_rateio = extrair_rateio(resto)
        centro_bruto = resto_sem_rateio
        observacao = resto_sem_rateio

    if not centro_bruto:
        bot.reply_to(message, "Entendi as horas, mas não achei o centro de custo. Manda de novo com o nome dele.")
        return

    rateio_escolhido, rateio_aviso = resolver_rateio(rateio_texto)

    opcoes_centro = nomes_do_tipo(catalogo, "centro_custo")
    centro_escolhido, score_centro = melhor_correspondencia(opcoes_centro, centro_bruto)

    if not centro_escolhido:
        bot.reply_to(
            message,
            "Não achei nenhum centro de custo parecido com isso. "
            "Confere o nome e manda de novo."
        )
        return

    salvar_lancamento(message, mes, dia, centro_escolhido, score_centro, horas, observacao, rateio_escolhido, rateio_aviso)


def resolver_rateio(rateio_texto: str) -> Tuple[str, str]:
    """
    Tenta achar o rateio mencionado no catalogo. Retorna (rateio_escolhido
    ou "", aviso ou "" pra mostrar na confirmacao quando nao achar).
    """
    if not rateio_texto:
        return "", ""

    opcoes_rateio = nomes_do_tipo(catalogo, "rateio")
    rateio_escolhido, score_rateio = melhor_correspondencia(opcoes_rateio, rateio_texto)

    if rateio_escolhido and score_rateio >= LIMIAR_CONFIANCA:
        return rateio_escolhido, ""

    return "", (
        f"Não achei com certeza o rateio \"{rateio_texto}\" - deixei sem rateio, "
        "ajuste direto no lancamentos_timesheet.csv se precisar."
    )


def salvar_lancamento(message, mes: str, dia: str, centro_custo: str, score_centro: float,
                       horas: str, observacao: str, rateio: str = "", rateio_aviso: str = "") -> None:
    """
    Grava o lancamento direto, sem esperar confirmacao - a pessoa nem
    sempre olha o Telegram na hora, entao esperar "sim" so' fazia o
    lancamento se perder. Se sair errado, ela manda "desfazer".
    """
    gravar_lancamento(
        mes=mes,
        dia=dia,
        centro_custo=centro_custo,
        centro_custo_busca=busca_para_nome(catalogo, "centro_custo", centro_custo),
        rateio=rateio,
        rateio_busca=busca_para_nome(catalogo, "rateio", rateio) if rateio else "",
        horas=horas,
        observacao=observacao,
    )

    linha_rateio = f"Rateio: {rateio}\n" if rateio else ""
    aviso_rateio = f"\n{rateio_aviso}" if rateio_aviso else ""

    aviso_confianca = ""
    if score_centro < LIMIAR_CONFIANCA:
        opcoes_centro = nomes_do_tipo(catalogo, "centro_custo")
        alternativas = melhores_correspondencias(opcoes_centro, observacao, quantidade=3)
        alternativas = [nome for nome, score in alternativas if nome != centro_custo and score > 0][:2]
        texto_alt = f" Outras possibilidades: {', '.join(alternativas)}." if alternativas else ""
        aviso_confianca = (
            f"\n⚠️ Não tenho certeza desse centro de custo ({score_centro:.0%} de parecença)."
            f"{texto_alt} Se estiver errado, manda \"desfazer\" e tenta de novo mais específico."
        )

    bot.reply_to(
        message,
        f"Lançado:\n"
        f"Dia {dia} de {mes}\n"
        f"Centro de custo: {centro_custo} ({score_centro:.0%} de parecença)\n"
        f"{linha_rateio}"
        f"Horas: {horas[:2]}:{horas[2:]}\n"
        f"Observação: {observacao}"
        f"{aviso_rateio}"
        f"{aviso_confianca}"
        f"\n\nSe algo saiu errado, manda \"editar N campo valor\" pra "
        f"corrigir (veja os números com \"pendentes\") ou \"desfazer\" "
        f"pra tirar o último. Nada disso vai pro Timesheet de verdade até "
        f"você mandar \"preencher\"."
    )


def desfazer_ultimo(message) -> None:
    p = Path(ARQUIVO_LANCAMENTOS)
    if not p.exists():
        bot.reply_to(message, "Não tem nenhum lançamento pra desfazer.")
        return

    with p.open("r", encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.reader(f))

    if len(linhas) <= 1:
        bot.reply_to(message, "Não tem nenhum lançamento pra desfazer.")
        return

    removida = linhas.pop()
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(linhas)

    dia, centro, horas = removida[1], removida[2], removida[6]
    bot.reply_to(message, f"Desfeito: dia {dia}, {centro}, {horas[:2]}:{horas[2:]}h.")


CAMPOS_EDITAVEIS = {
    "hora": "horas", "horas": "horas",
    "centro": "centro_custo", "centro_custo": "centro_custo", "cc": "centro_custo",
    "rateio": "rateio",
    "obs": "observacao", "observacao": "observacao", "observação": "observacao",
    "dia": "dia",
}


def listar_pendentes(message) -> None:
    """
    Mostra tudo que já foi gravado no CSV mas ainda não foi mandado pro
    Timesheet de verdade (isso some da lista assim que "preencher" roda
    com sucesso) - funciona só lendo o arquivo local, sem depender de
    internet/IA, então dá pra conferir e corrigir mesmo offline antes de
    mandar "preencher".
    """
    p = Path(ARQUIVO_LANCAMENTOS)
    if not p.exists():
        bot.reply_to(message, "Não tem nenhum lançamento pendente.")
        return

    with p.open("r", encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))

    if not linhas:
        bot.reply_to(message, "Não tem nenhum lançamento pendente.")
        return

    texto = "Pendentes (ainda não mandados pro Timesheet):\n"
    for i, linha in enumerate(linhas, start=1):
        rateio = f" | Rateio: {linha['rateio']}" if linha.get("rateio") else ""
        horas = linha["horas"]
        texto += (
            f"\n{i}) Dia {linha['dia']} de {linha['mes']} - {linha['centro_custo']}"
            f"{rateio} - {horas[:2]}:{horas[2:]}h"
            f"\n   Obs: {linha['observacao']}"
        )

    texto += (
        "\n\nPra corrigir algum antes de mandar pro Timesheet, manda "
        "\"editar N campo valor\" (campos: horas, centro_custo, rateio, "
        "observacao, dia) - ex: \"editar 2 horas 0430\" ou \"editar 2 "
        "centro_custo ADM Marketing\" ou \"editar 2 rateio sem\" (tira o "
        "rateio). Pra apagar o último de todos, manda \"desfazer\"."
    )
    bot.reply_to(message, texto)


def editar_lancamento(message, texto: str) -> None:
    """
    Corrige um campo de um lançamento pendente sem precisar desfazer e
    ditar tudo de novo - manda "editar N campo valor", onde N é o número
    mostrado em "pendentes". Só mexe no CSV local (o que ainda não foi
    preenchido de verdade), então dá pra revisar/ajustar à vontade antes
    de mandar "preencher".
    """
    partes = texto.split(maxsplit=3)
    if len(partes) < 4 or not partes[1].isdigit():
        bot.reply_to(
            message,
            "Pra editar, manda \"editar N campo valor\" - ex: \"editar 2 "
            "horas 0430\" ou \"editar 2 centro_custo ADM Marketing\". "
            "Manda \"pendentes\" pra ver os números."
        )
        return

    indice = int(partes[1])
    campo = CAMPOS_EDITAVEIS.get(limpar(partes[2]).lower())
    valor = limpar(partes[3])

    if not campo:
        bot.reply_to(
            message,
            f"Não conheço o campo \"{partes[2]}\". Use: horas, centro_custo, "
            "rateio, observacao ou dia."
        )
        return

    p = Path(ARQUIVO_LANCAMENTOS)
    if not p.exists():
        bot.reply_to(message, "Não tem nenhum lançamento pendente.")
        return

    with p.open("r", encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.reader(f))

    cabecalho, dados = linhas[0], linhas[1:]
    if indice < 1 or indice > len(dados):
        bot.reply_to(message, f"Não achei o lançamento número {indice}. Manda \"pendentes\" pra ver a lista.")
        return

    idx_col = {nome: i for i, nome in enumerate(cabecalho)}
    linha = dados[indice - 1]

    if campo == "horas":
        horas_novas = extrair_horas(valor) or (valor if re.match(r"^\d{4}$", valor) else None)
        if not horas_novas:
            bot.reply_to(message, "Não entendi essas horas. Manda tipo \"4:30\", \"4h30\" ou \"0430\".")
            return
        linha[idx_col["horas"]] = horas_novas

    elif campo == "centro_custo":
        opcoes_centro = nomes_do_tipo(catalogo, "centro_custo")
        centro_escolhido, score = melhor_correspondencia(opcoes_centro, valor)
        if not centro_escolhido:
            bot.reply_to(message, "Não achei nenhum centro de custo parecido com isso.")
            return
        linha[idx_col["centro_custo"]] = centro_escolhido
        linha[idx_col["centro_custo_busca"]] = busca_para_nome(catalogo, "centro_custo", centro_escolhido)

    elif campo == "rateio":
        if valor.lower() in ("sem", "nenhum", "remover", "tirar", "limpar", "não", "nao"):
            linha[idx_col["rateio"]] = ""
            linha[idx_col["rateio_busca"]] = ""
        else:
            rateio_escolhido, _ = resolver_rateio(valor)
            if not rateio_escolhido:
                bot.reply_to(
                    message,
                    f"Não achei com certeza o rateio \"{valor}\". Tenta um nome "
                    "mais parecido com o do catálogo."
                )
                return
            linha[idx_col["rateio"]] = rateio_escolhido
            linha[idx_col["rateio_busca"]] = busca_para_nome(catalogo, "rateio", rateio_escolhido)

    elif campo == "observacao":
        linha[idx_col["observacao"]] = valor

    elif campo == "dia":
        if not re.match(r"^\d{1,2}$", valor):
            bot.reply_to(message, "O dia deve ser só o número, ex: \"editar 2 dia 7\".")
            return
        linha[idx_col["dia"]] = f"{int(valor):02d}"

    with p.open("w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows([cabecalho] + dados)

    linha_dict = dict(zip(cabecalho, linha))
    rateio_txt = f" | Rateio: {linha_dict['rateio']}" if linha_dict.get("rateio") else ""
    horas_dict = linha_dict["horas"]
    bot.reply_to(
        message,
        f"Corrigido, lançamento {indice} agora é:\n"
        f"Dia {linha_dict['dia']} de {linha_dict['mes']} - {linha_dict['centro_custo']}"
        f"{rateio_txt} - {horas_dict[:2]}:{horas_dict[2:]}h\n"
        f"Obs: {linha_dict['observacao']}"
    )


def loop_lembrete() -> None:
    ja_avisado = False

    while True:
        horas = horas_desde_ultimo_lancamento()

        if horas is not None and horas >= LIMITE_HORAS_SEM_LANCAR:
            if not ja_avisado:
                try:
                    bot.send_message(
                        CHAT_ID_PERMITIDO,
                        f"Já faz mais de {LIMITE_HORAS_SEM_LANCAR}h que você não lança nada no "
                        "Timesheet. Bora lançar? Manda tipo \"4h ADM Marketing\".",
                    )
                except Exception:
                    pass
                ja_avisado = True
        else:
            # Voltou a lancar (ou ainda nao passou do limite) - reseta pra
            # poder avisar de novo se ficar 24h parado outra vez.
            ja_avisado = False

        time_module.sleep(600)


def preencher_ao_iniciar() -> None:
    # Espera um pouco pra dar tempo do bot processar qualquer mensagem que
    # ficou em espera no Telegram (enquanto o PC estava desligado) antes
    # de preencher - assim, ligar o PC ja' cobre "recebe o que ficou
    # pendente + lanca no Timesheet" sem precisar mandar "preencher".
    time_module.sleep(ESPERA_AO_LIGAR_SEGUNDOS)
    preencher_timesheet(CHAT_ID_PERMITIDO)


if __name__ == "__main__":
    print("Bot do Timesheet rodando. Ctrl+C para parar.")
    threading.Thread(target=loop_lembrete, daemon=True).start()
    threading.Thread(target=preencher_ao_iniciar, daemon=True).start()
    bot.infinity_polling()
