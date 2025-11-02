# Implementazione Sicurezza - LAC TRANSLATE

Documentazione completa del sistema di sicurezza implementato.

---

## Componenti Sicurezza

### 1. Security Manager (`security/security_manager.py`)

**Funzionalità:**
- ✅ Encryption/decryption dati con Fernet (cryptography)
- ✅ Generazione e gestione chiavi encryption
- ✅ Calcolo hash SHA256 per integrità file
- ✅ Storage sicuro dati criptati

**Uso:**
```python
from security import get_security_manager

security = get_security_manager()
encrypted = security.encrypt_data("dato sensibile")
decrypted = security.decrypt_data(encrypted)
```

---

### 2. Integrity Checker (`app/integrity_checker.py`)

**Funzionalità:**
- ✅ Verifica integrità file critici all'avvio
- ✅ Confronto hash SHA256
- ✅ Manifest file per file critici
- ✅ Protezione contro tampering

**File Verificati:**
- `app/license_manager.py`
- `app/license_activation.py`
- `app/pdf_translator_gui.py`
- `app/integrity_checker.py`
- `app/security_validator.py`

**Come Funziona:**
1. Durante build, crea manifest hash file critici
2. All'avvio, verifica hash file contro manifest
3. Se hash non corrisponde → file modificato → warning/log

**Creare Manifest:**
```bash
python scripts/development/create_integrity_manifest.py
```

---

### 3. Security Validator (`app/security_validator.py`)

**Funzionalità:**
- ✅ Rilevamento debugger
- ✅ Rilevamento VM/sandbox
- ✅ Verifica integrità eseguibile
- ✅ Controllo permessi file critici
- ✅ Security logging

**Controlli Eseguiti:**
1. **Debugger Detection**: Verifica se Python debugger attivo
2. **VM Detection**: Rileva se in esecuzione in VM (VirtualBox, VMware, etc.)
3. **Suspicious Processes**: Cerca processi sospetti (Wireshark, Fiddler, debuggers)
4. **Executable Integrity**: Verifica hash eseguibile (se PyInstaller)
5. **File Permissions**: Controlla permessi file licenza

**Logging:**
Tutti gli eventi sicurezza vengono loggati in `logs/security.log`

---

### 4. Secure Storage (`app/secure_storage.py`)

**Funzionalità:**
- ✅ Storage sicuro con encryption per dati sensibili
- ✅ Encryption automatica valori salvati
- ✅ Decryption trasparente al caricamento

**Uso:**
```python
from secure_storage import SecureStorage

storage = SecureStorage()
storage.save_secure_value('api_key', 'secret123', encrypt=True)
value = storage.load_secure_value('api_key')  # Decripta automaticamente
```

**Integrazione Licenze:**
Il `license_manager.py` usa `SecureStorage` per criptare la serial key della licenza.

---

## Flusso Sicurezza All'Avvio

1. **Integrity Check** (`check_security_integrity`)
   - Verifica hash file critici
   - Warning se file modificati (non-strict mode)

2. **Security Validation** (`SecurityValidator`)
   - Controlla debugger
   - Rileva VM/sandbox
   - Verifica permessi file licenza
   - Log eventi sicurezza

3. **License Check** (`check_license_on_startup`)
   - Carica licenza da secure storage
   - Verifica hardware binding
   - Verifica hash licenza
   - Mostra dialog attivazione se necessario

---

## Protezione Dati Sensibili

### Licenze

**Stored In:**
- `license/license.json` - Dati licenza (hash, hw_id, etc.)
- `security/secure_storage.json` - Serial key criptata (se use_secure_storage=True)

**Protezione:**
- Serial key criptata con Fernet
- Hash licenza verifica integrità
- Hardware binding previene trasferimento

**Esempio:**
```json
// license/license.json
{
  "serial_key": "[ENCRYPTED]",
  "license_hash": "abc123...",
  "hw_id": "machine123",
  "activated": true
}

// security/secure_storage.json
{
  "license_serial": {
    "encrypted": true,
    "value": "gAAAAABh..."  // Encrypted Fernet
  }
}
```

---

### File Critici

**Manifest:**
- `security/file_manifest.json` - Hash SHA256 file critici

**Protezione:**
- Verifica hash all'avvio
- Warning se file modificati
- Log eventi integrità

---

## Security Logging

**File:** `logs/security.log`

**Eventi Loggati:**
- Integrity check results
- Debugger detection
- VM detection
- License security warnings
- File permission issues
- Tampering attempts

**Formato:**
```
[2025-01-15T10:30:45] [INFO] [SECURITY_CHECK] All security checks passed
[2025-01-15T10:31:12] [WARNING] [DEBUGGER_DETECTED] Python debugger detected
[2025-01-15T10:32:00] [WARNING] [LICENSE_SECURITY_WARNING] License file has insecure permissions
```

---

## Anti-Tampering

### 1. Integrity Verification

File critici hanno hash verificato all'avvio. Modifiche vengono rilevate.

### 2. License Hash

Licenza ha hash calcolato da serial_key + hw_id. Modifiche invalidano licenza.

### 3. Hardware Binding

Licenza legata a hardware ID specifico. Trasferimento su altro PC invalida licenza.

### 4. Secure Storage Encryption

Serial key salvata criptata. Accesso diretto a file non rivela chiave.

### 5. File Permissions

Verifica che file licenza non siano world-writable (Unix) o accessibili (Windows).

---

## Configurazione

### Abilitare Secure Storage per Licenze

In `license_manager.py`, `save_license()` ha parametro `use_secure_storage=True` (default).

### Strict Mode Integrity Check

In `integrity_checker.py`, `verify_integrity(strict=True)` blocca avvio se file modificati.

**Attenzione:** Strict mode può bloccare anche aggiornamenti legittimi. Usare solo per build distribuiti.

---

## Build e Distribuzione

### 1. Creare Integrity Manifest

Prima di build distribuzione:
```bash
python scripts/development/create_integrity_manifest.py
```

Questo crea `security/file_manifest.json` con hash file critici.

### 2. Build Distribuzione

Il manifest viene incluso nel build. All'avvio, integrità viene verificata.

### 3. Secure Storage Key

**IMPORTANTE:** La chiave encryption (`security/.encryption_key`) è per-installazione.

**Non** condividere questa chiave tra installazioni diverse o la decryption fallirà.

Per distribuzione:
- Ogni installazione genera la propria chiave
- Secure storage è locale alla macchina

---

## Limitazioni e Considerazioni

### 1. Source Code Visibility

Il codice è pubblico su GitHub. L'integrità check è più per:
- Rilevare modifiche accidentali
- Verificare che build non sia corrotto
- Non è protezione forte contro reverse engineering (codice è pubblico)

### 2. Encryption Key Storage

La chiave è salvata localmente. Se qualcuno ha accesso al file system, può accedere ai dati criptati.

**Mitigazione:**
- Permessi file ristretti (Unix)
- Encryption è principalmente per dati at-rest (non in memoria)
- Hardware binding aggiunge livello protezione

### 3. Debugger Detection

Il rilevamento debugger è basic. Expert reverse engineer può aggirarlo.

**Mitigazione:**
- Più per logging che blocco
- Non blocca esecuzione (solo warning)

---

## Best Practices

1. **Non committare file sicurezza:**
   - `.gitignore` esclude `security/.encryption_key`, `secure_storage.json`, etc.

2. **Monitora security.log:**
   - Controlla regolarmente per eventi sospetti

3. **Usa secure storage per dati sensibili:**
   - API keys, serial keys, password

4. **Verifica integrità dopo aggiornamenti:**
   - Aggiorna manifest dopo modifiche file critici

5. **Backup chiave encryption:**
   - Se persa, dati criptati sono irrecuperabili
   - Backup solo se necessario (per installazione specifica)

---

## Troubleshooting

### "Integrity check found modified files"

**Causa:** File critici modificati dopo manifest creation.

**Soluzione:**
- Se modifica legittima: ricrea manifest
- Se sospetto tampering: verifica origine modifiche

### "Cannot decrypt license serial key"

**Causa:** Chiave encryption persa o diversa.

**Soluzione:**
- Re-attiva licenza (regenera storage)
- Verifica che `.encryption_key` esista

### "License file has insecure permissions"

**Causa:** File licenza world-writable o accessibile.

**Soluzione:**
- Su Unix: `chmod 600 license/license.json`
- Verifica permessi file system

---

## Stato Implementazione

✅ **Security Manager**: Implementato  
✅ **Integrity Checker**: Implementato  
✅ **Security Validator**: Implementato  
✅ **Secure Storage**: Implementato  
✅ **License Encryption**: Integrato  
✅ **Security Logging**: Implementato  
✅ **Anti-Tampering**: Implementato (base)  

⚠️ **Code Obfuscation**: Non implementato (codice pubblico)  
⚠️ **Strong Anti-Debug**: Non implementato (basic detection)  
⚠️ **Online Validation**: Non implementato (offline-first)  

---

**La sicurezza è implementata con approccio bilanciato:**
- Protezione dati sensibili (encryption)
- Verifica integrità (hash)
- Hardware binding (licenze)
- Security logging (audit)

**Limitazioni accettabili per software con codice pubblico e distribuzione locale.**

