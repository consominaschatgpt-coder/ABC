"""
Logica de comparacao/selecao de texto usada tanto pelo robo (robo_timesheet_v7.py,
escolhendo a opcao certa na lista suspensa) quanto pelo bot do Telegram
(bot_telegram.py, entendendo qual Centro de custo/Rateio a pessoa quis dizer
numa mensagem livre). Fica num arquivo so' pra garantir que os dois entendam
o texto exatamente do mesmo jeito.
"""

import difflib
import re

LIMIAR_CONFIANCA = 0.70


def limpar(texto: str) -> str:
    return (texto or "").strip()


def simplificar(texto: str) -> str:
    texto = limpar(texto).lower()
    texto = texto.replace("_", " ")
    texto = re.sub(r"[^\wÀ-ÿ/.\- ]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def extrair_codigos(texto: str) -> set:
    """
    Numeros/codigos de contrato, OS ou ano que aparecem no texto (ex: "20.022/2020",
    "001/2024"). Usado para não confundir opções quase idênticas que só diferem
    no código - ex: "AMG CT 20.022/2020 - OS 001/2024" e "... OS 002/2024"
    têm 0.97 de parecença de texto, mas são contratos/OS diferentes.
    """
    return set(re.findall(r"\d+(?:[./-]\d+)*", simplificar(texto)))


def score_similaridade(a: str, b: str) -> float:
    a_s = simplificar(a)
    b_s = simplificar(b)
    if not a_s or not b_s:
        return 0.0

    if a_s == b_s:
        return 1.0

    if a_s in b_s or b_s in a_s:
        return 0.92

    base = difflib.SequenceMatcher(None, a_s, b_s).ratio()

    codigos_a = extrair_codigos(a)
    codigos_b = extrair_codigos(b)
    if codigos_a and codigos_b and codigos_a != codigos_b:
        # Mesmo prefixo/texto parecido, mas numero de contrato/OS/ano diferente -
        # penaliza bastante para não arriscar lançar no contrato/OS errado só
        # por parecença de texto (só entra aqui quando NÃO é caso de busca
        # abreviada/prefixo, que já foi resolvido acima pelo "in").
        base *= 0.5

    return base


def termo_busca_padrao(valor: str) -> str:
    valor = limpar(valor)
    if not valor:
        return ""

    partes = [p.strip() for p in valor.split("-") if p.strip()]
    if len(partes) >= 2:
        palavras = partes[1].split()
        if palavras:
            return " ".join(palavras[:2])

    palavras = valor.split()
    return " ".join(palavras[:2])


def melhor_correspondencia(opcoes, texto: str):
    """
    Acha, entre 'opcoes' (nomes reais do catalogo), a que mais se parece com
    'texto' (o que a pessoa escreveu). Retorna (opcao, score) ou (None, 0.0).
    """
    melhor = None
    melhor_score = 0.0

    for op in opcoes:
        s = score_similaridade(op, texto)
        if s > melhor_score:
            melhor = op
            melhor_score = s

    return melhor, melhor_score


def melhores_correspondencias(opcoes, texto: str, quantidade: int = 3):
    """
    Devolve ate' 'quantidade' opcoes mais parecidas com 'texto', da melhor
    pra pior, cada uma com seu score - usado quando a melhor sozinha nao
    tem confianca suficiente, pra oferecer escolha em vez de so' recusar.
    """
    pontuadas = [(op, score_similaridade(op, texto)) for op in opcoes]
    pontuadas.sort(key=lambda par: par[1], reverse=True)
    return pontuadas[:quantidade]
