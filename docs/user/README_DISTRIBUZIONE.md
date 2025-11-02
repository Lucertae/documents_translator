# LAC TRANSLATE v2.0 - README Distribuzione

## 📋 Requisiti di Sistema

### Requisiti Minimi
- **Sistema Operativo**: Windows 10 (64-bit) o Windows 11
- **RAM**: 4GB minimo
- **Spazio Disco**: 2GB liberi
- **Processore**: Intel Core i5 o equivalente AMD

### Requisiti Consigliati
- **Sistema Operativo**: Windows 11 (64-bit)
- **RAM**: 8GB o superiore
- **Spazio Disco**: 5GB liberi (per modelli traduzione e OCR)
- **Processore**: Intel Core i7 o AMD Ryzen 7
- **Connessione Internet**: Per download modelli Argos Translate (solo prima installazione)

## 🚀 Installazione

### Installazione Automatica (Raccomandato)

1. **Scarica l'installer**
   - File: `LAC_Translate_v2.0_Setup.exe`
   - Dimensione: ~100-150 MB

2. **Esegui l'installer**
   - Doppio click su `LAC_Translate_v2.0_Setup.exe`
   - Segui le istruzioni del wizard di installazione
   - Scegli directory di installazione (default: `C:\Program Files\LAC TRANSLATE`)
   - Seleziona opzioni (shortcut desktop, menu Start)

3. **Avvia LAC TRANSLATE**
   - Dopo l'installazione, avvia il software dal desktop o menu Start
   - All'avvio, inserisci la chiave seriale fornita

4. **Download modelli (primo avvio)**
   - Se usi Argos Translate (traduzione offline), il software scaricherà automaticamente i modelli linguistici (~800MB)
   - Questo richiede una connessione internet stabile (5-15 minuti)

### Installazione Manuale (Avanzata)

Se preferisci installazione manuale:

1. Estrai `LAC_Translate.exe` dalla distribuzione ZIP
2. Copia il file in una directory (es. `C:\Program Files\LAC TRANSLATE`)
3. Crea shortcut manuale se necessario
4. Avvia l'eseguibile e inserisci la chiave seriale

## 🔑 Attivazione Licenza

### Prima Utilizzo

1. Avvia LAC TRANSLATE
2. Si aprirà automaticamente il dialog di attivazione licenza
3. Inserisci la chiave seriale nel formato: `LAC-XXXX-XXXX-XXXX`
4. Clicca "Attiva Licenza"

### Informazioni Licenza

- La licenza è legata all'hardware del computer
- Una licenza può essere utilizzata su un singolo computer
- Per trasferire la licenza su un nuovo computer, contatta il supporto

### Problemi Attivazione

Se hai problemi con l'attivazione:
- Verifica che la chiave seriale sia corretta
- Controlla la connessione internet (non richiesta ma può aiutare)
- Contatta il supporto con il tuo ID Hardware (mostrato nel dialog attivazione)

## 📚 Utilizzo Base

### Workflow Principale

1. **Apri PDF**
   - File → Apri PDF... (Ctrl+O)
   - Oppure clicca "Apri PDF" nella toolbar

2. **Configura Traduzione**
   - Seleziona lingua sorgente (o "Auto" per rilevamento automatico)
   - Seleziona lingua destinazione
   - Scegli traduttore: Google (online) o Argos (offline)

3. **Traduci**
   - "Traduci Pagina" per pagina corrente (F5)
   - "Traduci Tutto" per tutte le pagine (F6)

4. **Salva PDF Tradotto**
   - File → Salva PDF tradotto... (Ctrl+S)
   - Scegli destinazione e nome file

### Keyboard Shortcuts

- **Ctrl+O**: Apri file PDF
- **Ctrl+S**: Salva PDF tradotto
- **F5**: Traduci pagina corrente
- **F6**: Traduci tutte le pagine
- **Ctrl++**: Zoom in
- **Ctrl+-**: Zoom out
- **Ctrl+0**: Zoom adatta alla finestra

## 🔧 Funzionalità OCR

### Installazione Tesseract OCR

Per utilizzare la traduzione di PDF scansionati:

1. Scarica Tesseract OCR da: https://github.com/UB-Mannheim/tesseract/wiki
2. Installa in percorso standard: `C:\Program Files\Tesseract-OCR`
3. Riavvia LAC TRANSLATE
4. Il software rileverà automaticamente Tesseract

### Utilizzo OCR

- L'OCR viene utilizzato automaticamente per PDF scansionati
- Il software rileva automaticamente se un PDF è scansionato
- Tempo elaborazione: 15-30 secondi per pagina

## 📖 Documentazione

### Manuale Utente Completo
- Consulta `docs/MANUALE_UTENTE.pdf` per guida completa

### Guide Rapide
- `guides/QUICK_START_GUI.md` - Inizia subito
- `guides/GUIDA_OCR.md` - Guida OCR
- `guides/QUICK_COMPARISON.md` - Confronto traduttori

## ⚙️ Impostazioni

### Dialog Impostazioni
- Modifica → Impostazioni...
- Configurazione traduttore predefinito
- Lingue predefinite
- Directory output personalizzate
- Colore testo tradotto

### File Configurazione
Le impostazioni sono salvate in: `%APPDATA%\LAC TRANSLATE\config\settings.json`

## 🆘 Supporto Tecnico

### Contatti
- **Email**: info@lucertae.com
- **Risposta**: Entro 24-48 ore

### Informazioni Sistema
Per assistenza, includi:
- Versione software (Help → Informazioni su LAC TRANSLATE)
- Sistema operativo
- Messaggio di errore (se presente)
- Log file (se disponibile)

### Log Files
I log sono salvati in: `logs/pdf_translator.log`

## ❓ FAQ

### Il software richiede internet?
- **Google Translate**: Sì, richiede connessione internet
- **Argos Translate**: No, funziona completamente offline dopo download modelli

### Posso usare il software offline?
Sì, con Argos Translate. I modelli vengono scaricati una volta e poi funziona offline.

### Quale traduttore è migliore?
- **Google Translate**: Qualità superiore, richiede internet
- **Argos Translate**: Qualità buona, privacy totale, offline

### Come trasferisco la licenza?
Contatta il supporto con:
- Chiave seriale attuale
- ID Hardware nuovo computer

### Il software è sicuro?
Sì, tutti i dati rimangono sul tuo computer. Nessun dato viene inviato a server esterni (tranne Google Translate se utilizzato).

## 📝 Changelog

### Versione 2.0
- Sistema licenze completo
- GUI professionale migliorata
- Settings persistenti
- Installer Windows professionale
- Documentazione completa

## 📄 Licenza

Vedi file `LICENSE.txt` per termini completi di licenza.

---

**LAC TRANSLATE v2.0**  
© 2025 LAC Software - Tutti i diritti riservati

