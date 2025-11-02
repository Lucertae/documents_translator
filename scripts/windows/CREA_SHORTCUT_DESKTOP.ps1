# Script per creare shortcut desktop per Lac Translate
# Con icona personalizzata

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Lac Translate.lnk")

# Imposta il percorso del file batch di avvio
$Shortcut.TargetPath = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\AVVIA_GUI.bat"

# Imposta la directory di lavoro
$Shortcut.WorkingDirectory = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate"

# Imposta l'icona personalizzata
$Shortcut.IconLocation = "C:\Users\jecho\Pictures\logo_alt.png"

# Imposta la descrizione
$Shortcut.Description = "Lac Translate - Traduttore PDF con OCR"

# Salva il shortcut
$Shortcut.Save()

Write-Host "Shortcut desktop creato con successo!" -ForegroundColor Green
Write-Host "Percorso: $env:USERPROFILE\Desktop\Lac Translate.lnk" -ForegroundColor Cyan
Write-Host "Icona: C:\Users\jecho\Pictures\logo_alt.png" -ForegroundColor Cyan
