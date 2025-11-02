@echo off
echo ========================================
echo  LAC TRANSLATE - ICONA DESKTOP
echo ========================================
echo.

echo Convertendo PNG in ICO e aggiornando shortcut...
echo.

powershell -ExecutionPolicy Bypass -Command "& { Add-Type -AssemblyName System.Drawing; $pngPath = 'C:\Users\jecho\Pictures\logo_alt.png'; $icoPath = 'C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\logo_alt.ico'; $pngImage = [System.Drawing.Image]::FromFile($pngPath); $icon = [System.Drawing.Icon]::FromHandle((New-Object System.Drawing.Bitmap($pngImage)).GetHicon()); $fileStream = [System.IO.File]::Create($icoPath); $icon.Save($fileStream); $fileStream.Close(); $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\Desktop\Lac Translate.lnk'); $Shortcut.TargetPath = 'C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\AVVIA_GUI.bat'; $Shortcut.WorkingDirectory = 'C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate'; $Shortcut.IconLocation = $icoPath; $Shortcut.Description = 'Lac Translate - Traduttore PDF con OCR'; $Shortcut.Save(); $pngImage.Dispose(); $icon.Dispose(); Write-Host 'Icona desktop aggiornata!' -ForegroundColor Green }"

echo.
echo ✅ Shortcut desktop aggiornato con icona personalizzata!
echo 📁 File ICO creato: logo_alt.ico
echo 🎯 Icona: logo_alt.png convertita in formato Windows
echo.
echo 💡 Suggerimento: Premi F5 sul desktop per aggiornare le icone
echo.
pause
