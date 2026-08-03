@echo off
cd /d "%~dp0"

rem Garante que o atalho de inicio automatico do Windows aponta pra ESTA
rem pasta, sempre que voce roda este .bat na mao. Isso resolve o caso de
rem trocar de pasta (ex: extrair um zip novo em outro lugar) e o atalho
rem antigo ficar "morto", apontando pra uma pasta que nao existe mais -
rem sem isso, o bot so' liga sozinho se voce lembrar de rodar de novo o
rem INSTALAR_INICIO_AUTOMATICO.bat toda vez que mudar de pasta.
powershell -NoProfile -Command "Get-ChildItem -Path '%~dp0' -Recurse | Unblock-File" >nul 2>&1
set SCRIPT="%TEMP%\criar_atalho_timesheet.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Startup") ^& "\RodarBotTimesheet.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%~dp0RODAR_BOT.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.WindowStyle = 7 >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT% >nul 2>&1
del %SCRIPT% >nul 2>&1

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
