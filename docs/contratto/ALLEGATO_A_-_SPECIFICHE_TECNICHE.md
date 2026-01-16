


---

**CONFIDENTIALITY NOTICE**  
**CONFIDENTIAL DOCUMENT – DO NOT DISTRIBUTE WITHOUT AUTHORIZATION**

This document contains proprietary and confidential information of Lucertae S.r.l.s. Unauthorized disclosure, reproduction, or use is strictly prohibited. This business plan is provided for informational purposes only and does not constitute an investment offer.

© 2025 Lucertae S.r.l.s. All rights reserved.

---

# ALLEGATO A - SPECIFICHE TECNICHE

**Software:** Lac Translate - Sistema di Traduzione Offline  
**Riferimento:** Contratto di Sviluppo Software tra LUCERTAE SRLS e Enrico Pascatti



## 1. FUNZIONALITÀ MINIME RICHIESTE

Il Software dovrà garantire le seguenti funzionalità essenziali:

### 1.1. Traduzione Multilingua Offline

- Supporto per 7 lingue: Italiano, Inglese, Francese, Tedesco, Spagnolo, Portoghese, Olandese.
- Traduzione bidirezionale tra tutte le lingue supportate.
- Funzionamento completamente offline, senza necessità di connessione internet dopo l'installazione.

### 1.2. Estrazione Testo (OCR)

- Estrazione del testo da file PDF (anche scannerizzati).
- Estrazione del testo da immagini (formati: JPG, PNG, TIFF, BMP).
- Utilizzo della libreria Tesseract OCR con modelli linguistici per le 7 lingue supportate.

### 1.3. Interfaccia Utente

- Interfaccia grafica moderna sviluppata in Qt.
- Funzionalità drag-and-drop per caricare file.
- Visualizzazione del testo originale e tradotto in pannelli affiancati.
- Possibilità di esportare il testo tradotto in formato TXT, PDF o DOCX.

### 1.4. Installazione

- Installer eseguibile (.exe) per Windows 10 e Windows 11 (64-bit).
- Procedura di installazione guidata e user-friendly.
- Nessuna dipendenza esterna richiesta all'utente finale (tutto incluso nel pacchetto).



## 2. REQUISITI DI PERFORMANCE

### 2.1. Tempi di Risposta

- Avvio dell'applicazione: < 5 secondi su hardware standard.
- Caricamento di un file PDF (< 10 MB): < 3 secondi.
- OCR di una pagina A4 standard (300 dpi): < 10 secondi.
- Traduzione di un testo di 1000 parole: < 15 secondi.

### 2.2. Gestione della Memoria

- Utilizzo della RAM: < 500 MB in condizioni normali.
- Gestione ottimizzata per file di grandi dimensioni (> 50 MB) tramite elaborazione progressiva.

### 2.3. Stabilità

- Nessun crash o blocco dell'applicazione durante l'uso normale.
- Gestione degli errori con messaggi chiari e informativi per l'utente.



## 3. REQUISITI DI INTERFACCIA UTENTE (UI/UX)

### 3.1. Design

- Layout professionale, pulito e moderno.
- Temi personalizzabili: chiaro e scuro.
- Font leggibili e dimensioni adattabili.

### 3.2. Usabilità

- Interfaccia intuitiva, utilizzabile senza formazione specifica.
- Feedback visivo durante le operazioni di lunga durata (barre di progresso, spinner).
- Messaggi di errore chiari e suggerimenti per la risoluzione.

### 3.3. Accessibilità

- Supporto per scorciatoie da tastiera.
- Possibilità di ridimensionare la finestra e adattare il layout.



## 4. REQUISITI DI INSTALLAZIONE E DISTRIBUZIONE

### 4.1. Pacchetto di Installazione

- Formato: Installer eseguibile (.exe) autofirmato.
- Dimensioni: < 500 MB.
- Inclusione di tutti i modelli linguistici e dipendenze.

### 4.2. Compatibilità

- Windows 10 (versione 1809 o successiva).
- Windows 11 (tutte le versioni).
- Architettura: 64-bit (x64).

### 4.3. Disinstallazione

- Procedura di disinstallazione completa e pulita (nessun file residuo).



## 5. REQUISITI OCR (TESSERACT)

### 5.1. Qualità

- Accuratezza OCR: > 95% su testo stampato standard.
- Gestione di documenti scannerizzati con qualità media (200-300 dpi).

### 5.2. Formati Supportati

- PDF (anche multi-pagina).
- Immagini: JPG, PNG, TIFF, BMP.

### 5.3. Lingue

- Modelli Tesseract per le 7 lingue supportate inclusi nel pacchetto.



## 6. REQUISITI ARGOS TRANSLATE

### 6.1. Modelli Linguistici

- Modelli di traduzione per tutte le combinazioni linguistiche richieste.
- Modelli inclusi nel pacchetto di installazione (nessun download esterno).

### 6.2. Qualità della Traduzione

- Traduzione comprensibile e grammaticalmente corretta per testi standard.
- Gestione di termini tecnici e specialistici con dizionari integrati (opzionale).



## 7. REQUISITI DI SICUREZZA E PRIVACY

### 7.1. Architettura Offline

- Nessuna trasmissione di dati a server esterni.
- Nessuna telemetria o raccolta di statistiche d'uso.

### 7.2. Sicurezza del Codice

- Assenza di codice malevolo, backdoor o vulnerabilità note.
- Codice sorgente pulito e verificabile.

### 7.3. Conformità Licenze

- Rispetto delle licenze open-source (Tesseract: Apache 2.0, Argos Translate: MIT).



## 8. DELIVERABLE FINALI

Al termine dello sviluppo, lo Sviluppatore consegnerà:

1. Installer .exe funzionante e testato.
2. Codice sorgente completo su repository GitHub.
3. Script di build e file di configurazione.
4. Documentazione tecnica (architettura, API interne, commenti nel codice).
5. Manuale utente in formato PDF.
6. Video tutorial (almeno 1, durata 5-10 minuti).

---

**Letto, approvato e sottoscritto.**

**Luogo:** [Inserire Luogo]  
**Data:** [Inserire Data]

**Per LUCERTAE SRLS**  
(Legale Rappresentante)

**Per Enrico Pascatti**  
(Lo Sviluppatore)

