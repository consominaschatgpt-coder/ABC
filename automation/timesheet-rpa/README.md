# Robo de preenchimento do Timesheet (Consominas)

Automacao local, sem custo mensal, para preencher o Timesheet em
`https://consominas.vindula.net/` a partir de um CSV. Roda no seu proprio
PC, com o Edge, e voce faz o login manualmente (a senha nunca passa pelo
codigo).

Versao atual: **`robo_timesheet_v6.py`**. Ela corrige o problema em que,
apos salvar um lancamento, a intranet volta para a tela do Timesheet com o
calendario em branco - por isso o robo agora seleciona o mes de novo antes
de cada lancamento, e nao so uma vez no inicio.

## Fluxo que o robo executa

1. Abre `https://consominas.vindula.net/` no Edge.
2. Espera voce fazer login manualmente.
3. Entra em **Time Sheet**.
4. Para cada linha do CSV:
   - Seleciona o mes (ex: `2026 - Julho`) e clica em **Adicionar hora**.
   - Preenche **Centro de custo** (digita o termo de busca e escolhe a
     opcao mais parecida com o valor esperado).
   - Preenche **Rateio** somente quando a linha tiver rateio - muitos
     lancamentos nao tem.
   - Seleciona o **Dia**.
   - Digita **Horas** sem os dois pontos (ex: `0800` para 08:00).
   - Preenche **Observações** (funciona com editor CKEditor, campo
     `contenteditable` ou `textarea`, dependendo do que a tela usar).
   - Pausa para voce conferir antes de clicar em **Salvar**.
   - Volta para a tela do Timesheet e segue pro proximo lancamento.

Se algum passo nao encontrar o elemento automaticamente, o robo pausa,
mostra o que precisa ser feito e deixa voce completar manualmente na tela
antes de apertar ENTER para continuar.

## Instalar

```bash
pip install -r requirements.txt
python -m playwright install
```

## Rodar

Coloque seu CSV de lancamentos na mesma pasta (ou ajuste `ARQUIVO_CSV` no
topo do script) e rode:

```bash
python robo_timesheet_v6.py
```

O navegador abre visivel. Faca login manualmente e o robo continua depois
que voce confirmar no terminal. O login fica salvo em
`perfil_timesheet_robo/` (ignorado pelo git), entao nas proximas vezes pode
nao precisar logar de novo.

## Formato do CSV

```csv
mes,dia,centro_custo,centro_custo_busca,rateio,rateio_busca,horas,observacao
2026 - Julho,01,PROPOSTA,PROP,PROPOSTA - Acompanhamento de Propostas,Acompanhamento,0800,Acompanhamento de propostas e organizacao das informacoes comerciais.
2026 - Julho,02,ADM Atividades Adm,ADM Atividades,,,0400,Apoio administrativo e organizacao de demandas internas.
```

- `centro_custo` / `rateio`: o valor final que precisa aparecer selecionado
  na tela.
- `centro_custo_busca` / `rateio_busca`: o termo digitado no campo de busca
  para filtrar a lista suspensa antes de escolher a opcao. Se deixar em
  branco, o robo gera um termo de busca automaticamente a partir do valor
  final.
- Deixe `rateio` (e `rateio_busca`) vazios quando o lancamento nao tiver
  rateio.

Veja `README_PASSO_A_PASSO.txt` para o passo a passo resumido.

## Proximos passos (quando a v6 estiver validada)

- Trocar o CSV por Excel (`openpyxl` ja esta nas dependencias) ou por uma
  base local em DuckDB (`duckdb` ja esta nas dependencias) com centros de
  custo, rateios e apelidos cadastrados, para digitar menos.
- Reduzir as pausas manuais (`CONFIRMAR_ANTES_DE_SALVAR`, `MODO_ASSISTIDO`)
  conforme os seletores forem validados contra a tela real.
