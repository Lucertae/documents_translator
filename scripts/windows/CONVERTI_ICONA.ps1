# Script per convertire PNG in ICO e aggiornare il shortcut
# Usa Add-Type per caricare System.Drawing

Add-Type -AssemblyName System.Drawing

try {
    # Carica l'immagine PNG
    $pngPath = "C:\Users\jecho\Pictures\logo_alt.png"
    $icoPath = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\logo_alt.ico"
    
    Write-Host "Convertendo PNG in ICO..." -ForegroundColor Yellow
    
    # Carica l'immagine PNG
    $pngImage = [System.Drawing.Image]::FromFile($pngPath)
    
    # Crea un'icona dalle dimensioni dell'immagine originale
    $icon = [System.Drawing.Icon]::FromHandle((New-Object System.Drawing.Bitmap($pngImage)).GetHicon())
    
    # Salva come ICO
    $fileStream = [System.IO.File]::Create($icoPath)
    $icon.Save($fileStream)
    $fileStream.Close()
    
    Write-Host "ICO creato: $icoPath" -ForegroundColor Green
    
    # Aggiorna il shortcut con l'icona ICO
    Write-Host "Aggiornando shortcut desktop..." -ForegroundColor Yellow
    
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Lac Translate.lnk")
    $Shortcut.TargetPath = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\AVVIA_GUI.bat"
    $Shortcut.WorkingDirectory = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate"
    $Shortcut.IconLocation = $icoPath
    $Shortcut.Description = "Lac Translate - Traduttore PDF con OCR"
    $Shortcut.Save()
    
    Write-Host "Shortcut aggiornato con icona ICO!" -ForegroundColor Green
    Write-Host "Ricarica il desktop (F5) per vedere l'icona aggiornata" -ForegroundColor Cyan
    
    # Pulisci le risorse
    $pngImage.Dispose()
    $icon.Dispose()
    
} catch {
    Write-Host "Errore: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Proviamo metodo alternativo..." -ForegroundColor Yellow
}
