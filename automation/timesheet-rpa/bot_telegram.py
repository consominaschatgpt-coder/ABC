"""
Bot do Telegram para lançar horas no Timesheet por mensagem.

Fluxo:
- Você manda uma mensagem tipo "4h ADM Marketing" ou "3h AGA CT 15140".
- O bot acha o Centro de custo mais parecido no catálogo (mesmo algoritmo
  de comparação usado pelo robo_timesheet_v7.py, via matching.py).
- Ele devolve o que entendeu e pede confirmação (sim/não).
- Confirmando, grava uma nova linha em lancamentos_timesheet.csv - o mesmo
  arquivo que o robo_timesheet_v7.py lê para preencher o Timesheet de verdade.

Limitações desta primeira versão (MVP):
- Sempre lança pra hoje (não dá pra dizer "ontem" ainda).
- Não preenche Rateio pela mensagem (deixe em branco e ajuste no CSV se
  precisar de rateio nesse lançamento).
- O lembrete diário só funciona enquanto este script estiver rodando no
  seu PC.

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
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import telebot

from matching import limpar, melhor_correspondencia, termo_busca_padrao, LIMIAR_CONFIANCA

ARQUIVO_TOKEN = "telegram_token.txt"
ARQUIVO_CHAT_ID = "telegram_chat_id.txt"
ARQUIVO_CATALOGO = "catalogo_opcoes.csv"
ARQUIVO_LANCAMENTOS = "lancamentos_timesheet.csv"

HORA_LEMBRETE = 18  # a partir dessa hora, cobra se ainda não lançou nada hoje

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
    return limpar(p.read_text(encoding="utf-8"))


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


def mes_ano_atual() -> str:
    hoje = date.today()
    return f"{hoje.year} - {MESES[hoje.month - 1]}"


def dia_atual() -> str:
    return f"{date.today().day:02d}"


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


def ja_lancou_hoje() -> bool:
    if not Path(ARQUIVO_LANCAMENTOS).exists():
        return False

    mes_hoje = mes_ano_atual()
    dia_hoje = dia_atual()

    with open(ARQUIVO_LANCAMENTOS, "r", encoding="utf-8-sig", newline="") as f:
        for linha in csv.DictReader(f):
            if limpar(linha.get("mes", "")) == mes_hoje and limpar(linha.get("dia", "")).zfill(2) == dia_hoje:
                return True

    return False


TOKEN = ler_arquivo_config(ARQUIVO_TOKEN, "o token do bot (@BotFather)")
CHAT_ID_PERMITIDO = ler_arquivo_config(ARQUIVO_CHAT_ID, "seu chat_id (@userinfobot)")

bot = telebot.TeleBot(TOKEN)
catalogo = carregar_catalogo()

# Guarda a ultima proposta feita para cada chat, esperando confirmacao.
pendentes: Dict[int, Dict[str, str]] = {}


def usuario_autorizado(message) -> bool:
    return str(message.chat.id) == CHAT_ID_PERMITIDO


@bot.message_handler(commands=["start", "ajuda"])
def start(message):
    if not usuario_autorizado(message):
        return
    bot.reply_to(
        message,
        "Manda assim: \"4h ADM Marketing\" ou \"3h AGA CT 15140\".\n"
        "Eu acho o centro de custo mais parecido e confirmo com você antes "
        "de gravar (responda sim/não).\n\n"
        "Por enquanto eu sempre lanço pra hoje e sem rateio - se precisar "
        "de rateio, ajuste direto no lancamentos_timesheet.csv."
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

    horas = extrair_horas(texto)
    if not horas:
        bot.reply_to(message, "Não achei a quantidade de horas na mensagem. Tenta algo tipo \"4h ADM Marketing\".")
        return

    resto = remover_horas(texto)
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
        "mes": mes_ano_atual(),
        "dia": dia_atual(),
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
        f"Dia {dia_atual()} de {mes_ano_atual()}\n"
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
    bot.reply_to(message, "Lançado no CSV. Quando quiser, rode o robô pra mandar pro Timesheet de verdade.")


def loop_lembrete() -> None:
    avisado_hoje = False
    ultimo_dia_checado = None

    while True:
        agora = datetime.now()

        if ultimo_dia_checado != agora.date():
            avisado_hoje = False
            ultimo_dia_checado = agora.date()

        if agora.hour >= HORA_LEMBRETE and not avisado_hoje:
            if not ja_lancou_hoje():
                try:
                    bot.send_message(
                        CHAT_ID_PERMITIDO,
                        "Você ainda não lançou nenhuma hora hoje no Timesheet. "
                        "Bora lançar? Manda tipo \"4h ADM Marketing\".",
                    )
                except Exception:
                    pass
            avisado_hoje = True

        time_module.sleep(600)


if __name__ == "__main__":
    print("Bot do Timesheet rodando. Ctrl+C para parar.")
    threading.Thread(target=loop_lembrete, daemon=True).start()
    bot.infinity_polling()
