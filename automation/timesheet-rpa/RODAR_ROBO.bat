@echo off
cd /d "%~dp0"
echo Instalando dependencias (so demora na primeira vez)...
python -m pip install -r requirements.txt
python -m playwright install
echo.
echo Iniciando o robo do Timesheet (visivel - use se precisar logar de novo)...
echo.
python robo_timesheet_v7.py
echo.
echo O robo parou. Se apareceu algum erro acima, tire print e manda.
pause
