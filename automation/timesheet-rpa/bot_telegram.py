"""
Bot do Telegram para lançar horas no Timesheet por mensagem.

Fluxo:
- Você manda uma mensagem tipo "4h ADM Marketing" ou "3h AGA CT 15140".
- O bot acha o Centro de custo mais parecido no catálogo (mesmo algoritmo
  de comparação usado pelo robo_timesheet_v7.py, via matching.py).
- Ele devolve o que entendeu e pede confirmação (sim/não).
- Confirmando, grava uma nova linha em lancamentos_timesheet.csv - o mesmo
  arquivo que o robo_timesheet_v7.py lê para preencher o Timesheet de verdade.

Manda "preencher" (ou "atualizar") pro bot quando quiser que ele abra o
navegador (escondido) e lance no Timesheet de verdade tudo que estiver
pendente no CSV. Roda no mesmo processo do bot - so' um programa rodando,
sempre ligado, recebendo mensagens e preenchendo quando voce mandar.

Tambem aceita audio: manda um audio tipo "4 horas ontem ADM Marketing"
que o bot transcreve (Whisper local, sem custo) e processa igual a uma
mensagem de texto. Na primeira vez que usar audio, ele baixa o modelo de
voz (uns 150MB) - pode demorar um pouco.

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

Configuração (2 arquivos locais, fora do git - veja README.md):
- telegram_token.txt: token do bot, do @BotFather
- telegram_chat_id.txt: seu chat_id, do @userinfobot (só esse numero usa o bot)

Rodar:
    python bot_telegram.py
"""

import csv
import re
import time as time_module
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import telebot
from faster_whisper import WhisperModel

from matching import limpar, melhor_correspondencia, melhores_correspondencias, termo_busca_padrao, LIMIAR_CONFIANCA
import robo_timesheet_v7

ARQUIVO_TOKEN = "telegram_token.txt"
ARQUIVO_CHAT_ID = "telegram_chat_id.txt"
ARQUIVO_CATALOGO = "catalogo_opcoes.csv"
ARQUIVO_LANCAMENTOS = "lancamentos_timesheet.csv"

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


def extrair_horas(texto: str) -> Optional[str]:
    """
    Acha uma quantidade de horas na mensagem: "4h", "4:30", "04h30", "8 horas".
    Retorna no formato "HHMM" (o mesmo que o robo espera), ou None se nao achar.
    """
    m = re.search(r"(\d{1,2})\s*[:h]\s*(\d{2})\b", texto, re.IGNORECASE)
    if m:
        return f"{int(m.group(1)):02d}{m.group(2)}"

    m = re.search(r"(\d{1,2})\s*h(?:oras?)?\b", texto, re.IGNORECASE)
    if m:
        return f"{int(m.group(1)):02d}00"

    return None


def remover_horas(texto: str) -> str:
    texto = re.sub(r"\d{1,2}\s*[:h]\s*\d{2}\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\d{1,2}\s*h(?:oras?)?\b", " ", texto, flags=re.IGNORECASE)
    return limpar(re.sub(r"\s+", " ", texto))


def extrair_rateio(texto: str) -> Tuple[str, str]:
    """
    Se a mensagem mencionar "rateio" (ex: "... rateio state grid"), extrai
    o texto depois dessa palavra como a descrição do rateio. Mencione o
    rateio por último na mensagem (depois do centro de custo). Retorna
    (texto_do_rateio_ou_vazio, texto_sem_esse_trecho).
    """
    m = re.search(r"\brateio\b[:\s]*(.*)$", texto, re.IGNORECASE)
    if m and limpar(m.group(1)):
        return limpar(m.group(1)), limpar(texto[:m.start()])
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

bot = telebot.TeleBot(TOKEN)
catalogo = carregar_catalogo()

# Guarda a ultima proposta feita para cada chat, esperando confirmacao.
pendentes: Dict[int, Dict[str, str]] = {}

# Quando a confianca do centro de custo e' baixa, guarda aqui as opcoes
# sugeridas + o resto do lancamento, esperando a pessoa responder com um
# numero (1, 2, 3...) escolhendo qual delas e' a certa.
aguardando_escolha: Dict[int, Dict[str, object]] = {}

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
        "Eu acho o centro de custo mais parecido e confirmo com você antes "
        "de gravar (responda sim/não).\n\n"
        "Se não disser o dia, lanço pra hoje. Pra outro dia, inclua na "
        "mensagem: \"ontem\", \"anteontem\", \"hoje\", \"dia 3\", \"dia 3 "
        "de julho\" ou uma data tipo \"03/07\".\n\n"
        "Se eu não tiver certeza do centro de custo, mostro até 3 opções "
        "parecidas numeradas - só responder com o número certo.\n\n"
        "Quando quiser mandar tudo pro Timesheet de verdade, manda "
        "\"preencher\" - eu abro o navegador escondido e faço sozinho.\n\n"
        "Também aceito áudio - manda gravando \"4 horas ontem ADM "
        "Marketing\" que eu transcrevo e processo igual.\n\n"
        "Se tiver rateio, menciona por último na mensagem: \"3h PROPOSTA "
        "rateio state grid\". Se não achar com certeza, deixo sem rateio "
        "e aviso."
    )


@bot.message_handler(func=lambda m: True, content_types=["text"])
def receber_mensagem(message):
    if not usuario_autorizado(message):
        return

    texto = limpar(message.text)
    texto_lower = texto.lower()

    if texto_lower in ("sim", "s", "confirma", "confirmar"):
        confirmar_pendente(message)
        return

    if texto_lower in ("não", "nao", "n", "cancela", "cancelar"):
        pendentes.pop(message.chat.id, None)
        aguardando_escolha.pop(message.chat.id, None)
        bot.reply_to(message, "Beleza, descartei. Manda de novo quando quiser.")
        return

    if texto_lower in ("preencher", "atualizar", "/preencher", "/atualizar"):
        threading.Thread(target=preencher_timesheet, args=(message.chat.id,), daemon=True).start()
        return

    if texto_lower.isdigit() and message.chat.id in aguardando_escolha:
        escolher_centro_por_numero(message, int(texto_lower))
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

        caminho_temp = Path(f"{message.chat.id}_{ARQUIVO_AUDIO_TEMP}")
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
    mes, dia, texto_sem_data = extrair_data(texto)

    horas = extrair_horas(texto_sem_data)
    if not horas:
        bot.reply_to(message, "Não achei a quantidade de horas na mensagem. Tenta algo tipo \"4h ADM Marketing\" ou \"4h ontem ADM Marketing\".")
        return

    resto = remover_horas(texto_sem_data)
    if not resto:
        bot.reply_to(message, "Entendi as horas, mas não achei o centro de custo. Manda de novo com o nome dele.")
        return

    rateio_texto, resto = extrair_rateio(resto)
    if not resto:
        bot.reply_to(message, "Entendi as horas e o rateio, mas não achei o centro de custo. Manda de novo com o nome dele.")
        return

    rateio_escolhido, rateio_aviso = resolver_rateio(rateio_texto)

    opcoes_centro = nomes_do_tipo(catalogo, "centro_custo")
    centro_escolhido, score_centro = melhor_correspondencia(opcoes_centro, resto)

    if not centro_escolhido or score_centro < LIMIAR_CONFIANCA:
        candidatos = melhores_correspondencias(opcoes_centro, resto, quantidade=3)
        candidatos = [(nome, score) for nome, score in candidatos if score > 0]

        if not candidatos:
            bot.reply_to(
                message,
                "Não achei nenhum centro de custo parecido com isso. "
                "Confere o nome e manda de novo."
            )
            return

        aguardando_escolha[message.chat.id] = {
            "mes": mes,
            "dia": dia,
            "horas": horas,
            "observacao": resto,
            "rateio": rateio_escolhido,
            "opcoes": [nome for nome, _ in candidatos],
        }

        linhas = "\n".join(f"{i}. {nome} ({score:.0%})" for i, (nome, score) in enumerate(candidatos, start=1))
        bot.reply_to(
            message,
            f"Não tenho certeza do centro de custo pra \"{resto}\". Quis dizer:\n"
            f"{linhas}\n\n"
            "Responde com o número, ou manda de novo escrevendo o nome mais certo."
        )
        return

    propor_lancamento(message, mes, dia, centro_escolhido, score_centro, horas, resto, rateio_escolhido, rateio_aviso)


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


def escolher_centro_por_numero(message, numero: int) -> None:
    dados = aguardando_escolha.pop(message.chat.id, None)
    if not dados:
        return

    opcoes = dados["opcoes"]
    if numero < 1 or numero > len(opcoes):
        aguardando_escolha[message.chat.id] = dados  # devolve, era so' numero invalido
        bot.reply_to(message, f"Escolhe um número de 1 a {len(opcoes)}.")
        return

    centro_escolhido = opcoes[numero - 1]
    propor_lancamento(
        message, dados["mes"], dados["dia"], centro_escolhido, 1.0,
        dados["horas"], dados["observacao"], dados.get("rateio", ""), "",
    )


def propor_lancamento(message, mes: str, dia: str, centro_custo: str, score_centro: float,
                       horas: str, observacao: str, rateio: str = "", rateio_aviso: str = "") -> None:
    pendentes[message.chat.id] = {
        "mes": mes,
        "dia": dia,
        "centro_custo": centro_custo,
        "centro_custo_busca": busca_para_nome(catalogo, "centro_custo", centro_custo),
        "rateio": rateio,
        "rateio_busca": busca_para_nome(catalogo, "rateio", rateio) if rateio else "",
        "horas": horas,
        "observacao": observacao,
    }

    linha_rateio = f"Rateio: {rateio}\n" if rateio else ""
    aviso = f"\n{rateio_aviso}\n" if rateio_aviso else ""

    bot.reply_to(
        message,
        f"Entendi:\n"
        f"Dia {dia} de {mes}\n"
        f"Centro de custo: {centro_custo} ({score_centro:.0%} de parecença)\n"
        f"{linha_rateio}"
        f"Horas: {horas[:2]}:{horas[2:]}\n"
        f"Observação: {observacao}\n"
        f"{aviso}\n"
        "Confirma? (sim/não)"
    )


def confirmar_pendente(message) -> None:
    dados = pendentes.pop(message.chat.id, None)
    if not dados:
        bot.reply_to(message, "Não tem nada pendente pra confirmar. Manda o lançamento primeiro.")
        return

    gravar_lancamento(**dados)
    bot.reply_to(message, "Lançado no CSV. Quando quiser, manda \"preencher\" pra eu mandar tudo pro Timesheet de verdade.")


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
