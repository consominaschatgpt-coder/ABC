# Robo de preenchimento do Timesheet (Consominas)

Automacao local, sem custo mensal, para preencher o Timesheet em
`https://consominas.vindula.net/` a partir de um CSV. Roda no seu proprio
PC, com o Edge, e voce faz o login manualmente (a senha nunca passa pelo
codigo).

Versao atual: **`robo_timesheet_v7.py`**. Mantem a correcao da v6 (recomeca
pela selecao do mes a cada lancamento, porque a intranet volta para o
calendario em branco apos salvar) e adiciona:

- **Escolha sempre pela opcao mais parecida** (`matching.py`): em vez de
  desistir e apertar ENTER as cegas numa lista suspensa que nao carregou
  a opcao exata, o robo compara todas as opcoes visiveis com o valor
  esperado e escolhe a mais parecida, com um score de confianca de 0 a 1.
- **Modo rapido** (`MODO_RAPIDO = True`): nao pausa pedindo ENTER a cada
  lancamento. So pausa quando um campo obrigatorio nao tem nenhuma opcao
  parecida o suficiente (falha de verdade).
- **Relatorio final** (`relatorio_execucao.csv`, gerado a cada execucao e
  ignorado pelo git): mostra o score de cada campo preenchido, para
  revisar depois em vez de conferir lancamento por lancamento.

## Testar o "matching" sem abrir navegador (recomendado antes de rodar de verdade)

A tela de Centro de custo tem uma lista longa e com nomes parecidos (varios
"ADM ..." e codigos de contrato como `AGA CT 15140/2025 - CB`). Antes de
apontar o robo pro site real, da pra validar se o algoritmo de escolha
acerta a opcao certa mesmo quando o texto do CSV nao bate 100% com o texto
da tela:

```bash
python teste_matching_offline.py
```

Esse teste nao abre navegador nenhum. Ele roda em duas partes:

1. **Casamento direto** - usa `lancamentos_semana_simulada.csv` (uma
   semana com 2 a 3 centros de custo/contratos diferentes por dia) contra
   `opcoes_centro_de_custo_exemplo.txt` (lista real, porem parcial,
   extraida das telas enviadas).
2. **Estresse com texto imperfeito** - testa abreviacoes/erros de digitacao
   propositais (ex: `"Logistica"` no lugar de `"ADM LOGISTICA"`) e mede se
   o algoritmo ainda acha a opcao certa e com que score.

No teste atual, os dois cenarios batem 100% (scores entre 0.69 e 1.00),
acima do limiar de aceitacao automatica configurado em `matching.py`
(`LIMIAR_AUTOMATICO = 0.5`).

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
   - Clica em **Salvar** direto (modo rapido) - sem pedir ENTER a cada
     lancamento.
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
python robo_timesheet_v7.py
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

Veja `README_PASSO_A_PASSO.txt` para o passo a passo resumido (documento
original da v6 - a logica de fluxo e' a mesma na v7, so' mudou o matching
e as pausas).

## Proximos passos (quando a v7 estiver validada contra o site real)

- Substituir os exemplos por uma semana real de lancamentos (5 a 10
  linhas) antes de rodar o mes inteiro.
- Ampliar `opcoes_centro_de_custo_exemplo.txt` com a lista completa de
  Centro de custo (hoje e' parcial, baseada so' no que apareceu nas
  telas) para deixar o teste offline mais representativo.
- Trocar o CSV por Excel (`openpyxl` ja esta nas dependencias) ou por uma
  base local em DuckDB (`duckdb` ja esta nas dependencias) com centros de
  custo, rateios e apelidos cadastrados, para digitar menos.
- Desligar `MODO_ASSISTIDO` (pausas de seguranca) so' depois que os
  seletores estiverem validados contra a tela real por algumas semanas.
