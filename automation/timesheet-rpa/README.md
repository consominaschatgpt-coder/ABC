# Robo de preenchimento do Timesheet (Consominas)

Automacao local, sem custo mensal, para preencher o Timesheet em
`https://consominas.vindula.net/` a partir de um CSV. Roda no seu proprio
PC, com o Edge, e voce faz o login manualmente (a senha nunca passa pelo
codigo).

## Fluxo que o robo executa

1. Abre `https://consominas.vindula.net/` no Edge.
2. Espera voce fazer login manualmente.
3. Clica em **Time Sheet** no menu lateral.
4. Seleciona o mes (ex: `2026 - Julho`).
5. Clica em **Adicionar hora**.
6. Para cada linha do CSV:
   - Preenche **Centro de custo**.
   - Preenche **Rateio** somente quando a linha tiver rateio (muitos
     lancamentos nao tem).
   - Preenche **Dia**.
   - Digita **Horas** sem os dois pontos (ex: `0800` para 08:00).
   - Preenche **Observações**.
   - Clica em **Salvar**.
   - Espera a tela voltar para **Adicionar hora** e segue pro proximo.

## Instalar

```bash
pip install -r requirements.txt
python -m playwright install
```

## Rodar

Coloque seu CSV de lancamentos na mesma pasta (ou passe o caminho) e rode:

```bash
python robo_timesheet_v1.py lancamentos_timesheet.csv
```

O navegador abre visivel. Faca login manualmente e volte no terminal para
apertar ENTER. O login fica salvo em `perfil_timesheet/` (ignorado pelo
git), entao nas proximas vezes pode nao precisar logar de novo.

## Formato do CSV

```csv
mes,dia,centro_custo,rateio,horas,observacao
2026 - Julho,01,PROPOSTA,PROPOSTA - Acompanhamento de Propostas,0800,Acompanhamento de propostas e organizacao das informacoes comerciais.
2026 - Julho,02,ADM Atividades Adm,,0400,Apoio administrativo e organizacao de demandas internas.
```

Deixe a coluna `rateio` vazia quando o lancamento nao tiver rateio.

## Se algum campo nao for encontrado

Como o site fica atras de login corporativo, os textos usados no script
(`Centro de custo`, `Rateio`, `Adicionar hora`, etc.) foram definidos pela
descricao do fluxo, e podem nao bater 100% com o HTML real na primeira
tentativa. Quando isso acontecer, o robo:

- Mostra no terminal qual campo nao encontrou.
- Pausa e deixa voce preencher esse campo manualmente na tela.
- Continua para o proximo lancamento quando voce apertar ENTER.

Para corrigir o seletor de vez, rode o gravador do Playwright apontando
pro site e clique nos campos reais - ele te devolve o seletor exato:

```bash
python -m playwright codegen https://consominas.vindula.net/
```

Copie o seletor certo para dentro de `robo_timesheet_v1.py`, na funcao
`preencher_lancamento`.

## Proximos passos (quando a v1 estiver validada)

- Trocar o CSV por Excel (`openpyxl` ja esta nas dependencias) ou por uma
  base local (ex: DuckDB) com centros de custo, rateios e apelidos
  cadastrados, para digitar menos.
- Adicionar um modo "dry-run" que so mostra o que seria preenchido, sem
  clicar em Salvar.
