"""
Leitura e validação do CSV de lançamentos. Sem dependência de Playwright,
para poder ser usado tanto pelo robô real quanto pelo teste offline de
matching.
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional

from matching import limpar, termo_busca_padrao

ARQUIVO_CSV_PADRAO = "lancamentos_timesheet.csv"


def carregar_csv(caminho_csv: Optional[str] = None) -> List[Dict[str, str]]:
    caminho = Path(caminho_csv or ARQUIVO_CSV_PADRAO)

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho.resolve()}")

    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))

    if not linhas:
        raise ValueError("CSV vazio.")

    colunas_minimas = {"mes", "dia", "centro_custo", "rateio", "horas", "observacao"}
    faltantes = colunas_minimas - set(linhas[0].keys())

    if faltantes:
        raise ValueError(f"Colunas faltando no CSV: {', '.join(sorted(faltantes))}")

    tratadas = []

    for i, linha in enumerate(linhas, start=1):
        centro_custo = limpar(linha.get("centro_custo", ""))
        rateio = limpar(linha.get("rateio", ""))

        item = {
            "mes": limpar(linha.get("mes", "")),
            "dia": limpar(linha.get("dia", "")).zfill(2),
            "centro_custo": centro_custo,
            "centro_custo_busca": limpar(linha.get("centro_custo_busca", "")) or termo_busca_padrao(centro_custo),
            "rateio": rateio,
            "rateio_busca": limpar(linha.get("rateio_busca", "")) or termo_busca_padrao(rateio),
            "horas": limpar(linha.get("horas", "")).replace(":", ""),
            "observacao": limpar(linha.get("observacao", "")),
        }

        if not item["mes"]:
            raise ValueError(f"Linha {i}: mês vazio.")
        if not item["dia"]:
            raise ValueError(f"Linha {i}: dia vazio.")
        if not item["centro_custo"]:
            raise ValueError(f"Linha {i}: centro_custo vazio.")
        if not item["horas"]:
            raise ValueError(f"Linha {i}: horas vazio.")
        if not item["observacao"]:
            raise ValueError(f"Linha {i}: observacao vazia.")

        tratadas.append(item)

    return tratadas
