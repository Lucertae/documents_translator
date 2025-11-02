# Generatore Chiavi Seriali - LAC TRANSLATE

## Utilizzo

Esegui lo script per generare chiavi seriali da distribuire ai clienti:

```bash
python app/generate_license.py
```

## Modalità

### 1. Singola Chiave
Genera una singola chiave seriale con informazioni cliente opzionali.

### 2. Multiple Chiavi (Bulk)
Genera un numero specificato di chiavi seriali per distribuzione di massa.

## Formato Chiave

Le chiavi seguono il formato: `LAC-XXXX-XXXX-XXXX`

Dove XXXX sono 4 caratteri alfanumerici (esclusi 0, O, I, 1 per evitare confusione).

## Output

Le chiavi generate vengono salvate in:
- `license_keys/` directory
- File formato `.txt` per singole chiavi
- File formato `.json` e `.txt` per bulk

## Sicurezza

- Ogni chiave è unica e generata casualmente
- Hash SHA256 viene generato per ogni chiave
- Le chiavi sono legate all'hardware del cliente all'attivazione

## Note

- Conserva sempre una copia delle chiavi generate
- Non condividere le chiavi pubblicamente
- Usa un database per tracciare chiavi vendute (opzionale)

