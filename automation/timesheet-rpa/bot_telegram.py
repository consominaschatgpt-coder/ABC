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

Limitações desta primeira versão (MVP):
- Não preenche Rateio pela mensagem (deixe em branco e ajuste no CSV se
  precisar de rateio nesse lançamento).
- O lembrete (se passar 24h sem nenhum lançamento novo) e o "preencher"
  só funcionam enquanto este script estiver rodando no seu PC.
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

from matching import limpar, melhor_correspondencia, termo_busca_padrao, LIMIAR_CONFIANCA
import robo_timesheet_v7

ARQUIVO_TOKEN = "telegram_token.txt"
ARQUIVO_CHAT_ID = "telegram_chat_id.txt"
ARQUIVO_CATALOGO = "catalogo_opcoes.csv"
ARQUIVO_LANCAMENTOS = "lancamentos_timesheet.csv"

LIMITE_HORAS_SEM_LANCAR = 24  # avisa se passar desse tempo sem nenhum lançamento novo

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


def mes_ano_de(d: date) -> str:
    return f"{d.year} - {MESES[d.month - 1]}"


def extrair_data(texto: str) -> Tuple[str, str, str]:
    """
    Acha uma data mencionada na mensagem: "ontem", "anteontem", "dia 3",
    "03/07" ou "03/07/2026". Se nao achar nada (ou a data for invalida),
    usa hoje. Retorna (mes_ano, dia, texto_sem_a_data_mencionada).
    """
    hoje = date.today()

    m = re.search(r"\bante ?ontem\b", texto, re.IGNORECASE)
    if m:
        d = hoje - timedelta(days=2)
        texto = limpar(re.sub(r"\s+", " ", texto[:m.start()] + " " + texto[m.end():]))
        return mes_ano_de(d), f"{d.day:02d}", texto

    m = re.search(r"\bontem\b", texto, re.IGNORECASE)
    if m:
        d = hoje - timedelta(days=1)
        texto = limpar(re.sub(r"\s+", " ", texto[:m.start()] + " " + texto[m.end():]))
        return mes_ano_de(d), f"{d.day:02d}", texto

    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", texto)
    if m:
        try:
            ano = int(m.group(3)) if m.group(3) else hoje.year
            if ano < 100:
                ano += 2000
            d = date(ano, int(m.group(2)), int(m.group(1)))
            texto = limpar(re.sub(r"\s+", " ", texto[:m.start()] + " " + texto[m.end():]))
            return mes_ano_de(d), f"{d.day:02d}", texto
        except ValueError:
            pass  # data invalida (ex: 31/02) - ignora e tenta os outros formatos

    m = re.search(r"\bdia\s+(\d{1,2})\b", texto, re.IGNORECASE)
    if m:
        try:
            d = date(hoje.year, hoje.month, int(m.group(1)))
            texto = limpar(re.sub(r"\s+", " ", texto[:m.start()] + " " + texto[m.end():]))
            return mes_ano_de(d), f"{d.day:02d}", texto
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
        "mensagem: \"ontem\", \"anteontem\", \"dia 3\" ou uma data tipo "
        "\"03/07\".\n\n"
        "Quando quiser mandar tudo pro Timesheet de verdade, manda "
        "\"preencher\" - eu abro o navegador escondido e faço sozinho.\n\n"
        "Também aceito áudio - manda gravando \"4 horas ontem ADM "
        "Marketing\" que eu transcrevo e processo igual.\n\n"
        "Por enquanto não preencho Rateio pela mensagem - se precisar, "
        "ajuste direto no lancamentos_timesheet.csv."
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
        bot.reply_to(message, "Beleza, descartei. Manda de novo quando quiser.")
        return

    if texto_lower in ("preencher", "atualizar", "/preencher", "/atualizar"):
        threading.Thread(target=preencher_timesheet, args=(message.chat.id,), daemon=True).start()
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

    opcoes_centro = nomes_do_tipo(catalogo, "centro_custo")
    centro_escolhido, score_centro = melhor_correspondencia(opcoes_centro, resto)

    if not centro_escolhido or score_centro < LIMIAR_CONFIANCA:
        bot.reply_to(
            message,
            f"Não tenho certeza do centro de custo (melhor palpite: {centro_escolhido or '-'}, "
            f"{score_centro:.0%} de parecença). Pode reescrever mais parecido com o nome oficial?"
        )
        return

    pendentes[message.chat.id] = {
        "mes": mes,
        "dia": dia,
        "centro_custo": centro_escolhido,
        "centro_custo_busca": busca_para_nome(catalogo, "centro_custo", centro_escolhido),
        "rateio": "",
        "rateio_busca": "",
        "horas": horas,
        "observacao": resto,
    }

    bot.reply_to(
        message,
        f"Entendi:\n"
        f"Dia {dia} de {mes}\n"
        f"Centro de custo: {centro_escolhido} ({score_centro:.0%} de parecença)\n"
        f"Horas: {horas[:2]}:{horas[2:]}\n"
        f"Observação: {resto}\n\n"
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


if __name__ == "__main__":
    print("Bot do Timesheet rodando. Ctrl+C para parar.")
    threading.Thread(target=loop_lembrete, daemon=True).start()
    bot.infinity_polling()
