"""
Robo de preenchimento do Timesheet (consominas.vindula.net) via Playwright.

Uso:
    python robo_timesheet_v1.py [caminho_do_csv] [--mes "2026 - Julho"]

O CSV precisa ter as colunas:
    mes,dia,centro_custo,rateio,horas,observacao

Quando "rateio" estiver vazio, o campo de rateio e' pulado (nem todo
lancamento tem rateio).

O campo "horas" e' digitado sem os dois pontos, ex: 0800 para 08:00.

IMPORTANTE sobre os seletores:
Os textos usados em get_by_label/get_by_role abaixo (ex: "Centro de custo",
"Rateio", "Adicionar hora") foram definidos a partir da descricao do fluxo
real da tela, mas o robo nunca teve acesso direto ao HTML do site (ele fica
atras de login corporativo). Se algum passo nao encontrar o elemento, o
robo avisa no terminal, pausa e deixa voce ajustar manualmente na tela -
depois e' so apertar ENTER para continuar com o proximo lancamento.

Para descobrir o seletor exato de um campo que nao funcionar, rode:
    python -m playwright codegen https://consominas.vindula.net/
Isso abre um navegador que grava os seletores reais conforme voce clica,
e voce copia o trecho certo para dentro deste arquivo.
"""

import argparse
import csv
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = "https://consominas.vindula.net/"
PROFILE_DIR = str(Path(__file__).parent / "perfil_timesheet")


def carregar_lancamentos(caminho_csv):
    lancamentos = []
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        colunas_esperadas = {"mes", "dia", "centro_custo", "rateio", "horas", "observacao"}
        if not colunas_esperadas.issubset(leitor.fieldnames or []):
            sys.exit(
                f"CSV invalido. Colunas esperadas: {sorted(colunas_esperadas)}. "
                f"Colunas encontradas: {leitor.fieldnames}"
            )
        for linha in leitor:
            lancamentos.append({
                "mes": linha["mes"].strip(),
                "dia": linha["dia"].strip(),
                "centro_custo": linha["centro_custo"].strip(),
                "rateio": linha["rateio"].strip(),
                "horas": linha["horas"].strip(),
                "observacao": linha["observacao"].strip(),
            })
    return lancamentos


def preencher_lancamento(page, lancamento, indice, total):
    print(f"\n[{indice}/{total}] Dia {lancamento['dia']} - {lancamento['centro_custo']} - {lancamento['horas']}")

    # Centro de custo
    page.get_by_label("Centro de custo").click()
    page.get_by_role("option", name=lancamento["centro_custo"], exact=False).click()

    # Rateio - so preenche quando existir. Muitos lancamentos nao tem rateio.
    if lancamento["rateio"]:
        page.get_by_label("Rateio").click()
        page.get_by_role("option", name=lancamento["rateio"], exact=False).click()
    else:
        print("  -> sem rateio, campo ignorado")

    # Dia do lancamento
    page.get_by_label("Dia").fill(lancamento["dia"])

    # Horas: digitado direto, sem os dois pontos (ex: 0800)
    page.get_by_label("Horas").fill(lancamento["horas"])

    # Observacoes
    page.get_by_label("Observações").fill(lancamento["observacao"])

    # Salvar - depois disso a tela volta para "Adicionar hora"
    page.get_by_role("button", name="Salvar").click()
    page.get_by_role("button", name="Adicionar hora").wait_for(state="visible", timeout=15000)
    print("  -> salvo")


def main():
    parser = argparse.ArgumentParser(description="Robo de preenchimento do Timesheet Consominas")
    parser.add_argument("csv", nargs="?", default="lancamentos_timesheet.csv", help="Caminho do CSV de lancamentos")
    parser.add_argument(
        "--mes",
        default=None,
        help="Mes a selecionar na tela, ex: '2026 - Julho'. Se nao informado, usa o mes da primeira linha do CSV.",
    )
    args = parser.parse_args()

    caminho_csv = Path(args.csv)
    if not caminho_csv.exists():
        sys.exit(f"Arquivo nao encontrado: {caminho_csv}")

    lancamentos = carregar_lancamentos(caminho_csv)
    if not lancamentos:
        sys.exit("CSV vazio, nada para lancar.")

    mes = args.mes or lancamentos[0]["mes"]
    total = len(lancamentos)

    with sync_playwright() as p:
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            channel="msedge",
        )
        page = contexto.pages[0] if contexto.pages else contexto.new_page()
        page.goto(URL)

        input(
            "\nFaca login manualmente na intranet (o perfil fica salvo, "
            "da segunda vez em diante isso pode nao ser necessario).\n"
            "Quando estiver na tela inicial, volte aqui e aperte ENTER..."
        )

        page.get_by_role("link", name="Time Sheet").click()
        page.get_by_text(mes, exact=False).click()
        page.get_by_role("button", name="Adicionar hora").click()

        for indice, lancamento in enumerate(lancamentos, start=1):
            try:
                preencher_lancamento(page, lancamento, indice, total)
            except PlaywrightTimeoutError as erro:
                print(f"  !! Nao encontrei um campo no lancamento {indice}: {erro}")
                input("  Ajuste manualmente na tela e aperte ENTER para seguir com o proximo lancamento...")

        print("\nTodos os lancamentos foram processados.")
        input("Aperte ENTER para fechar o navegador...")
        contexto.close()


if __name__ == "__main__":
    main()
