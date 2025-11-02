# Guida Primo Versioning e Attivazione Security

Guida passo-passo per:
1. ✅ Generare manifest integrità
2. ✅ Verificare sistema sicurezza
3. ✅ Creare prima release versione
4. ✅ Attivare CI/CD pipeline

---

## Step 1: Preparazione Pre-Versioning

### 1.1 Verifica versione corrente

```bash
python app/version.py
```

Verifica che la versione sia corretta (es. `2.0.0`).

### 1.2 Aggiorna CHANGELOG

Edita `changelog/CHANGELOG.md` e aggiungi entry per la release:

```markdown
## [2.0.0] - 2025-01-15

### Added
- Sistema licenze completo
- Security system (integrity checker, secure storage)
- CI/CD pipeline automatizzata
- Update checker da GitHub Releases

### Changed
- Miglioramenti traduzione PDF
- UI improvements

### Fixed
- Bug fixes vari
```

### 1.3 Commit preparazione

```bash
git add changelog/CHANGELOG.md app/version.py
git commit -m "Prepare for v2.0.0 release"
git push origin main
```

---

## Step 2: Genera Integrity Manifest

### 2.1 Crea manifest file critici

```bash
python scripts/development/create_integrity_manifest.py
```

**Output atteso:**
```
============================================================
LAC TRANSLATE - Integrity Manifest Generator
============================================================

Creating integrity manifest for critical files...

✓ Manifest created: security/file_manifest.json

Files in manifest:
  app/license_manager.py: abc123def456...
  app/license_activation.py: 789xyz...
  app/pdf_translator_gui.py: def456abc123...
  app/integrity_checker.py: xyz789...
  app/security_validator.py: 456def...
```

### 2.2 Verifica manifest creato

```bash
# Windows PowerShell
Get-Content security\file_manifest.json | ConvertFrom-Json | Format-List

# Linux/macOS
cat security/file_manifest.json | python -m json.tool
```

**Verifica che contenga:**
- Hash SHA256 per ogni file critico
- Formato JSON valido

### 2.3 Commit manifest

```bash
git add security/file_manifest.json
git commit -m "Add integrity manifest for v2.0.0"
git push origin main
```

**⚠️ IMPORTANTE:** Il manifest va committato perché serve all'application per verificare integrità.

---

## Step 3: Verifica Sistema Sicurezza

### 3.1 Test Security Manager

```bash
python -c "from security import get_security_manager; sm = get_security_manager(); print('✓ Security Manager OK')"
```

### 3.2 Test Integrity Checker

```bash
python -c "from app.integrity_checker import IntegrityChecker; from pathlib import Path; ic = IntegrityChecker(); print('✓ Integrity Checker OK'); print(f'Status: {ic.check_critical_files()}')"
```

### 3.3 Test Security Validator

```bash
python -c "from app.security_validator import get_security_validator; from pathlib import Path; sv = get_security_validator(); results = sv.perform_security_checks(); print('✓ Security Validator OK'); print(f'Status: {results[\"overall_status\"]}')"
```

### 3.4 Test Secure Storage

```bash
python -c "from app.secure_storage import SecureStorage; ss = SecureStorage(); ss.save_secure_value('test_key', 'test_value', encrypt=True); value = ss.load_secure_value('test_key'); print(f'✓ Secure Storage OK: {value}')"
```

### 3.5 Test applicazione completa

```bash
# Avvia applicazione (deve passare security checks)
python app/pdf_translator_gui.py
```

**Verifica:**
- Nessun errore all'avvio
- Log `logs/security.log` creato (se disponibile)
- Application si avvia correttamente

---

## Step 4: Creazione Tag Versione

### 4.1 Crea tag git

```bash
# Tag formato: vMAJOR.MINOR.PATCH
git tag -a v2.0.0 -m "Release v2.0.0 - First production release with security system"

# Verifica tag creato
git tag -l "v*"
```

### 4.2 Push tag su GitHub

```bash
git push origin v2.0.0
```

**Oppure push tutti i tag:**
```bash
git push origin --tags
```

---

## Step 5: Verifica CI/CD Pipeline

### 5.1 Controlla GitHub Actions

1. Vai su: https://github.com/Lucertae/documents_translator/actions
2. Dovresti vedere workflow **"Build and Release"** in esecuzione
3. Attendi completamento (5-10 minuti)

**Cosa succede automaticamente:**
- ✅ Build Windows installer
- ✅ Verifica build output
- ✅ Crea GitHub Release
- ✅ Upload installer alla release

### 5.2 Verifica Release creata

1. Vai su: https://github.com/Lucertae/documents_translator/releases
2. Dovresti vedere release **v2.0.0**
3. Verifica che installer sia presente

---

## Step 6: Test Release

### 6.1 Download release (opzionale)

Scarica installer dalla release GitHub per testare.

### 6.2 Verifica update checker

L'applicazione dovrebbe:
- Trovare release v2.0.0 su GitHub
- Mostrare notifica aggiornamento disponibile

---

## Step 7: Verifica Security Logging

### 7.1 Controlla security log

```bash
# Windows PowerShell
Get-Content logs\security.log -Tail 20

# Linux/macOS
tail -20 logs/security.log
```

**Dovresti vedere:**
```
[2025-01-15T10:30:45] [INFO] [SECURITY_CHECK] All security checks passed
[2025-01-15T10:30:46] [INFO] [EXECUTABLE_HASH] Executable hash: abc123...
[2025-01-15T10:30:47] [INFO] [INTEGRITY_CHECK] All critical files verified
```

---

## Checklist Completa

Prima del tag, verifica:

- [ ] Versione corretta in `app/version.py`
- [ ] CHANGELOG aggiornato
- [ ] Integrity manifest generato (`security/file_manifest.json`)
- [ ] Security tests passati
- [ ] Application si avvia senza errori
- [ ] Security log creato correttamente
- [ ] Commit preparazione fatti
- [ ] Tag creato con messaggio descrittivo
- [ ] Tag pushato su GitHub
- [ ] GitHub Actions workflow in esecuzione
- [ ] Release creata automaticamente

---

## Troubleshooting

### "Manifest not found" all'avvio

**Causa:** Manifest non creato o non committato.

**Soluzione:**
```bash
python scripts/development/create_integrity_manifest.py
git add security/file_manifest.json
git commit -m "Add integrity manifest"
git push origin main
```

### "Security modules not available"

**Causa:** Dipendenze non installate.

**Soluzione:**
```bash
pip install -r requirements.txt
```

Verifica che `cryptography` e `psutil` siano installati.

### GitHub Actions build fallisce

**Causa:** Possibili problemi:
- InnoSetup non configurato (per installer Windows)
- Dipendenze mancanti
- Errori nel build script

**Soluzione:**
1. Controlla log GitHub Actions
2. Verifica che `build.py` funzioni localmente
3. Testa build locale: `python build.py`

### Release non creata automaticamente

**Causa:** Workflow non triggerato o fallito.

**Soluzione:**
1. Verifica formato tag: deve essere `v*.*.*` (es. `v2.0.0`)
2. Controlla GitHub Actions per errori
3. Puoi creare release manualmente su GitHub

---

## Prossimi Passi Dopo Prima Release

1. **Testa installer** scaricato dalla release
2. **Verifica aggiornamento** automatico funziona
3. **Monitora security.log** per eventi
4. **Prepara prossima versione** quando necessario

---

## Comandi Rapidi Riepilogo

```bash
# 1. Genera manifest
python scripts/development/create_integrity_manifest.py

# 2. Test security
python -c "from app.integrity_checker import IntegrityChecker; from pathlib import Path; ic = IntegrityChecker(); print(ic.check_critical_files())"

# 3. Crea tag
git tag -a v2.0.0 -m "Release v2.0.0"

# 4. Push tag
git push origin v2.0.0

# 5. Verifica Actions
# Vai su: https://github.com/Lucertae/documents_translator/actions
```

---

**Pronto per la prima release! 🚀**

