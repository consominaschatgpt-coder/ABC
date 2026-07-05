"""
Logica de comparacao/selecao usada tanto pelo robo real (Playwright)
quanto pelo teste offline (sem navegador), para escolher a opcao mais
parecida numa lista suspensa em vez de travar pedindo ENTER as cegas.
"""

import difflib
import re

LIMIAR_AUTOMATICO = 0.5
LIMIAR_MINIMO = 0.3


def limpar(texto: str) -> str:
    return (texto or "").strip()


def simplificar(texto: str) -> str:
    texto = limpar(texto).lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto


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


def escolher_opcao(opcoes, valor_final, busca=""):
    """
    Escolhe, entre as opcoes visiveis na lista suspensa, a que mais se
    parece com valor_final. Sempre retorna a melhor candidata encontrada -
    nunca desiste no meio do caminho - junto com um score de 0 a 1 e o
    motivo da escolha, para quem chama decidir se aceita automaticamente
    ou pede conferencia manual.

    Retorna (opcao_escolhida, score, motivo) ou (None, 0.0, "sem_opcoes").
    """
    opcoes = [o for o in opcoes if limpar(o)]
    if not opcoes:
        return None, 0.0, "sem_opcoes"

    alvo = simplificar(valor_final)
    busca_s = simplificar(busca) or simplificar(termo_busca_padrao(valor_final))

    for op in opcoes:
        if simplificar(op) == alvo:
            return op, 1.0, "match_exato"

    contidas = [op for op in opcoes if alvo and alvo in simplificar(op)]
    if contidas:
        melhor = min(contidas, key=len)
        return melhor, 0.95, "contem_valor_final"

    candidatos = [op for op in opcoes if busca_s and busca_s in simplificar(op)]
    universo = candidatos or opcoes

    ordenadas = sorted(
        universo,
        key=lambda op: difflib.SequenceMatcher(None, simplificar(op), alvo).ratio(),
        reverse=True,
    )
    melhor = ordenadas[0]
    score = difflib.SequenceMatcher(None, simplificar(melhor), alvo).ratio()
    motivo = "melhor_da_busca" if candidatos else "melhor_geral"
    return melhor, score, motivo


def classificar(score: float) -> str:
    if score >= LIMIAR_AUTOMATICO:
        return "automatico"
    if score >= LIMIAR_MINIMO:
        return "baixa_confianca"
    return "falha"
