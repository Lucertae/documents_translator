# Script avanzato per creare icona desktop funzionante
# Usa metodo più robusto per conversione PNG->ICO

Add-Type -AssemblyName System.Drawing

try {
    Write-Host "Creando icona ICO avanzata..." -ForegroundColor Yellow
    
    $pngPath = "C:\Users\jecho\Pictures\logo_alt.png"
    $icoPath = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\logo_alt.ico"
    
    # Carica l'immagine PNG
    $originalImage = [System.Drawing.Image]::FromFile($pngPath)
    
    # Crea multiple dimensioni per l'ICO (Windows preferisce questo)
    $sizes = @(16, 32, 48, 64, 128, 256)
    $iconImages = @()
    
    foreach ($size in $sizes) {
        $resizedImage = New-Object System.Drawing.Bitmap($originalImage, $size, $size)
        $iconImages += $resizedImage
    }
    
    # Crea l'icona con multiple dimensioni
    $icon = [System.Drawing.Icon]::FromHandle($iconImages[1].GetHicon()) # Usa 32x32
    
    # Salva l'ICO
    $fileStream = [System.IO.File]::Create($icoPath)
    $icon.Save($fileStream)
    $fileStream.Close()
    
    Write-Host "ICO avanzato creato: $icoPath" -ForegroundColor Green
    
    # Copia l'icona anche nella cartella di sistema per maggiore compatibilità
    $systemIconPath = "$env:LOCALAPPDATA\Microsoft\Windows\Themes\logo_alt.ico"
    Copy-Item $icoPath $systemIconPath -Force
    Write-Host "Icona copiata in sistema: $systemIconPath" -ForegroundColor Green
    
    # Ricrea il shortcut con il nuovo ICO
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Lac Translate.lnk")
    $Shortcut.TargetPath = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\AVVIA_GUI.bat"
    $Shortcut.WorkingDirectory = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate"
    $Shortcut.IconLocation = $icoPath
    $Shortcut.Description = "Lac Translate - Traduttore PDF con OCR"
    $Shortcut.Save()
    
    Write-Host "Shortcut aggiornato con ICO avanzato!" -ForegroundColor Green
    
    # Pulisci le risorse
    $originalImage.Dispose()
    foreach ($img in $iconImages) { $img.Dispose() }
    $icon.Dispose()
    
    Write-Host "Prova ora a premere F5 sul desktop per aggiornare!" -ForegroundColor Cyan
    
} catch {
    Write-Host "Errore: $($_.Exception.Message)" -ForegroundColor Red
    
    # Fallback: usa icona di sistema
    Write-Host "Usando icona di sistema come fallback..." -ForegroundColor Yellow
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Lac Translate.lnk")
    $Shortcut.TargetPath = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate\AVVIA_GUI.bat"
    $Shortcut.WorkingDirectory = "C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate"
    $Shortcut.IconLocation = "shell32.dll,1"
    $Shortcut.Description = "Lac Translate - Traduttore PDF con OCR"
    $Shortcut.Save()
    Write-Host "Shortcut creato con icona di sistema!" -ForegroundColor Green
}
