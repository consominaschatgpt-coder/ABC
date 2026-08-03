@echo off
echo Removendo bloqueio de seguranca dos arquivos desta pasta (evita a tela
echo "Fornecedor Desconhecido" toda vez que o Windows tentar abrir sozinho)...
powershell -NoProfile -Command "Get-ChildItem -Path '%~dp0' -Recurse | Unblock-File" >nul 2>&1

echo Configurando o bot para iniciar sozinho quando o Windows ligar...

set SCRIPT="%TEMP%\criar_atalho_timesheet.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Startup") ^& "\RodarBotTimesheet.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%~dp0RODAR_BOT.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.WindowStyle = 7 >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo Pronto! Da proxima vez que voce ligar o Windows (ou fizer login),
echo o bot do Timesheet vai abrir sozinho, sem precisar clicar em nada.
echo.
echo Se um dia quiser desligar isso, va em:
echo   %%APPDATA%%\Microsoft\Windows\Start Menu\Programs\Startup
echo e apague o atalho "RodarBotTimesheet".
echo.
pause
