# Robo de preenchimento do Timesheet (Consominas)

Automacao local, sem custo mensal, para preencher o Timesheet em
`https://consominas.vindula.net/` a partir de um CSV. Roda no seu proprio
PC, com o Edge, e voce faz o login manualmente (a senha nunca passa pelo
codigo).

**Validado**: a v7 ja rodou de ponta a ponta contra a intranet real e
lancou os 20 lancamentos de uma semana completa (`lancamentos_timesheet.csv`),
incluindo os dois casos com rateio dependente do Centro de custo
("PROPOSTA" com dois rateios diferentes), sem precisar apertar ENTER
nenhuma vez durante a execucao.

Depois dessa validacao, foram feitos dois ajustes em cima do que ja
funcionava (sem mexer no fluxo comprovado):

- **Mais assertividade**: o catalogo tem varios contratos/OS quase
  identicos no texto, diferindo so' no numero (ex: `AMG CT 20.022/2020 -
  OS 001/2024` vs `... OS 002/2024`, ou `MRN CT 4336/2026` vs `... 4337/2026`).
  O algoritmo antigo dava ate 0.97 de parecenca entre esses pares -
  perigosamente acima do limiar de 70%, ou seja, arriscava lancar no
  contrato/OS errado so' por parecenca de texto. Agora o score penaliza
  quando o numero de contrato/OS/ano e' diferente, derrubando esses pares
  para 0.35-0.48 (abaixo do limiar), sem afetar os casos legitimos de
  busca abreviada que ja funcionavam (ex: `MRN CT 4343` continua achando
  `MRN CT 4343/2026` com 0.92).
- **Mais rapido**: a espera fixa de 3s antes de abrir o Rateio (pra dar
  tempo da tela buscar as opcoes validas para o Centro de custo escolhido)
  virou uma espera adaptativa - so' espera o tempo maximo quando a rede
  realmente demora, e segue na hora quando carrega mais rapido.

## Como funciona

1. Abre `https://consominas.vindula.net/` no Edge.
2. Aguarda o login manual - detecta sozinho quando a tela de "Time Sheet"
   ou "Home" aparece (ate 3 minutos); se nao detectar, so' ai pede ENTER.
3. Entra em **Time Sheet**.
4. Para cada linha do CSV:
   - Seleciona o mes (ex: `2026 - Julho`) e clica em **Adicionar hora**.
   - Preenche **Centro de custo** tentando varios termos de busca em
     sequencia (o que veio do CSV, um termo padrao derivado do nome, a
     primeira palavra, as duas primeiras) ate achar uma opcao visivel com
     pelo menos 70% de parecenca com o valor esperado.
   - Preenche **Rateio** do mesmo jeito, só quando a linha tiver rateio -
     muitos lancamentos nao tem.
   - Seleciona o **Dia**, digita **Horas** (sem os dois pontos, ex: `0300`)
     e preenche **Observações** (CKEditor, `contenteditable` ou
     `textarea`, o que a tela usar).
   - Clica em **Salvar** direto, sem pausa manual.
5. Se nenhuma opcao bater 70% de parecenca num campo obrigatorio, o
   lancamento e' marcado como erro (nao salva "no achismo") e o robo segue
   para o proximo, sem travar a fila inteira.

Cada execucao grava:

- **`timesheet_robo.duckdb`**: base local com o catalogo de opcoes e o
  status de cada lancamento (`pendente`, `lancado`, `erro`). Como o
  status fica salvo, rodar o script de novo nao repete o que ja foi
  lancado com sucesso.
- **`log_execucao_timesheet.csv`**: log linha a linha (data/hora, id,
  status, centro/rateio escolhidos ou erro). Os dois arquivos sao gerados
  localmente e ignorados pelo git (dados de execucao, nao codigo).

## Instalar

```bash
pip install -r requirements.txt
python -m playwright install
```

## Rodar

```bash
python robo_timesheet_v7.py
```

O navegador abre visivel. Faca login manualmente - o robo detecta sozinho
e continua. O login do navegador fica salvo em `perfil_timesheet_robo/`
(ignorado pelo git), entao nas proximas vezes pode nao precisar logar de
novo.

## Arquivos

- **`robo_timesheet_v7.py`**: o robo.
- **`catalogo_opcoes.csv`**: catalogo de Centro de custo e Rateio
  conhecidos (`tipo,nome,busca,apelidos`), usado para gerar um termo de
  busca melhor quando o CSV de lancamentos nao traz um. Hoje cobre a
  parte da lista real ja mapeada nas telas - vale ampliar conforme
  aparecerem centros de custo/rateios novos.
- **`lancamentos_timesheet.csv`**: exemplo real e ja validado (uma semana
  completa, 20 lancamentos, misturando varios centros de custo/contratos
  por dia e dois casos de rateio).
- **`README_PASSO_A_PASSO.txt`**: passo a passo original da v6 (a logica
  de fluxo e' a mesma na v7; mudou o matching e a forma de nao precisar de
  ENTER).
- **`matching.py`**: logica de comparacao de texto (usada tanto pelo robo
  quanto pelo bot do Telegram), pra garantir que os dois entendam o Centro
  de custo/Rateio exatamente do mesmo jeito.
- **`bot_telegram.py`**: bot que recebe mensagem tipo `"4h ADM Marketing"`,
  confirma o que entendeu e grava direto em `lancamentos_timesheet.csv`.
  Veja a secao abaixo.

## Bot do Telegram (lançar hora por mensagem)

Em vez de editar o CSV na mao, da pra mandar uma mensagem no Telegram tipo
`"4h ADM Marketing"` e o bot grava o lancamento pra voce, depois de
confirmar. Ele usa o mesmo algoritmo de comparacao do robo (`matching.py`)
pra achar o Centro de custo certo no `catalogo_opcoes.csv`.

**Configurar (uma vez):**

1. No Telegram, procure `@BotFather`, mande `/newbot`, escolha um nome e
   um username terminado em "bot". Ele devolve um **token**.
2. Crie o arquivo `telegram_token.txt` nesta pasta, com só o token dentro
   (sem espacos ou linhas extras).
3. No Telegram, procure `@userinfobot`, mande qualquer mensagem, ele
   devolve seu **chat_id** (um numero).
4. Crie o arquivo `telegram_chat_id.txt` nesta pasta, com só esse numero.

Os dois arquivos (`telegram_token.txt`, `telegram_chat_id.txt`) sao
ignorados pelo git - sao segredos pessoais, nunca devem ser commitados.

**Rodar:**

```bash
python bot_telegram.py
```

Deixe rodando (numa janela de terminal aberta) e manda mensagem pro bot.
Ele so' responde pro `chat_id` configurado - qualquer outra pessoa que
achar o bot e' ignorada.

**Limitacoes desta primeira versao (MVP):**

- So' funciona enquanto o script estiver rodando no seu PC (nao e' 24/7
  ainda - isso e' um proximo passo, depois de validar o uso no dia a dia).
- Lanca pra **hoje** por padrao, mas entende data se voce mencionar na
  mensagem: `"ontem"`, `"anteontem"`, `"dia 3"` ou uma data tipo `"03/07"`
  ou `"03/07/2026"` (ex: `"4h ontem ADM Marketing"`).
- Nao preenche **Rateio** pela mensagem - se precisar, ajuste direto no
  `lancamentos_timesheet.csv` depois.
- Se passar `LIMITE_HORAS_SEM_LANCAR` (24h por padrao) sem nenhum
  lancamento novo, ele manda um lembrete uma vez - e volta a poder avisar
  de novo se ficar 24h parado outra vez.
- O robo (`robo_timesheet_v7.py`) continua manual - roda quando voce
  clicar no `RODAR_ROBO.bat`, sem disparo automatico.

## Formato do CSV de lancamentos

```csv
mes,dia,centro_custo,centro_custo_busca,rateio,rateio_busca,horas,observacao
2026 - Julho,01,PROPOSTA,PROP,PROPOSTA - Acompanhamento de Propostas,Acompanhamento,0300,"Acompanhamento de propostas comerciais..."
2026 - Julho,01,ADM MARKETING,ADM MARKETING,,,0300,"Elaboração, revisão e organização de demandas..."
```

- `centro_custo` / `rateio`: o valor final que precisa aparecer
  selecionado na tela.
- `centro_custo_busca` / `rateio_busca`: termo digitado no campo de busca.
  Se vazio, o robo tenta achar um termo no `catalogo_opcoes.csv` e, se nao
  achar, gera um termo padrao a partir do valor final.
- Deixe `rateio` (e `rateio_busca`) vazios quando o lancamento nao tiver
  rateio - a maioria nao tem.
- Pode ter varias linhas no mesmo `dia`, com centros de custo diferentes.

## Ajustar a sensibilidade

No topo de `robo_timesheet_v7.py`:

- `LIMIAR_CONFIANCA = 0.70`: abaixo disso, o robo nao arrisca clicar e
  marca o lancamento como erro em vez de salvar algo errado.
- `SALVAR_AUTOMATICAMENTE = True`: coloque `False` para o robo preencher
  tudo e parar antes de clicar em Salvar (util pra conferir sem lancar).
- `NAVEGADOR_ESCONDIDO = True`: navegador roda invisivel (headless). So'
  funciona bem porque a sessao de login ja fica salva em
  `perfil_timesheet_robo/` de uma execucao visivel anterior - se a sessao
  expirar um dia, nao tem tela pra logar de novo, entao rode com
  `NAVEGADOR_ESCONDIDO = False` uma vez pra relogar.
- `MODO_SILENCIOSO = True`: no terminal, mostra so' uma barra de
  progresso (`[####------] 40% (8/20) ...`) em vez dos logs tecnicos
  passo a passo. Os detalhes tecnicos continuam sendo gravados em
  `debug_execucao.log`, pra investigar se algo der erro.

## Proximos passos

- Ampliar `catalogo_opcoes.csv` conforme aparecerem centros de
  custo/rateios novos na intranet.
- Validar o bot do Telegram no dia a dia (v1: so' Centro de custo + horas,
  sem Rateio, sempre pra hoje).
- Deixar o bot rodando 24/7 (hoje so' funciona com o script aberto no PC) -
  precisa decidir onde hospedar sem custo mensal.
- Disparo automatico do robo (ex: toda sexta a noite) depois que o bot
  estiver validado, fechando o ciclo sem precisar abrir o terminal.
