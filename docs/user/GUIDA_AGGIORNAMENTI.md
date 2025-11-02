# Guida Aggiornamenti - LAC TRANSLATE

Come aggiornare LAC TRANSLATE alla versione più recente.

---

## Controllo Manuale Aggiornamenti

### Metodo 1: Dal Menu

1. Apri LAC TRANSLATE
2. Vai su **Aiuto → Verifica Aggiornamenti...**
3. Il software controllerà automaticamente se ci sono nuove versioni
4. Se disponibile, segui le istruzioni per scaricare

---

## Controllo Automatico

### Configurazione

LAC TRANSLATE può controllare automaticamente gli aggiornamenti all'avvio:

**File:** `config/update_config.json`

```json
{
  "check_on_startup": true,
  "check_interval_days": 7
}
```

**Opzioni:**
- `check_on_startup`: `true` per controllo automatico all'avvio
- `check_interval_days`: Giorni tra un controllo e l'altro (default: 7)

---

## Download Aggiornamenti

### Opzione 1: Download da GitHub (Raccomandato)

Quando viene trovato un aggiornamento:

1. Clicca "Sì" quando chiesto se scaricare
2. Il software aprirà la pagina GitHub Release nel browser
3. Scarica manualmente l'installer dalla pagina GitHub
4. Esegui l'installer per aggiornare

### Opzione 2: Download Automatico

1. Quando viene trovato un aggiornamento, scegli "Download Automatico"
2. Il file verrà scaricato nella cartella `downloads/`
3. Dopo il download, chiudi LAC TRANSLATE
4. Esegui l'installer scaricato
5. Riavvia l'applicazione

---

## Installazione Aggiornamento

### Windows

1. **Chiudi LAC TRANSLATE** completamente
2. Esegui il file `LAC_Translate_v[X.X.X]_Setup.exe`
3. Segui l'installer (sovrascriverà la versione precedente)
4. Riavvia LAC TRANSLATE

### macOS / Linux

1. **Chiudi LAC TRANSLATE**
2. Esegui l'installer corrispondente alla tua piattaforma
3. Segui le istruzioni di installazione
4. Riavvia l'applicazione

---

## Verifica Versione Installata

Per verificare quale versione hai installata:

1. Apri LAC TRANSLATE
2. Vai su **Aiuto → Informazioni su LAC TRANSLATE**
3. Vedrai la versione corrente

Oppure usa il menu **Aiuto → Verifica Aggiornamenti...** per confrontare con l'ultima disponibile.

---

## Troubleshooting

### Il controllo aggiornamenti non funziona

**Problema:** Errore "Impossibile verificare aggiornamenti"

**Soluzioni:**
1. Verifica connessione internet
2. Verifica che GitHub sia accessibile
3. Controlla firewall/antivirus che non blocchi la connessione
4. Prova manualmente: `Aiuto → Verifica Aggiornamenti...`

### Download fallisce

**Problema:** Download non completa o errore

**Soluzioni:**
1. Verifica spazio su disco sufficiente
2. Controlla connessione internet stabile
3. Prova a scaricare manualmente da GitHub
4. Verifica permessi di scrittura nella cartella `downloads/`

### Installer non funziona

**Problema:** Installer non si avvia o dà errore

**Soluzioni:**
1. Verifica che il download sia completo (dimensione file)
2. Scarica di nuovo da GitHub se corrotto
3. Esegui come amministratore (Windows)
4. Verifica che non ci siano processi LAC TRANSLATE attivi

---

## Note Importanti

- **Backup:** Prima di aggiornare, fai backup della cartella `config/` se hai personalizzazioni
- **Licenza:** La licenza viene mantenuta dopo l'aggiornamento
- **Settings:** Le impostazioni vengono preservate
- **PDF in lavorazione:** Completa eventuali traduzioni in corso prima di aggiornare

---

## Link Utili

- **Repository GitHub:** https://github.com/Lucertae/documents_translator
- **Releases:** https://github.com/Lucertae/documents_translator/releases
- **Supporto:** info@lucertae.it

---

**Versione Documento:** 1.0  
**Data:** 2025

