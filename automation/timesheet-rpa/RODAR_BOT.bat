@echo off
cd /d "%~dp0"
echo Instalando dependencias (so demora na primeira vez)...
python -m pip install -r requirements.txt
python -m playwright install
echo.
echo Iniciando o bot do Timesheet (fica sempre ligado)...
echo Manda mensagens no Telegram e "preencher" quando quiser lancar tudo.
echo.
python bot_telegram.py
echo.
echo O bot parou. Se apareceu algum erro acima, tire print e manda.
pause
