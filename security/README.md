# 🔒 Security Module - LAC TRANSLATE

Modulo di sicurezza per protezione dati e integrità applicazione.

## Funzionalità

### 1. Encryption Dati Sensibili
- Criptazione dati con Fernet (cryptography)
- Chiavi generate automaticamente e salvate in modo sicuro
- Supporto per criptare/decryptare qualsiasi dato stringa

### 2. Verifica Integrità File
- Calcolo hash SHA256 per verificare integrità file
- Confronto hash per rilevare modifiche ai file
- Protezione contro file corrotti o manomessi

### 3. Storage Sicuro
- Salvataggio dati sensibili in formato criptato
- File di configurazione protetto
- Accesso controllato ai dati

## Utilizzo

```python
from security import get_security_manager

# Ottieni istanza manager sicurezza
security = get_security_manager()

# Cripta dati
encrypted = security.encrypt_data("dato sensibile")
decrypted = security.decrypt_data(encrypted)

# Salva dati sicuri
security.save_secure_data("api_key", "chiave_segreta", encrypt=True)
api_key = security.load_secure_data("api_key", decrypt=True)

# Verifica integrità file
file_hash = security.compute_file_hash(Path("file.pdf"))
is_valid = security.verify_file_integrity(Path("file.pdf"), expected_hash)

# Verifica stato sicurezza
status = security.check_security_status()
```

## File

- `security_manager.py` - Manager principale sicurezza
- `security_config.json` - Configurazione dati criptati (generato automaticamente)
- `.encryption_key` - Chiave di encryption (generata automaticamente, NON condividere)

## Note Sicurezza

⚠️ **IMPORTANTE**: 
- Il file `.encryption_key` contiene la chiave di decriptazione
- NON condividere questo file o perdere l'accesso
- Backup regolari della cartella `security/` se necessario
- Il file `.encryption_key` è protetto con permessi ristretti (solo su Unix)

## Dipendenze

- `cryptography>=41.0.0` - Per encryption/decryption

