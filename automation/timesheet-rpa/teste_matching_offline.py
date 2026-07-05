"""
Teste offline do algoritmo de escolha de opcao (matching.py) - sem abrir
navegador nenhum.

Serve para responder, antes de rodar contra a intranet real: o robo
consegue achar a opcao certa de Centro de custo mesmo quando o texto do
CSV nao bate 100% com o texto exibido na tela (abreviacao, sem acento,
etc)? Roda em duas partes:

  Parte 1 - Casamento direto: usa lancamentos_semana_simulada.csv, onde o
  centro_custo ja esta escrito exatamente como aparece na lista real. E'
  o caso feliz, deveria dar 100%.

  Parte 2 - Estresse com texto imperfeito: usa variacoes propositalmente
  erradas/abreviadas (simulando o que uma pessoa digitaria de cabeca) e
  mede se o algoritmo ainda acha a opcao certa e com que score.
"""

from pathlib import Path

from matching import escolher_opcao, classificar, LIMIAR_AUTOMATICO
from csv_lancamentos import carregar_csv

ARQUIVO_OPCOES = "opcoes_centro_de_custo_exemplo.txt"
ARQUIVO_SEMANA = "lancamentos_semana_simulada.csv"

# Variacoes propositalmente imperfeitas do centro_custo, simulando o que
# uma pessoa digitaria de cabeca num CSV pessoal sem checar a grafia exata
# do sistema. Usadas so' neste teste, para estressar o algoritmo.
VARIACOES_IMPERFEITAS = {
    "ADM Atividades Adm": "ADM Atividades Administrativas",
    "ADM COMERCIAL": "Adm comercial",
    "ADM LOGISTICA": "Logistica",
    "ADM MARKETING": "marketing adm",
    "AGA CT 15140/2025 - CB": "AGA 15140/2025",
    "BH AIRPORT CT 4600084150/2024": "BH Airport 4600084150",
    "MRN 3686 BAQ": "MRN 3686",
    "ADM Compensação de Banco de Horas": "Compensacao banco de horas",
    "ADM DESENVOLVIMENTO HUMANO E SOCIAL": "Desenvolvimento Humano",
}


def carregar_opcoes() -> list:
    caminho = Path(ARQUIVO_OPCOES)
    linhas = [linha.strip() for linha in caminho.read_text(encoding="utf-8").splitlines()]
    return [linha for linha in linhas if linha and not linha.startswith("#")]


def testar(opcoes: list, valor_testado: str, busca: str, esperado: str, rotulo: str) -> bool:
    """
    Roda o matching com 'valor_testado' (o que estaria no CSV) e confere
    se o resultado bate com 'esperado' (a opção real que deveria ser
    escolhida na tela).
    """
    escolhida, score, motivo = escolher_opcao(opcoes, valor_testado, busca)
    classe = classificar(score)
    ok = escolhida == esperado
    resultado = "OK" if ok else "DIVERGIU"

    print(f"[{rotulo}] testado={valor_testado!r} busca={busca!r} esperado={esperado!r}")
    print(f"    escolhido={escolhida!r} score={score:.2f} motivo={motivo} classe={classe} -> {resultado}")

    return ok and classe != "falha"


def main() -> None:
    opcoes = carregar_opcoes()
    print(f"Opções de centro de custo carregadas: {len(opcoes)}\n")

    lancamentos = carregar_csv(ARQUIVO_SEMANA)
    print(f"Lançamentos da semana simulada: {len(lancamentos)}\n")

    print("=" * 100)
    print("PARTE 1 - Casamento direto (CSV com o valor exatamente como aparece na tela)")
    print("=" * 100)

    acertos_diretos = 0
    for linha in lancamentos:
        ok = testar(
            opcoes,
            linha["centro_custo"],
            linha["centro_custo_busca"],
            linha["centro_custo"],
            f"dia {linha['dia']}",
        )
        acertos_diretos += int(ok)

    total = len(lancamentos)
    print(f"\nAcerto direto: {acertos_diretos}/{total} ({acertos_diretos / total:.0%})\n")

    print("=" * 100)
    print("PARTE 2 - Estresse com variações imperfeitas (typos/abreviações)")
    print("=" * 100)

    acertos_imperfeitos = 0
    total_imperfeitos = 0
    for valor_final, variacao in VARIACOES_IMPERFEITAS.items():
        if valor_final not in opcoes:
            continue
        total_imperfeitos += 1
        ok = testar(opcoes, variacao, "", valor_final, "variação")
        acertos_imperfeitos += int(ok)

    if total_imperfeitos:
        print(
            f"\nAcerto com texto imperfeito: {acertos_imperfeitos}/{total_imperfeitos} "
            f"({acertos_imperfeitos / total_imperfeitos:.0%})"
        )

    print(f"\nLimiar automático configurado: {LIMIAR_AUTOMATICO:.0%}")


if __name__ == "__main__":
    main()
