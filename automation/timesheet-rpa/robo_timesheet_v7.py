"""
Robô Local De Preenchimento Do Timesheet
Versão 7

Herda tudo da v6 (recomeça pela seleção do mês a cada lançamento, porque a
intranet volta para o calendário em branco após salvar) e adiciona:

- Escolha de opção sempre pela mais parecida (ver matching.py), em vez de
  desistir e apertar ENTER às cegas na lista suspensa.
- Modo rápido: não pausa pedindo ENTER a cada lançamento. Só pausa quando
  um campo obrigatório não tem nenhuma opção parecida o suficiente
  (falha real), o que precisa de atenção manual mesmo.
- Relatório final com o score de confiança de cada campo preenchido, para
  revisar depois de tudo pronto em vez de conferir lançamento por
  lançamento.
"""

import csv
from pathlib import Path
from typing import Dict, List

from playwright.sync_api import sync_playwright, Page

from matching import escolher_opcao, classificar, limpar, termo_busca_padrao
from csv_lancamentos import carregar_csv


URL = "https://consominas.vindula.net/"
ARQUIVO_CSV = "lancamentos_timesheet.csv"
ARQUIVO_RELATORIO = "relatorio_execucao.csv"
PERFIL_NAVEGADOR = "perfil_timesheet_robo"
CANAL_NAVEGADOR = "msedge"

MODO_ASSISTIDO = True
MODO_RAPIDO = True
ESPERA_CARREGAR_RATEIO_MS = 3500


def pausa(mensagem: str) -> None:
    print("\n" + "=" * 100)
    print(mensagem)
    print("=" * 100)
    input("Pressione ENTER no terminal para continuar...")


def abrir_timesheet(page: Page) -> None:
    print("Abrindo Time Sheet...")

    try:
        page.get_by_text("Time Sheet", exact=True).click(timeout=12000)
    except Exception:
        page.get_by_text("Time Sheet", exact=False).first.click(timeout=12000)

    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)


def selecionar_mes(page: Page, mes: str) -> None:
    print(f"Selecionando mês: {mes}")

    selects = page.locator("select")
    total = selects.count()

    for i in range(total):
        select = selects.nth(i)
        try:
            opcoes = select.locator("option").all_inner_texts()
            if any(mes.lower() in opcao.lower() for opcao in opcoes):
                select.select_option(label=mes)
                page.wait_for_timeout(1800)
                return
        except Exception:
            pass

    try:
        page.get_by_text("Escolha o ano e mês para o registro", exact=False).first.wait_for(state="visible", timeout=6000)
        campo_calendario = page.locator("select").first
        campo_calendario.click(timeout=5000)
        page.wait_for_timeout(500)
        page.get_by_text(mes, exact=False).first.click(timeout=7000)
        page.wait_for_timeout(1800)
        return
    except Exception:
        pass

    if MODO_ASSISTIDO:
        pausa(f"Não consegui selecionar o mês '{mes}'. Selecione manualmente na tela e volte aqui.")
        return

    raise Exception(f"Não consegui selecionar o mês '{mes}'.")


def aguardar_timesheet(page: Page) -> None:
    print("Aguardando tela do Timesheet...")

    try:
        page.get_by_text("Escolha o Calendário", exact=False).first.wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(800)
        return
    except Exception:
        pass

    try:
        page.get_by_text("Timesheet", exact=False).first.wait_for(state="visible", timeout=8000)
        page.wait_for_timeout(800)
        return
    except Exception:
        pass

    if MODO_ASSISTIDO:
        pausa("Não consegui confirmar a tela do Timesheet. Se estiver na tela do Timesheet, pressione ENTER.")
        return


def aguardar_botao_adicionar(page: Page) -> None:
    print("Aguardando botão Adicionar hora...")

    try:
        page.get_by_text("Adicionar hora", exact=False).first.wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(800)
        return
    except Exception:
        pass

    if MODO_ASSISTIDO:
        pausa("Não encontrei o botão Adicionar hora. Selecione o mês manualmente até ele aparecer e volte aqui.")
        return


def preparar_novo_lancamento(page: Page, mes: str) -> None:
    aguardar_timesheet(page)
    selecionar_mes(page, mes)
    aguardar_botao_adicionar(page)

    print("Clicando em Adicionar hora...")
    try:
        page.get_by_text("Adicionar hora", exact=False).first.click(timeout=15000)
    except Exception:
        if MODO_ASSISTIDO:
            pausa("Não consegui clicar em Adicionar hora. Clique manualmente e volte aqui.")
            return
        raise

    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(1200)


def clicar_campo_por_label(page: Page, label: str) -> None:
    label_el = page.get_by_text(label, exact=False).first
    box = label_el.bounding_box(timeout=6000)

    if not box:
        raise Exception(f"Não encontrei o label '{label}'.")

    page.mouse.click(box["x"] + 110, box["y"] + 48)
    page.wait_for_timeout(650)


def textos_opcoes_visiveis(page: Page) -> List[str]:
    seletores = [
        ".select2-results__option:visible",
        ".selectize-dropdown .option:visible",
        ".dropdown-menu li:visible",
        ".chosen-results li:visible",
        "[role='option']:visible",
        ".ui-menu-item:visible",
        "li:visible",
    ]

    textos = []
    vistos = set()

    for seletor in seletores:
        try:
            loc = page.locator(seletor)
            count = min(loc.count(), 80)
            for i in range(count):
                txt = limpar(loc.nth(i).inner_text(timeout=700))
                if txt and txt not in vistos:
                    vistos.add(txt)
                    textos.append(txt)
        except Exception:
            pass

    return textos


def clicar_opcao_por_texto(page: Page, texto: str) -> bool:
    seletores = [
        ".select2-results__option",
        ".selectize-dropdown .option",
        ".dropdown-menu li",
        ".chosen-results li",
        "[role='option']",
        ".ui-menu-item",
        "li",
    ]

    for seletor in seletores:
        try:
            loc = page.locator(seletor).filter(has_text=texto).first
            if loc.count() > 0:
                loc.click(timeout=5000)
                page.wait_for_timeout(800)
                return True
        except Exception:
            pass

    try:
        page.get_by_text(texto, exact=True).first.click(timeout=5000)
        page.wait_for_timeout(800)
        return True
    except Exception:
        pass

    try:
        page.get_by_text(texto, exact=False).first.click(timeout=5000)
        page.wait_for_timeout(800)
        return True
    except Exception:
        pass

    return False


def selecionar_lista_inteligente(
    page: Page,
    label: str,
    valor_final: str,
    termo_busca: str,
    relatorio: List[Dict[str, str]],
    obrigatorio: bool = True,
) -> None:
    valor_final = limpar(valor_final)
    termo_busca = limpar(termo_busca) or termo_busca_padrao(valor_final)

    if not valor_final:
        if obrigatorio:
            raise ValueError(f"Campo obrigatório vazio: {label}")
        print(f"{label}: vazio. Pulando.")
        relatorio.append({"campo": label, "esperado": "", "escolhido": "", "score": "", "classe": "vazio"})
        return

    print(f"Selecionando {label}")
    print(f"  Busca digitada: {termo_busca}")
    print(f"  Valor esperado: {valor_final}")

    try:
        clicar_campo_por_label(page, label)

        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.wait_for_timeout(250)
        page.keyboard.type(termo_busca, delay=35)
        page.wait_for_timeout(1500)

        opcoes = textos_opcoes_visiveis(page)
        print(f"  Opções visíveis encontradas: {len(opcoes)}")

        escolhida, score, motivo = escolher_opcao(opcoes, valor_final, termo_busca)
        classe = classificar(score)
        print(f"  Escolhida: {escolhida!r} | score={score:.2f} | motivo={motivo} | classe={classe}")

        relatorio.append({
            "campo": label,
            "esperado": valor_final,
            "escolhido": escolhida or "",
            "score": f"{score:.2f}",
            "classe": classe,
        })

        if classe in ("automatico", "baixa_confianca") and escolhida:
            if clicar_opcao_por_texto(page, escolhida):
                return
            print(f"  Não consegui clicar em '{escolhida}', tentando ENTER na opção destacada...")

        if classe == "falha" or not escolhida:
            raise Exception(
                f"Nenhuma opção parecida o suficiente com '{valor_final}' (melhor score={score:.2f})"
            )

        page.keyboard.press("Enter")
        page.wait_for_timeout(900)
        return

    except Exception as erro:
        print(f"Falha automática em {label}: {erro}")

    if MODO_ASSISTIDO:
        pausa(
            f"Não consegui selecionar automaticamente o campo '{label}'.\n\n"
            f"Escolha manualmente na tela:\n{valor_final}\n\n"
            "Depois volte ao terminal."
        )
        return

    raise Exception(f"Não consegui selecionar '{valor_final}' no campo '{label}'.")


def selecionar_dia(page: Page, dia: str) -> None:
    dia = limpar(dia).zfill(2)
    print(f"Selecionando dia: {dia}")

    try:
        select_dia = page.locator("#id_dia")
        select_dia.select_option(label=dia, timeout=4000)
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    try:
        select_dia = page.locator("select[name='dia']")
        select_dia.select_option(label=dia, timeout=4000)
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    try:
        select_dia = page.locator("xpath=(//*[contains(normalize-space(), 'Dia')][1]/following::select[1])")
        select_dia.select_option(label=dia, timeout=7000)
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    if MODO_ASSISTIDO:
        pausa(f"Não consegui selecionar o Dia {dia}. Selecione manualmente na tela.")
        return

    raise Exception(f"Não consegui selecionar o dia {dia}.")


def preencher_horas(page: Page, horas: str) -> None:
    horas = limpar(horas).replace(":", "")
    print(f"Preenchendo horas: {horas}")

    seletores = [
        "#id_horario",
        "input[name='horario']",
        "input[type='time']",
    ]

    ultimo_erro = None

    for seletor in seletores:
        try:
            campo = page.locator(seletor).first
            campo.wait_for(state="visible", timeout=5000)
            campo.scroll_into_view_if_needed(timeout=5000)
            campo.click(timeout=5000)

            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.wait_for_timeout(250)
            page.keyboard.type(horas, delay=90)
            page.wait_for_timeout(500)
            return

        except Exception as erro:
            ultimo_erro = erro
            continue

    print(f"Falha automática no campo de horas: {ultimo_erro}")

    if MODO_ASSISTIDO:
        pausa(f"Não consegui preencher horas. Digite manualmente: {horas}")
        return

    raise Exception("Não consegui preencher Quantidade de horas.")


def preencher_observacao(page: Page, texto: str) -> None:
    texto = limpar(texto)
    print("Preenchendo Observações...")

    try:
        frame = page.frame_locator("iframe.cke_wysiwyg_frame").first
        body = frame.locator("body")
        body.click(timeout=7000)
        body.press("Control+A")
        body.press("Backspace")
        body.type(texto, delay=5)
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    try:
        editor = page.locator("[contenteditable='true']:visible").first
        editor.click(timeout=7000)
        editor.press("Control+A")
        editor.press("Backspace")
        editor.type(texto, delay=5)
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    try:
        textarea = page.locator("textarea:visible").first
        textarea.fill(texto, timeout=7000)
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    if MODO_ASSISTIDO:
        pausa(f"Não consegui preencher Observações. Copie manualmente:\n\n{texto}")
        return

    raise Exception("Não consegui preencher Observações.")


def salvar(page: Page) -> None:
    if not MODO_RAPIDO:
        pausa(
            "Confira se Centro de custo, Rateio, Dia, Horas e Observações estão corretos.\n"
            "Se estiver certo, pressione ENTER e o robô clicará em Salvar."
        )

    print("Salvando...")

    candidatos = [
        "input[type='submit'][value='Salvar']",
        "#submit-id-submit",
        "button:has-text('Salvar')",
        "text=Salvar",
    ]

    for seletor in candidatos:
        try:
            page.locator(seletor).first.click(timeout=5000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            aguardar_timesheet(page)
            return
        except Exception:
            continue

    if MODO_ASSISTIDO:
        pausa("Não consegui clicar em Salvar. Clique manualmente e depois volte aqui.")
        aguardar_timesheet(page)
        return

    raise Exception("Não consegui salvar.")


def lancar(page: Page, linha: Dict[str, str], atual: int, total: int, relatorio: List[Dict[str, str]]) -> None:
    print("\n" + "-" * 100)
    print(f"Lançamento {atual}/{total}")
    print(f"Dia: {linha['dia']}")
    print(f"Centro de custo: {linha['centro_custo']} | Busca: {linha['centro_custo_busca']}")
    print(f"Rateio: {linha['rateio'] or '(sem rateio)'} | Busca: {linha['rateio_busca'] or '(vazio)'}")
    print(f"Horas: {linha['horas']}")
    print("-" * 100)

    preparar_novo_lancamento(page, linha["mes"])

    selecionar_lista_inteligente(
        page,
        label="Centro de custo",
        valor_final=linha["centro_custo"],
        termo_busca=linha["centro_custo_busca"],
        relatorio=relatorio,
        obrigatorio=True,
    )

    if linha["rateio"]:
        print("Aguardando carregar opções de Rateio...")
        page.wait_for_timeout(ESPERA_CARREGAR_RATEIO_MS)

        selecionar_lista_inteligente(
            page,
            label="Rateio",
            valor_final=linha["rateio"],
            termo_busca=linha["rateio_busca"],
            relatorio=relatorio,
            obrigatorio=False,
        )
    else:
        print("Sem rateio. Pulando Rateio.")

    selecionar_dia(page, linha["dia"])
    preencher_horas(page, linha["horas"])
    preencher_observacao(page, linha["observacao"])
    salvar(page)


def salvar_relatorio(relatorio: List[Dict[str, str]]) -> None:
    if not relatorio:
        return

    caminho = Path(ARQUIVO_RELATORIO)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=["campo", "esperado", "escolhido", "score", "classe"])
        escritor.writeheader()
        escritor.writerows(relatorio)

    total = len(relatorio)
    automaticos = sum(1 for r in relatorio if r["classe"] == "automatico")
    baixa_confianca = sum(1 for r in relatorio if r["classe"] == "baixa_confianca")
    falhas = sum(1 for r in relatorio if r["classe"] == "falha")

    print("\n" + "=" * 100)
    print(f"Relatório salvo em {caminho.resolve()}")
    print(f"Campos preenchidos: {total}")
    print(f"  Automático (alta confiança): {automaticos}")
    print(f"  Baixa confiança (revisar):   {baixa_confianca}")
    print(f"  Falha:                       {falhas}")
    print("=" * 100)


def main() -> None:
    linhas = carregar_csv(ARQUIVO_CSV)
    relatorio: List[Dict[str, str]] = []

    print("Robô Local De Timesheet - Versão 7")
    print(f"Arquivo: {ARQUIVO_CSV}")
    print(f"Lançamentos: {len(linhas)}")
    print(f"Modo rápido: {'ligado' if MODO_RAPIDO else 'desligado'}")

    with sync_playwright() as p:
        try:
            contexto = p.chromium.launch_persistent_context(
                user_data_dir=PERFIL_NAVEGADOR,
                headless=False,
                channel=CANAL_NAVEGADOR,
                viewport={"width": 1600, "height": 900},
                slow_mo=120,
            )
        except Exception:
            print("Não consegui abrir pelo Edge. Abrindo Chromium do Playwright.")
            contexto = p.chromium.launch_persistent_context(
                user_data_dir=PERFIL_NAVEGADOR,
                headless=False,
                viewport={"width": 1600, "height": 900},
                slow_mo=120,
            )

        page = contexto.new_page()
        page.goto(URL, wait_until="domcontentloaded")

        pausa("Faça login na intranet. Quando estiver na página inicial, volte aqui.")

        abrir_timesheet(page)

        pausa("Confira se você está na tela do Timesheet. Se estiver, volte aqui para iniciar os lançamentos.")

        for i, linha in enumerate(linhas, start=1):
            try:
                lancar(page, linha, i, len(linhas), relatorio)
            except Exception as erro:
                print("\nERRO")
                print(f"Lançamento: {i}")
                print(f"Dia: {linha.get('dia')}")
                print(f"Centro de custo: {linha.get('centro_custo')}")
                print(f"Erro: {erro}")

                if MODO_ASSISTIDO:
                    pausa("O navegador ficará aberto. Confira a tela e depois volte aqui.")
                    break
                raise

        salvar_relatorio(relatorio)

        print("\nProcesso finalizado.")
        pausa("Confira a tela. Depois volte aqui para fechar o navegador.")
        contexto.close()


if __name__ == "__main__":
    main()
