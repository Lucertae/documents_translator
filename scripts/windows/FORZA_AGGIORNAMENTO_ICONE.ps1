# Script per forzare l'aggiornamento delle icone desktop
# e provare metodi alternativi

Write-Host "Aggiornando cache icone Windows..." -ForegroundColor Yellow

# Metodo 1: Forza aggiornamento cache icone
try {
    # Pulisce la cache delle icone
    Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache*" -Force -ErrorAction SilentlyContinue
    Write-Host "Cache icone pulita" -ForegroundColor Green
} catch {
    Write-Host "Impossibile pulire cache: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Metodo 2: Riavvia Explorer per forzare aggiornamento
Write-Host "Riavviando Explorer..." -ForegroundColor Yellow
try {
    Stop-Process -Name "explorer" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Start-Process "explorer.exe"
    Write-Host "Explorer riavviato" -ForegroundColor Green
} catch {
    Write-Host "Errore riavvio Explorer: $($_.Exception.Message)" -ForegroundColor Red
}

# Metodo 3: Ricrea il shortcut con icona di sistema come fallback
Write-Host "Ricreando shortcut con icona di sistema..." -ForegroundColor Yellow

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Lac Translate.lnk")

# Usa un'icona di sistema come fallback
$Shortcut.TargetPath = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\AVVIA_GUI.bat"
$Shortcut.WorkingDirectory = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate"
$Shortcut.Description = "Lac Translate - Traduttore PDF con OCR"

# Prova prima con l'ICO personalizzato, poi fallback su icona sistema
$icoPath = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\logo_alt.ico"
if (Test-Path $icoPath) {
    $Shortcut.IconLocation = $icoPath
    Write-Host "Usando icona personalizzata: $icoPath" -ForegroundColor Green
} else {
    # Fallback su icona di sistema
    $Shortcut.IconLocation = "shell32.dll,1"
    Write-Host "Usando icona di sistema come fallback" -ForegroundColor Yellow
}

$Shortcut.Save()

Write-Host "Shortcut aggiornato!" -ForegroundColor Green
Write-Host "Aspetta qualche secondo e controlla il desktop..." -ForegroundColor Cyan
