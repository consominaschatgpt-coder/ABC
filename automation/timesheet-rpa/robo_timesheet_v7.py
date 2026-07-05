"""
Robô Local De Preenchimento Do Timesheet
Versão 7

Foco:
- Sem ENTER a cada lançamento.
- Vários lançamentos no mesmo dia.
- Base local DuckDB.
- Fuzzy match com limite mínimo de 70%, penalizando parecença de texto
  quando o número de contrato/OS/ano é diferente (evita confundir opções
  quase idênticas, ex: "OS 001/2024" com "OS 002/2024").
- Espera adaptativa pelo carregamento do Rateio (não trava no tempo
  máximo fixo quando a tela responde mais rápido).
- Log de execução.
- Não salva quando a confiança da seleção for baixa.

Importante:
- Faça login manualmente quando o navegador abrir.
- Depois disso, o robô detecta a tela e segue sozinho.
"""

import csv
import difflib
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import duckdb
from playwright.sync_api import sync_playwright, Page


URL = "https://consominas.vindula.net/"
ARQUIVO_LANCAMENTOS = "lancamentos_timesheet.csv"
ARQUIVO_CATALOGO = "catalogo_opcoes.csv"
BANCO_DUCKDB = "timesheet_robo.duckdb"
LOG_EXECUCAO = "log_execucao_timesheet.csv"
PERFIL_NAVEGADOR = "perfil_timesheet_robo"
CANAL_NAVEGADOR = "msedge"

LIMIAR_CONFIANCA = 0.70
SALVAR_AUTOMATICAMENTE = True
ESPERA_CARREGAR_RATEIO_MS = 3000
TEMPO_MAXIMO_LOGIN_SEGUNDOS = 180


class SelecaoInsegura(Exception):
    pass


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


def agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def inicializar_banco() -> None:
    con = duckdb.connect(BANCO_DUCKDB)

    con.execute("""
        CREATE TABLE IF NOT EXISTS catalogo_opcoes (
            tipo VARCHAR,
            nome VARCHAR,
            busca VARCHAR,
            apelidos VARCHAR
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER,
            mes VARCHAR,
            dia VARCHAR,
            centro_custo VARCHAR,
            centro_custo_busca VARCHAR,
            rateio VARCHAR,
            rateio_busca VARCHAR,
            horas VARCHAR,
            observacao VARCHAR,
            status VARCHAR,
            erro VARCHAR,
            atualizado_em VARCHAR
        )
    """)

    con.execute("DELETE FROM catalogo_opcoes")

    if Path(ARQUIVO_CATALOGO).exists():
        con.execute(f"""
            INSERT INTO catalogo_opcoes
            SELECT * FROM read_csv_auto('{ARQUIVO_CATALOGO}', header=true, ignore_errors=true)
        """)

    # Recarrega lançamentos do CSV a cada execução.
    con.execute("DELETE FROM lancamentos")

    with open(ARQUIVO_LANCAMENTOS, "r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        linhas = list(leitor)

    for idx, linha in enumerate(linhas, start=1):
        centro = limpar(linha.get("centro_custo", ""))
        rateio = limpar(linha.get("rateio", ""))

        con.execute("""
            INSERT INTO lancamentos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            idx,
            limpar(linha.get("mes", "")),
            limpar(linha.get("dia", "")).zfill(2),
            centro,
            limpar(linha.get("centro_custo_busca", "")) or buscar_termo_no_catalogo("centro_custo", centro) or termo_busca_padrao(centro),
            rateio,
            limpar(linha.get("rateio_busca", "")) or buscar_termo_no_catalogo("rateio", rateio) or termo_busca_padrao(rateio),
            limpar(linha.get("horas", "")).replace(":", ""),
            limpar(linha.get("observacao", "")),
            "pendente",
            "",
            agora(),
        ])

    con.close()


def buscar_termo_no_catalogo(tipo: str, nome: str) -> str:
    if not Path(BANCO_DUCKDB).exists():
        return ""

    try:
        con = duckdb.connect(BANCO_DUCKDB)
        rows = con.execute(
            "SELECT nome, busca FROM catalogo_opcoes WHERE tipo = ?",
            [tipo],
        ).fetchall()
        con.close()
    except Exception:
        return ""

    melhor_busca = ""
    melhor_score = 0.0

    for nome_cat, busca_cat in rows:
        s = score_similaridade(nome, nome_cat)
        if s > melhor_score:
            melhor_score = s
            melhor_busca = busca_cat or ""

    if melhor_score >= LIMIAR_CONFIANCA:
        return melhor_busca

    return ""


def obter_lancamentos_pendentes() -> List[Dict[str, str]]:
    con = duckdb.connect(BANCO_DUCKDB)
    rows = con.execute("""
        SELECT id, mes, dia, centro_custo, centro_custo_busca, rateio, rateio_busca, horas, observacao
        FROM lancamentos
        WHERE status = 'pendente'
        ORDER BY id
    """).fetchall()
    con.close()

    dados = []
    for r in rows:
        dados.append({
            "id": r[0],
            "mes": r[1],
            "dia": r[2],
            "centro_custo": r[3],
            "centro_custo_busca": r[4],
            "rateio": r[5],
            "rateio_busca": r[6],
            "horas": r[7],
            "observacao": r[8],
        })
    return dados


def atualizar_status(id_lancamento: int, status: str, erro: str = "") -> None:
    con = duckdb.connect(BANCO_DUCKDB)
    con.execute("""
        UPDATE lancamentos
        SET status = ?, erro = ?, atualizado_em = ?
        WHERE id = ?
    """, [status, erro, agora(), id_lancamento])
    con.close()


def escrever_log(id_lancamento: int, status: str, mensagem: str, extra: str = "") -> None:
    novo = not Path(LOG_EXECUCAO).exists()
    with open(LOG_EXECUCAO, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["data_hora", "id_lancamento", "status", "mensagem", "extra"])
        w.writerow([agora(), id_lancamento, status, mensagem, extra])


def aguardar_login(page: Page) -> None:
    print("Aguardando login manual na intranet...")

    limite = time.time() + TEMPO_MAXIMO_LOGIN_SEGUNDOS

    while time.time() < limite:
        try:
            if page.get_by_text("Time Sheet", exact=False).first.is_visible(timeout=1000):
                print("Login detectado.")
                return
        except Exception:
            pass

        try:
            if page.get_by_text("Home", exact=False).first.is_visible(timeout=1000):
                print("Tela inicial detectada.")
                return
        except Exception:
            pass

        time.sleep(1)

    print("Não consegui detectar o login automaticamente.")
    input("Se você já está logado, pressione ENTER para continuar...")


def abrir_timesheet(page: Page) -> None:
    print("Abrindo Time Sheet...")

    try:
        page.get_by_text("Time Sheet", exact=True).click(timeout=12000)
    except Exception:
        page.get_by_text("Time Sheet", exact=False).first.click(timeout=12000)

    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(1200)


def aguardar_timesheet(page: Page) -> None:
    try:
        page.get_by_text("Escolha o Calendário", exact=False).first.wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    try:
        page.get_by_text("Timesheet", exact=False).first.wait_for(state="visible", timeout=8000)
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    abrir_timesheet(page)


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
                page.wait_for_timeout(1500)
                return
        except Exception:
            pass

    # Fallback manual por clique no primeiro select.
    campo = page.locator("select").first
    campo.select_option(label=mes)
    page.wait_for_timeout(1500)


def aguardar_botao_adicionar(page: Page) -> None:
    page.get_by_text("Adicionar hora", exact=False).first.wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(500)


def aguardar_rateio_carregar(page: Page) -> None:
    """
    Depois de escolher o Centro de custo, a tela busca no servidor os
    Rateios validos para ele. Em vez de sempre esperar o tempo fixo
    (ESPERA_CARREGAR_RATEIO_MS), espera so' ate a rede ficar ociosa -
    normalmente mais rapido - com o mesmo tempo maximo como teto de
    seguranca se a rede nao ficar ociosa a tempo.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=ESPERA_CARREGAR_RATEIO_MS)
    except Exception:
        pass


def preparar_lancamento(page: Page, mes: str) -> None:
    aguardar_timesheet(page)
    selecionar_mes(page, mes)
    aguardar_botao_adicionar(page)

    print("Clicando em Adicionar hora...")
    page.get_by_text("Adicionar hora", exact=False).first.click(timeout=15000)
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(1000)


def clicar_campo_por_label(page: Page, label: str) -> None:
    label_el = page.get_by_text(label, exact=False).first
    box = label_el.bounding_box(timeout=7000)

    if not box:
        raise Exception(f"Não encontrei o label '{label}'.")

    page.mouse.click(box["x"] + 110, box["y"] + 48)
    page.wait_for_timeout(500)


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
            count = min(loc.count(), 120)
            for i in range(count):
                txt = limpar(loc.nth(i).inner_text(timeout=600))
                if txt and txt not in vistos and len(txt) <= 180:
                    vistos.add(txt)
                    textos.append(txt)
        except Exception:
            pass

    return textos


def melhor_opcao(opcoes: List[str], valor_final: str, busca: str) -> Tuple[Optional[str], float]:
    if not opcoes:
        return None, 0.0

    alvo = limpar(valor_final)
    busca = limpar(busca)

    melhor = None
    melhor_score = 0.0

    for op in opcoes:
        s1 = score_similaridade(op, alvo)
        s2 = score_similaridade(op, busca) * 0.92 if busca else 0.0
        s = max(s1, s2)

        if s > melhor_score:
            melhor = op
            melhor_score = s

    return melhor, melhor_score


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
                page.wait_for_timeout(700)
                return True
        except Exception:
            pass

    try:
        page.get_by_text(texto, exact=True).first.click(timeout=5000)
        page.wait_for_timeout(700)
        return True
    except Exception:
        pass

    return False


def gerar_buscas(valor_final: str, busca_csv: str) -> List[str]:
    termos = []
    for t in [busca_csv, termo_busca_padrao(valor_final)]:
        t = limpar(t)
        if t and t not in termos:
            termos.append(t)

    palavras = valor_final.split()
    if palavras:
        t = palavras[0]
        if t not in termos:
            termos.append(t)

    if len(palavras) >= 2:
        t = " ".join(palavras[:2])
        if t not in termos:
            termos.append(t)

    return termos


def selecionar_lista_inteligente(page: Page, label: str, valor_final: str, termo_busca: str, obrigatorio: bool = True) -> str:
    valor_final = limpar(valor_final)

    if not valor_final:
        if obrigatorio:
            raise ValueError(f"Campo obrigatório vazio: {label}")
        return ""

    print(f"Selecionando {label}: {valor_final}")

    melhor_global = None
    score_global = 0.0
    opcoes_global = []

    for busca in gerar_buscas(valor_final, termo_busca):
        print(f"  Tentando busca: {busca}")

        clicar_campo_por_label(page, label)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.wait_for_timeout(200)
        page.keyboard.type(busca, delay=30)
        page.wait_for_timeout(1200)

        opcoes = textos_opcoes_visiveis(page)
        opcoes_global.extend(opcoes)

        escolhida, score = melhor_opcao(opcoes, valor_final, busca)

        print(f"  Opções visíveis: {len(opcoes)} | Melhor: {escolhida} | Confiança: {score:.0%}")

        if escolhida and score >= LIMIAR_CONFIANCA:
            if clicar_opcao_por_texto(page, escolhida):
                return escolhida

        if score > score_global:
            melhor_global = escolhida
            score_global = score

        # Fecha dropdown antes da próxima tentativa.
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    extra = f"Melhor opção: {melhor_global} | Confiança: {score_global:.0%} | Opções: {opcoes_global[:10]}"
    raise SelecaoInsegura(
        f"Seleção insegura em {label}. Esperado: {valor_final}. {extra}"
    )


def selecionar_dia(page: Page, dia: str) -> None:
    dia = limpar(dia).zfill(2)
    print(f"Selecionando dia: {dia}")

    for seletor in ["#id_dia", "select[name='dia']"]:
        try:
            page.locator(seletor).select_option(label=dia, timeout=5000)
            page.wait_for_timeout(300)
            return
        except Exception:
            pass

    raise Exception(f"Não consegui selecionar o dia {dia}")


def preencher_horas(page: Page, horas: str) -> None:
    horas = limpar(horas).replace(":", "")
    print(f"Preenchendo horas: {horas}")

    for seletor in ["#id_horario", "input[name='horario']", "input[type='time']"]:
        try:
            campo = page.locator(seletor).first
            campo.wait_for(state="visible", timeout=5000)
            campo.scroll_into_view_if_needed(timeout=5000)
            campo.click(timeout=5000)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.wait_for_timeout(150)
            page.keyboard.type(horas, delay=60)
            page.wait_for_timeout(300)
            return
        except Exception:
            pass

    raise Exception("Não consegui preencher Quantidade de horas")


def preencher_observacao(page: Page, texto: str) -> None:
    texto = limpar(texto)
    print("Preenchendo Observações...")

    try:
        frame = page.frame_locator("iframe.cke_wysiwyg_frame").first
        body = frame.locator("body")
        body.click(timeout=7000)
        body.press("Control+A")
        body.press("Backspace")
        body.type(texto, delay=3)
        page.wait_for_timeout(300)
        return
    except Exception:
        pass

    try:
        editor = page.locator("[contenteditable='true']:visible").first
        editor.click(timeout=7000)
        editor.press("Control+A")
        editor.press("Backspace")
        editor.type(texto, delay=3)
        page.wait_for_timeout(300)
        return
    except Exception:
        pass

    try:
        page.locator("textarea:visible").first.fill(texto, timeout=7000)
        page.wait_for_timeout(300)
        return
    except Exception:
        pass

    raise Exception("Não consegui preencher Observações")


def salvar(page: Page) -> None:
    print("Salvando...")

    if not SALVAR_AUTOMATICAMENTE:
        print("SALVAR_AUTOMATICAMENTE = False. Não vou clicar em Salvar.")
        return

    for seletor in [
        "input[type='submit'][value='Salvar']",
        "#submit-id-submit",
        "button:has-text('Salvar')",
        "text=Salvar",
    ]:
        try:
            page.locator(seletor).first.click(timeout=5000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            page.wait_for_timeout(1200)
            return
        except Exception:
            continue

    raise Exception("Não consegui clicar em Salvar")


def tentar_cancelar_ou_voltar(page: Page) -> None:
    try:
        page.get_by_text("Cancelar", exact=False).first.click(timeout=3000)
        page.wait_for_timeout(1000)
        return
    except Exception:
        pass

    try:
        abrir_timesheet(page)
    except Exception:
        pass


def lancar(page: Page, linha: Dict[str, str]) -> None:
    id_l = int(linha["id"])

    print("\n" + "-" * 100)
    print(f"Lançamento {id_l}")
    print(f"{linha['mes']} | Dia {linha['dia']} | {linha['centro_custo']} | {linha['horas']}")
    print("-" * 100)

    preparar_lancamento(page, linha["mes"])

    selecionado_cc = selecionar_lista_inteligente(
        page,
        "Centro de custo",
        linha["centro_custo"],
        linha["centro_custo_busca"],
        obrigatorio=True,
    )

    selecionado_rateio = ""
    if linha["rateio"]:
        aguardar_rateio_carregar(page)
        selecionado_rateio = selecionar_lista_inteligente(
            page,
            "Rateio",
            linha["rateio"],
            linha["rateio_busca"],
            obrigatorio=False,
        )
    else:
        print("Sem rateio.")

    selecionar_dia(page, linha["dia"])
    preencher_horas(page, linha["horas"])
    preencher_observacao(page, linha["observacao"])
    salvar(page)

    msg = f"Centro selecionado: {selecionado_cc} | Rateio selecionado: {selecionado_rateio}"
    escrever_log(id_l, "lancado", "Lançamento salvo", msg)
    atualizar_status(id_l, "lancado", "")


def main() -> None:
    inicializar_banco()
    lancamentos = obter_lancamentos_pendentes()

    print("Robô Local De Timesheet - Versão 7")
    print(f"Lançamentos pendentes: {len(lancamentos)}")
    print(f"Limiar de confiança: {LIMIAR_CONFIANCA:.0%}")
    print(f"Salvar automaticamente: {SALVAR_AUTOMATICAMENTE}")

    with sync_playwright() as p:
        try:
            contexto = p.chromium.launch_persistent_context(
                user_data_dir=PERFIL_NAVEGADOR,
                headless=False,
                channel=CANAL_NAVEGADOR,
                viewport={"width": 1600, "height": 900},
                slow_mo=80,
            )
        except Exception:
            print("Não consegui abrir Edge. Abrindo Chromium.")
            contexto = p.chromium.launch_persistent_context(
                user_data_dir=PERFIL_NAVEGADOR,
                headless=False,
                viewport={"width": 1600, "height": 900},
                slow_mo=80,
            )

        page = contexto.new_page()
        page.goto(URL, wait_until="domcontentloaded")

        aguardar_login(page)
        abrir_timesheet(page)

        for linha in lancamentos:
            try:
                lancar(page, linha)
            except Exception as erro:
                erro_txt = str(erro)
                print(f"ERRO NO LANÇAMENTO {linha['id']}: {erro_txt}")
                escrever_log(int(linha["id"]), "erro", erro_txt)
                atualizar_status(int(linha["id"]), "erro", erro_txt)
                tentar_cancelar_ou_voltar(page)
                page.wait_for_timeout(1000)
                continue

        print("\nProcesso finalizado.")
        print(f"Veja o log em: {LOG_EXECUCAO}")
        print(f"Veja o banco em: {BANCO_DUCKDB}")

        contexto.close()


if __name__ == "__main__":
    main()
