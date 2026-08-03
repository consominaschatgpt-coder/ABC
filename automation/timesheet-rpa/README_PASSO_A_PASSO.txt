ROBÔ LOCAL DE TIMESHEET - VERSÃO 6

Correção desta versão:
Depois de salvar, a intranet volta para a tela do Timesheet com o calendário em branco.
Por isso, antes de cada lançamento, o robô agora seleciona o mês novamente e só depois clica em Adicionar hora.

Como rodar:

python robo_timesheet_v6.py

Não precisa reinstalar nada se você já instalou as versões anteriores.

Fluxo:
1. Abre a intranet.
2. Você faz login.
3. O robô entra em Time Sheet.
4. Para cada linha do CSV:
   4.1 Seleciona o mês.
   4.2 Clica em Adicionar hora.
   4.3 Preenche os campos.
   4.4 Pausa para você conferir.
   4.5 Salva.
   4.6 Volta para o Timesheet.
5. Repete a próxima linha.

CSV:
mes,dia,centro_custo,centro_custo_busca,rateio,rateio_busca,horas,observacao
