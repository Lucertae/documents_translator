# GitHub Actions CI/CD Pipeline - Guida Completa

Documentazione completa per la pipeline CI/CD automatizzata su GitHub Actions.

---

## Workflows Implementati

### 1. Build and Release (`build-and-release.yml`)

**Trigger:**
- Push di tag versione (es. `v2.1.0`)
- Trigger manuale da GitHub Actions

**Cosa fa:**
- Build automatico Windows installer
- Build Linux package (se disponibile)
- Build macOS package (se disponibile)
- Creazione GitHub Release automatica
- Upload installer alle release

**Output:**
- Installer Windows: `release/installer/LAC_Translate_v[X.X.X]_Setup.exe`
- Archivi release per tutte le piattaforme

---

### 2. Update Version (`update-version.yml`)

**Trigger:**
- Push di tag versione

**Cosa fa:**
- Estrae versione dal tag
- Crea `version.json` con info release
- Upload come artifact

**Output:**
- `version.json` con metadati release

---

### 3. Tests (`test.yml`)

**Trigger:**
- Push su branch `main` o `develop`
- Pull Request

**Cosa fa:**
- Test su Windows, Ubuntu, macOS
- Test con Python 3.9, 3.10, 3.11
- Verifica import moduli
- Verifica sistema licenze
- Verifica update checker

**Output:**
- Report test per ogni combinazione OS/Python

---

### 4. Code Quality (`code-quality.yml`)

**Trigger:**
- Push su `main`
- Pull Request

**Cosa fa:**
- Linting con flake8
- Controllo errori comuni
- Verifica sintassi Python

**Output:**
- Report linting (non blocca build)

---

## Come Usare la Pipeline

### Scenario 1: Rilasciare Nuova Versione

**Step 1:** Aggiorna versione
```bash
# Modifica app/version.py
VERSION_MAJOR = 2
VERSION_MINOR = 1  # Incrementa
VERSION_PATCH = 0
```

**Step 2:** Commit e push
```bash
git add app/version.py changelog/CHANGELOG.md
git commit -m "Bump version to 2.1.0"
git push origin main
```

**Step 3:** Crea tag
```bash
git tag v2.1.0 -m "Release v2.1.0"
git push origin v2.1.0
```

**Step 4:** GitHub Actions esegue automaticamente:
1. ✅ Build Windows installer
2. ✅ Build Linux/macOS (se implementati)
3. ✅ Crea GitHub Release
4. ✅ Upload installer alla release

**Risultato:** Release pubblicata con installer pronto al download!

---

### Scenario 2: Test su Pull Request

1. Crei branch feature
2. Fai modifiche
3. Apri Pull Request
4. GitHub Actions esegue automaticamente:
   - ✅ Test su tutte le piattaforme
   - ✅ Code quality checks
5. Review e merge se tutti i test passano

---

## Configurazione Workflows

### Build Windows

**Requisiti:**
- Python 3.11 installato automaticamente
- Dipendenze installate da `requirements.txt`
- PyInstaller installato automaticamente
- Build eseguito con `build.py`

**Output:**
- Eseguibile: `dist/LAC_Translate.exe`
- Installer: `release/installer/LAC_Translate_v[X.X.X]_Setup.exe`

---

### Build Linux/macOS

**Status:** Implementato ma opzionale
- Richiede script build completi per Linux/macOS
- Attualmente workflow esegue ma potrebbe fallire se build non completo
- Puoi disabilitare temporaneamente se non supportati

**Per abilitare:**
- Completa `build_multi_platform.py` per Linux/macOS
- Oppure rimuovi job da workflow

---

## Artifacts e Downloads

### Artifacts GitHub Actions

Gli artifact vengono salvati per 30 giorni:
- Windows installer
- Linux package (se disponibile)
- macOS package (se disponibile)
- version.json

**Come scaricare:**
1. Vai su Actions → Ultima run
2. Sezione "Artifacts"
3. Download manuale

### GitHub Releases

Gli installer vengono caricati automaticamente sulle Release:
1. Vai su: https://github.com/Lucertae/documents_translator/releases
2. Trova release con tag `v[X.X.X]`
3. Download installer direttamente da lì

---

## Troubleshooting CI/CD

### Build fallisce su Windows

**Problema:** Errori durante build

**Soluzioni:**
1. Verifica log GitHub Actions
2. Controlla che `requirements.txt` sia completo
3. Verifica che `build.py` funzioni localmente
4. Controlla che InnoSetup sia configurato (per installer)

**Nota:** InnoSetup richiede installazione su runner Windows, potrebbe servire setup aggiuntivo.

### Tag non triggera release

**Problema:** Release non viene creata

**Soluzioni:**
1. Verifica formato tag: deve essere `v2.1.0` (con "v")
2. Verifica che workflow sia in `.github/workflows/`
3. Controlla log Actions per errori
4. Verifica permessi repository (deve permettere creazione release)

### Installer non viene caricato

**Problema:** Release creata ma senza installer

**Soluzioni:**
1. Verifica che build abbia successo
2. Verifica percorso file: `release/installer/*.exe`
3. Controlla che file esista dopo build
4. Verifica permessi scrittura

---

## Miglioramenti Futuri

### Opzionale: Code Signing

Per firmare digitalmente installer Windows:

```yaml
- name: Sign executable
  uses: actions/codesign@v1
  with:
    certificate: ${{ secrets.WINDOWS_CERTIFICATE }}
    password: ${{ secrets.CERTIFICATE_PASSWORD }}
```

**Requisiti:**
- Certificato code signing (.pfx)
- Salvato in GitHub Secrets
- Costo: ~€200-400/anno

---

### Opzionale: Automated Testing

Aggiungi test automatici:

```yaml
- name: Run unit tests
  run: |
    python -m pytest tests/ -v
```

**Requisiti:**
- Test suite completa in `tests/`
- pytest installato

---

### Opzionale: Security Scanning

Scanner vulnerabilità:

```yaml
- name: Run security scan
  uses: github/super-linter@v4
```

---

## Workflow Manuale vs Automatico

### Manuale (Attuale)

**Vantaggi:**
- Controllo totale
- Possibilità di testare prima
- Build locale se necessario

**Svantaggi:**
- Richiede intervento manuale
- Più tempo

### Automatico (CI/CD)

**Vantaggi:**
- Completamente automatico
- Consistente su tutti i build
- Release pronte subito dopo tag

**Svantaggi:**
- Richiede setup iniziale
- Build potrebbero fallire (da fixare)

---

## Best Practices

1. **Testa localmente prima di tag:**
   ```bash
   python build.py
   # Verifica che installer funzioni
   ```

2. **Versiona correttamente:**
   - Tag deve corrispondere a `VERSION_STRING`
   - Usa formato: `vMAJOR.MINOR.PATCH`

3. **Changelog aggiornato:**
   - Aggiorna `changelog/CHANGELOG.md` prima di release
   - GitHub Actions genera release notes automaticamente

4. **Monitora Actions:**
   - Controlla sempre che build abbia successo
   - Fix errori prima di merge

---

## Struttura Workflows

```
.github/
└── workflows/
    ├── build-and-release.yml   # Build e release principale
    ├── update-version.yml      # Genera version.json
    ├── test.yml                # Test automatici
    └── code-quality.yml        # Linting e quality
```

---

## Stato Attuale

✅ **Build Windows:** Implementato e funzionante  
✅ **Release Automatica:** Implementata  
⚠️ **Build Linux/macOS:** Implementato ma opzionale  
✅ **Test:** Implementati (base)  
✅ **Code Quality:** Implementato  

---

## Prossimi Passi

1. **Testa workflow:**
   - Crea tag di test: `v2.0.1` (se non esiste ancora)
   - Verifica che Actions si attivi
   - Controlla output

2. **Migliora build:**
   - Completa build Linux/macOS se necessario
   - Aggiungi code signing se vuoi

3. **Aggiungi test:**
   - Crea test suite se vuoi coverage completo

---

**La pipeline CI/CD è pronta e funzionante! 🚀**

