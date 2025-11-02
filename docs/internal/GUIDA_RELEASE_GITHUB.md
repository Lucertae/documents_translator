# Guida Rilascio Nuova Versione - GitHub

Come rilasciare una nuova versione che gli utenti installati potranno aggiornare automaticamente.

---

## Processo Completo di Release

### Step 1: Aggiorna Numero Versione

**File:** `app/version.py`

Aggiorna i numeri di versione:
```python
VERSION_MAJOR = 2  # Cambia solo per breaking changes
VERSION_MINOR = 1  # Incrementa per nuove funzionalità
VERSION_PATCH = 0  # Incrementa per bug fixes
```

**Esempio per patch:** `2.0.0` → `2.0.1`  
**Esempio per feature:** `2.0.1` → `2.1.0`  
**Esempio per major:** `2.1.0` → `3.0.0`

---

### Step 2: Aggiorna Changelog

**File:** `changelog/CHANGELOG.md`

Aggiungi le nuove modifiche:
```markdown
## [2.1.0] - 2025-01-XX

### Aggiunto
- Nuova funzionalità X
- Miglioramento Y

### Corretto
- Bug fix Z
```

---

### Step 3: Build Installer

**Windows:**
```bash
python build.py
```

Output:
- `dist/LAC_Translate.exe` - Eseguibile standalone
- `release/installer/LAC_Translate_v2.1.0_Setup.exe` - Installer Windows

**macOS/Linux:** (se supportati)
```bash
python build_multi_platform.py
```

---

### Step 4: Test Installer

1. Installa su PC pulito o VM
2. Verifica funzionamento
3. Testa aggiornamento da versione precedente
4. Verifica licenza preservata

---

### Step 5: Crea GitHub Release

#### Metodo A: Via GitHub Web Interface

1. Vai su: https://github.com/Lucertae/documents_translator/releases
2. Clicca **"Draft a new release"**
3. **Tag version:** `v2.1.0` (deve corrispondere a `VERSION_STRING` senza "v")
4. **Release title:** `LAC TRANSLATE v2.1.0`
5. **Description:** Copia da `changelog/CHANGELOG.md` o scrivi summary
6. **Attach binaries:** 
   - Carica `release/installer/LAC_Translate_v2.1.0_Setup.exe`
   - (Opzionale: altri installer per macOS/Linux)
7. Clicca **"Publish release"**

#### Metodo B: Via Git Tag (CLI)

```bash
# Commit modifiche
git add app/version.py changelog/CHANGELOG.md
git commit -m "Bump version to 2.1.0"

# Crea tag
git tag v2.1.0 -m "Release v2.1.0"
git push origin main
git push origin v2.1.0

# Poi crea release su GitHub web interface e carica installer
```

---

### Step 6: Verifica Release

1. Vai su: https://github.com/Lucertae/documents_translator/releases/latest
2. Verifica che release appaia come "Latest"
3. Verifica che installer sia allegato
4. Testa download manuale

---

### Step 7: Notifica Utenti (Opzionale)

Gli utenti con installazione attiva riceveranno automaticamente notifica quando:
- Avviano il software (se `check_on_startup: true`)
- Oppure cliccano manualmente "Verifica Aggiornamenti"

**Non è necessario notificarli manualmente**, ma puoi:
- Inviare email a clienti registrati
- Post su social (se presenti)

---

## Struttura Release GitHub

### Release Notes Template

```
# LAC TRANSLATE v2.1.0

## Novità
- [Nuova funzionalità 1]
- [Nuova funzionalità 2]

## Miglioramenti
- [Miglioramento 1]
- [Miglioramento 2]

## Correzioni
- [Bug fix 1]
- [Bug fix 2]

## Installazione
1. Scarica l'installer per la tua piattaforma
2. Chiudi LAC TRANSLATE se aperto
3. Esegui l'installer
4. Riavvia l'applicazione

La licenza e le impostazioni verranno preservate.
```

---

## Versionamento

Segui **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR** (3.0.0): Breaking changes, incompatibilità
- **MINOR** (2.1.0): Nuove funzionalità, backward compatible
- **PATCH** (2.0.1): Bug fixes, backward compatible

---

## Checklist Pre-Release

Prima di pubblicare una release:

- [ ] Versione aggiornata in `app/version.py`
- [ ] Changelog aggiornato
- [ ] Installer creato e testato
- [ ] Testato su sistema pulito
- [ ] Licenza preservata dopo aggiornamento
- [ ] Settings preservati dopo aggiornamento
- [ ] Release creata su GitHub
- [ ] Installer caricato su GitHub Release
- [ ] Tag versione corretto (es. `v2.1.0`)

---

## Come Funziona per l'Utente

### Installazione su Nuovo Dispositivo

1. Utente scarica installer dalla GitHub Release
2. Installa software
3. Attiva licenza
4. Software funziona normalmente

### Aggiornamento su Dispositivo Esistente

**Opzione A: Controllo Automatico**
1. Utente avvia software
2. Dopo 5 secondi (se `check_on_startup: true`), appare notifica se aggiornamento disponibile
3. Utente clicca "Sì" per verificare
4. Software mostra dialog aggiornamento
5. Utente sceglie se scaricare

**Opzione B: Controllo Manuale**
1. Utente va su **Aiuto → Verifica Aggiornamenti...**
2. Software controlla GitHub
3. Se disponibile, mostra dialog download
4. Utente scarica e installa

**Download e Installazione:**
1. Utente scarica installer (automatico o manuale da GitHub)
2. Chiude LAC TRANSLATE
3. Esegue installer (sovrascrive versione precedente)
4. Riavvia applicazione
5. Licenza e settings preservati automaticamente

---

## Troubleshooting Release

### Release non viene rilevata

**Problema:** Utenti non vedono aggiornamento disponibile

**Soluzioni:**
1. Verifica che tag sia `v2.1.0` (con "v")
2. Verifica che release sia marcata come "Latest"
3. Verifica formato versione in `app/version.py` corrisponda
4. Attendi alcuni minuti (cache GitHub API)

### Installer non disponibile

**Problema:** Utente non trova installer da scaricare

**Soluzioni:**
1. Verifica che installer sia allegato alla release
2. Verifica nome file (deve contenere versione)
3. Verifica permessi file (non bloccato)

### Versione non corrisponde

**Problema:** Versione in app non corrisponde a tag GitHub

**Soluzioni:**
1. Verifica `app/version.py` aggiornato prima di release
2. Tag GitHub deve essere `v` + `VERSION_STRING`
3. Esempio: se `VERSION_STRING = "2.1.0"`, tag deve essere `v2.1.0`

---

## Best Practices

1. **Test sempre** su sistema pulito prima di release
2. **Incrementa versione** PRIMA di build
3. **Tag corretto** corrispondente a versione
4. **Release notes** chiare e complete
5. **Installers multipli** se supporti più piattaforme
6. **Backup database** tracking prima di aggiornamenti major

---

## Automazione Futura (Opzionale)

Puoi automatizzare con GitHub Actions:

1. Creare `.github/workflows/release.yml`
2. Build automatico su tag
3. Creazione release automatica
4. Upload installer automatico

Per ora, processo manuale va bene.

---

**Buon rilascio! 🚀**

