@echo off
echo ========================================
echo  LAC TRANSLATE - RISOLUZIONE ICONA
echo ========================================
echo.

echo Metodo 1: Creazione ICO avanzato...
powershell -ExecutionPolicy Bypass -File "ICONA_AVANZATA.ps1"

echo.
echo Metodo 2: Forzare aggiornamento cache...
powershell -ExecutionPolicy Bypass -File "FORZA_AGGIORNAMENTO_ICONE.ps1"

echo.
echo Metodo 3: Riavvia Explorer completamente...
taskkill /f /im explorer.exe >nul 2>&1
timeout /t 2 /nobreak >nul
start explorer.exe

echo.
echo ✅ Tutti i metodi eseguiti!
echo.
echo 💡 ISTRUZIONI:
echo 1. Premi F5 sul desktop per aggiornare le icone
echo 2. Se ancora bianco, riavvia il computer
echo 3. L'icona dovrebbe apparire dopo il riavvio
echo.
echo 🔧 ALTERNATIVA: Usa il file batch AVVIA_GUI.bat direttamente
echo.
pause
