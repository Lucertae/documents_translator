---

**CONFIDENTIALITY NOTICE**  
**CONFIDENTIAL DOCUMENT – DO NOT DISTRIBUTE WITHOUT AUTHORIZATION**

This document contains proprietary and confidential information of Lucertae S.r.l.s. Unauthorized disclosure, reproduction, or use is strictly prohibited. This business plan is provided for informational purposes only and does not constitute an investment offer.

© 2025 Lucertae S.r.l.s. All rights reserved.

---

# CONTRATTO DI SVILUPPO SOFTWARE, CESSIONE DEI DIRITTI, ASSISTENZA E ROYALTIES

**Tra:**

**LUCERTAE SRLS**, con sede legale in Piazza Carlo Caneva 5, 20154 Milano (MI), Partita IVA 14388990963 e Codice Fiscale 14388990963, in persona del suo legale rappresentante pro tempore (di seguito, "Committente"),

**e**

**Enrico Pascatti**, residente in [Inserire Indirizzo Completo], Codice Fiscale [Inserire Codice Fiscale] (di seguito, "Sviluppatore").

(di seguito congiuntamente le "Parti" e singolarmente la "Parte")

## PREMESSO CHE:

**A)** Il Committente è titolare di un software in stato di Minimum Viable Product (MVP), denominato "Lac Translate", destinato alla traduzione di documenti in modalità interamente offline, e intende affidarne il completamento e la commercializzazione allo Sviluppatore, come da specifiche tecniche definite nell'Allegato A.

**B)** Lo Sviluppatore dichiara di possedere le competenze tecniche, l'esperienza e le risorse necessarie per eseguire l'incarico in modo professionale e a regola d'arte, in conformità con le migliori pratiche del settore.

**C)** Le Parti intendono disciplinare in modo chiaro, completo ed esaustivo ogni aspetto del loro rapporto, inclusi lo sviluppo, la cessione dei diritti di proprietà intellettuale, le modalità di assistenza, il regime delle royalties e gli obblighi di riservatezza.

**TUTTO CIÒ PREMESSO, SI CONVIENE E STIPULA QUANTO SEGUE:**

## Art. 1 - Oggetto del Contratto

**1.1.** Il presente contratto ha per oggetto l'incarico conferito dal Committente allo Sviluppatore, che accetta, di svolgere le attività di sviluppo, completamento e ottimizzazione del software "Lac Translate" (di seguito, il "Software"), nonché la fornitura dei servizi accessori di assistenza, manutenzione e formazione, come meglio specificato nel presente contratto e nei suoi allegati.

**1.2. Specifiche Tecniche:** Le funzionalità, i requisiti di performance, i requisiti di interfaccia utente (UI), i requisiti di installazione e ogni altro dettaglio tecnico del Software sono definiti nell'Allegato A (Specifiche Tecniche), che costituisce parte integrante e sostanziale del presente contratto.

**1.3. Architettura Offline:** Lo Sviluppatore garantisce che l'architettura del Software sarà interamente full offline. Il Software, una volta installato, dovrà operare senza alcuna necessità di connessione a server esterni o servizi cloud, assicurando che nessun dato, testo o informazione venga trasmesso al di fuori dell'ambiente locale del cliente. Tale caratteristica è elemento essenziale del presente contratto.



## Art. 2 - Gestione del Codice e Repository

**2.1. Repository Git:** Tutto il codice sorgente del Software, inclusi gli sviluppi futuri, dovrà essere gestito e mantenuto dallo Sviluppatore su un repository Git privato, accessibile al Committente. Il repository ufficiale del progetto è stabilito al seguente indirizzo: https://github.com/Lucertae/documents_translator.git.

**2.2. Obbligo di Aggiornamento:** Lo Sviluppatore si impegna ad aggiornare il repository con cadenza almeno settimanale, documentando i commit in modo chiaro e professionale, con messaggi descrittivi delle modifiche apportate.

**2.3. Consegna Finale dell'Ambiente:** Al termine dello sviluppo e al momento della consegna finale, lo Sviluppatore si impegna a consegnare al Committente:

- a) Il codice sorgente completo e commentato.
- b) L'intero ambiente di build, inclusi script di compilazione, file di configurazione e dipendenze.
- c) La documentazione tecnica completa per la compilazione e il deployment.
- d) I modelli linguistici di Argos Translate e ogni altro asset necessario.



## Art. 3 - Conformità delle Licenze Open-Source

**3.1. Dichiarazione di Conformità:** Lo Sviluppatore dichiara e garantisce che tutte le librerie open-source utilizzate nel Software (incluse Tesseract OCR e Argos Translate) sono compatibili con l'uso commerciale del Software e non impongono vincoli di licenza che possano limitare i diritti del Committente.

**3.2. Divieto di Licenze Copyleft Invasive:** Lo Sviluppatore si impegna a non utilizzare librerie soggette a licenze copyleft invasive (quali GPL versione 3, AGPL o simili) che possano richiedere la divulgazione del codice sorgente del Software o imporre vincoli alla sua commercializzazione.

**3.3. Responsabilità:** Lo Sviluppatore assume piena responsabilità per la verifica della compatibilità delle licenze e si impegna a manlevare il Committente da qualsiasi pretesa di terzi derivante dalla violazione di licenze open-source.

## Art. 4 - Presenza Personale e Divieto di Subappalto (Key Man Clause)

**4.1. Presenza Personale:** Lo Sviluppatore si impegna a svolgere personalmente le attività critiche di sviluppo e assistenza oggetto del presente contratto. È fatto divieto allo Sviluppatore di delegare a terzi, subappaltare o affidare a collaboratori esterni le attività principali senza il preventivo consenso scritto del Committente.

**4.2. Collaboratori Secondari:** Lo Sviluppatore potrà avvalersi di collaboratori esclusivamente per attività accessorie e non critiche, previa comunicazione al Committente e mantenendo la piena responsabilità del loro operato.



## Art. 5 - Milestone, Consegna e Accettazione

**5.1. Milestone di Sviluppo:** Lo sviluppo del Software seguirà le milestone definite nell'Allegato B (Tempi e Milestone). Per ciascuna milestone sono indicati i deliverable attesi e le scadenze.


**5.2. Procedura di Accettazione:** Per ogni deliverable, il Committente avrà a disposizione 10 (dieci) giorni lavorativiper effettuare i test di collaudo e verificare la conformità alle specifiche. L'esito dovrà essere comunicato per iscritto:

- a) **Accettazione:** Se il deliverable è conforme, si intende accettato.
- b) **Accettazione Tacita:** In caso di mancata comunicazione entro il termine di 10 giorni, il deliverable si intende tacitamente accettato.
- c) **Rifiuto Motivato:** In caso di vizi o non conformità, il Committente dovrà fornire un report dettagliato e riproducibile dei problemi riscontrati. Lo Sviluppatore avrà 15 (quindici) giorni lavorativi per correggere i vizi e sottoporre nuovamente il deliverable a collaudo.


**5.3. Penali per Ritardi:** In caso di ritardo nella consegna di una milestone per cause imputabili allo Sviluppatore, sarà applicata una penale pari al 2% (due percento) del valore della milestone per ogni settimana di ritardo, fino a un massimo del 20% (venti percento) del valore della stessa. Le penali non si applicano in caso di ritardi dovuti a richieste di modifica del Committente o a cause di forza maggiore.



## Art. 6 - Change Request e Modifiche Aggiuntive

**6.1. Gestione delle Modifiche: Qualsiasi richiesta di modifica o integrazione alle specifiche tecniche concordate (change request) dovrà essere formalizzata per iscritto dal Committente.


**6.2. Valutazione e Quotazione: Lo Sviluppatore valuterà l'impatto della change request e fornirà entro 5 (cinque) giorni lavorativi una stima dei tempi e dei costi aggiuntivi. La change request si intenderà approvata solo previo accordo scritto tra le Parti.


**6.3. Esclusioni: Sono escluse dal presente contratto e considerate extra-scope tutte le funzionalità, integrazioni o personalizzazioni non espressamente previste nell'Allegato A.



## Art. 7 - Corrispettivo e Modalità di Pagamento

**7.1. Compenso Fisso: Per le attività di sviluppo, il Committente corrisponderà allo Sviluppatore un compenso totale di € 5.000,00(cinquemila/00), al lordo di eventuali ritenute di legge, erogato come segue:

- a) Acconto: € 3.000,00 alla sottoscrizione del presente contratto.
- b) Saldo: € 2.000,00 all'accettazione finale del Software.


**7.2. Modalità di Pagamento: I pagamenti avverranno tramite bonifico bancario entro 5 (cinque) giorni lavorativi dalla ricezione della relativa fattura.



## Art. 8 - Regime delle Royalties e Opzione di Buyout
**8.1. Royalties:** A titolo di compenso variabile, il Committente riconosce allo Sviluppatore una royalty pari al 25% (venticinque percento) dei ricavi netti derivanti dalla vendita di ogni licenza del Software. Per "ricavi netti" si intendono gli importi effettivamente incassati dal Committente, al netto di IVA, imposte, commissioni di vendita e sconti.


**8.2. Rendicontazione e Pagamento: Il Committente fornirà allo Sviluppatore un report mensile delle vendite. Le royalties maturate verranno ridistribuite allo Sviluppatore con cadenza trimestrale, entro 30 giorni dalla fine di ogni trimestre solare (31 marzo, 30 giugno, 30 settembre, 31 dicembre), tramite bonifico bancario.


**8.3. Opzione di Buyout: A partire dal 25° mese dalla data della prima vendita, il Committente avrà il diritto irrevocabile di acquistare la totalità dei diritti di royalty dello Sviluppatore ("buyout"). Il prezzo di buyout sarà calcolato come il maggiore tra i seguenti importi:

- a) Una somma pari a3 (tre) volte l'ammontare totale delle royaltiescorrisposte allo Sviluppatore nei 12 mesi precedenti l'esercizio dell'opzione.
- b) Un importo minimo garantito di€ 4.000,00 (quattromila/00).

Il prezzo di buyout non potrà in ogni caso superare l'importo massimo di **€ 30.000,00** (trentamila/00). Il Committente dovrà comunicare la volontà di esercitare l'opzione con un preavviso di 60 giorni. Il pagamento del buyout estingue definitivamente ogni diritto dello Sviluppatore a future royalties.


## Art. 9 - Assistenza, Manutenzione e Formazione
**9.1. Assistenza Obbligatoria (Primi 24 Mesi): Per i primi 24 (ventiquattro) mesidalla data di accettazione finale del Software, lo Sviluppatore è obbligato a fornire un servizio di assistenza tecnica continuativa, a fronte del riconoscimento della royalty del 25%. Tale servizio include:

- a) 15 (quindici) ore di supporto mensili, cumulabili per un massimo di 2 (due) mesi consecutivi (es. le ore non usate a gennaio possono essere usate a febbraio, ma non a marzo).
- b) Tempi di Risposta: Presa in carico delle richieste entro 24 ore lavorative e risoluzione dei bug critici entro 72 ore lavorative.
- c) Attività Incluse: Bug fixing, aggiornamenti minori, supporto all'integrazione, ottimizzazioni di performance.


**9.2. Assistenza Facoltativa (Dopo 24 Mesi): Allo scadere del 24° mese, lo Sviluppatore potrà scegliere se:

- a) Continuare l'assistenza: Mantenendo le stesse condizioni e la royalty al 25%.
- b) Cessare l'assistenza: Comunicandolo con 60 giorni di preavviso. In tal caso, la royalty sarà automaticamente e permanentemente ridotta al 12,5% (dodicivirgolacinque percento) a decorrere dal mese successivo alla cessazione.


**9.3. Pacchetti Extra: Il Committente potrà acquistare pacchetti di 10 ore di assistenza a € 400,00, utilizzabili entro 3 mesi dall'acquisto.


**9.4. Formazione: Lo Sviluppatore fornirà la documentazione tecnica e utente completa, nonché video tutorial per l'utilizzo del Software. Sessioni di training dal vivo (remoto o in loco) saranno fatturate a parte, secondo tariffe da concordare.


**9.5. Documentazione Minima Obbligatoria: Lo Sviluppatore si impegna a fornire:

- a) Documentazione tecnica del codice (commenti inline, README, architettura).
- b) Manuale utente con istruzioni operative.
- c) Guida all'installazione e alla configurazione.



## Art. 10 - Proprietà Intellettuale e Riservatezza
**10.1. Cessione dei Diritti: Tutti i diritti di utilizzazione economica sul Software e su ogni materiale creato in esecuzione del presente contratto sono ceduti in via esclusiva e definitiva al Committente. Il codice sorgente dell'MVP fornito dal Committente rimane di sua proprietà esclusiva.

**10.2. Obblighi di Riservatezza: Le Parti si impegnano a mantenere strettamente riservata ogni informazione tecnica, commerciale e finanziaria per tutta la durata del contratto e per i 10 (dieci) anni successivi alla sua cessazione.

**10.3. Divieto di Divulgazione: Lo Sviluppatore si impegna a non divulgare, mostrare o utilizzare il codice o il know-how del progetto per portfolio personali, consulenze, pubblicazioni o altri progetti, senza il preventivo consenso scritto del Committente.



## Art. 11 - Garanzie e Limitazione di Responsabilità
**11.1. Garanzia di Funzionamento: Lo Sviluppatore garantisce che il Software sarà esente da vizi e conforme alle specifiche per un periodo di 2 (due) mesi dalla data di accettazione finale.

**11.2. Garanzia di Sicurezza e Conformità: Lo Sviluppatore garantisce che il Software:
    a) Non conterrà codice malevolo, backdoor, telemetria non autorizzata o funzionalità nascoste.
    b) Non effettuerà alcuna trasmissione di dati all'esterno dell'ambiente locale.
    c) Sarà compatibile con Windows 10 e Windows 11 (64-bit).
    d) Rispetterà le licenze delle librerie open-source integrate.

**11.3. Clausola di Non Deterioramento: Lo Sviluppatore si impegna a non introdurre modifiche che possano rallentare, degradare o compromettere il funzionamento del Software.

**11.4. Limitazione di Responsabilità: Fatti salvi i limiti inderogabili di legge e salvo il caso di dolo o colpa grave, la responsabilità totale dello Sviluppatore per qualsiasi danno derivante dal presente contratto non potrà superare:
    a) Per danni diretti: l'importo del compenso fisso di cui all'Art. 7.1.
    b) Per danni indiretti, lucro cessante, perdita di dati o mancato guadagno: lo Sviluppatore non sarà in alcun caso responsabile.



## Art. 12 - Trattamento dei Dati Personali (GDPR)
**12.1. Ruoli GDPR: Ai fini del Regolamento (UE) 2016/679 (GDPR), il Committente agisce in qualità di Titolare del Trattamento e lo Sviluppatore in qualità di Responsabile del Trattamento, limitatamente ai dati personali eventualmente trattati nell'ambito delle attività di sviluppo e assistenza.

**12.2. Architettura Offline e Riduzione degli Obblighi: Poiché il Software opera interamente offline senza trasmissione di dati a server esterni, i rischi di violazione dei dati personali sono minimizzati. Tuttavia, lo Sviluppatore si impegna a rispettare i principi di privacy by design e privacy by default.

**12.3. Data Processing Agreement (DPA): Le Parti sottoscrivono il separato Allegato C (Data Processing Agreement), conforme all'Art. 28 del GDPR, che definisce in dettaglio gli obblighi dello Sviluppatore.

**12.4. Responsabilità in Caso di Data Breach: In caso di violazione dei dati personali imputabile allo Sviluppatore, questi si impegna a notificare il Committente entro 24 ore e a collaborare per la gestione dell'incidente.



## Art. 13 - Continuità del Servizio e Restituzione del Codice
**13.1. Obbligo di Continuità: In caso di cessazione anticipata del rapporto per qualsiasi causa (recesso, risoluzione, impossibilità sopravvenuta), lo Sviluppatore si impegna a consegnare immediatamente al Committente:
    a) Il codice sorgente completo e aggiornato.
    b) L'ambiente di build funzionante e replicabile.
    c) La documentazione tecnica completa.
    d) Ogni credenziale, accesso e materiale necessario alla prosecuzione autonoma del progetto.

**13.2. Escrow del Codice (Opzionale): Le Parti potranno concordare la costituzione di un escrow del codice sorgente presso un terzo fiduciario, da rilasciare al Committente in caso di morte, incapacità permanente o inadempimento grave dello Sviluppatore.



## Art. 14 - Divieto di Concorrenza
**14.1. Per tutta la durata del contratto e per i 12 (dodici) mesi successivi alla sua cessazione per qualsiasi causa, lo Sviluppatore si impegna a non svolgere, direttamente o indirettamente, attività in concorrenza diretta con il Software, inclusi lo sviluppo, la produzione o la commercializzazione di software di traduzione con funzionalità analoghe.

**14.2. In caso di violazione del presente divieto, lo Sviluppatore sarà tenuto a corrispondere al Committente una penale di € 15.000,00 (quindicimila/00), fatto salvo il risarcimento del maggior danno.



## Art. 15 - Durata e Recesso
**15.1. Il presente contratto ha una durata di 2 (due) anni dalla data di sottoscrizione, rinnovabili tacitamente per ulteriori periodi di 1 (uno) anno, salvo disdetta con preavviso di 90 giorni.

**15.2. Ciascuna Parte può recedere anticipatamente dal contratto per giusta causa, comunicandolo per iscritto con un preavviso di 60 giorni.

**15.3. In caso di inadempimento grave di una delle Parti, l'altra potrà risolvere il contratto di diritto ai sensi dell'art. 1456 del Codice Civile, previa diffida ad adempiere.



## Art. 16 - Legge Applicabile e Foro Competente
**16.1. Il presente contratto è regolato dalla legge italiana.

**16.2. Per qualsiasi controversia derivante dal presente contratto o ad esso collegata, è competente in via esclusiva il Foro di Milano.



## Art. 17 - Disposizioni Finali
**17.1. Il presente contratto, inclusi i suoi allegati (Allegato A - Specifiche Tecniche, Allegato B - Tempi e Milestone, Allegato C - Data Processing Agreement), costituisce l'intero accordo tra le Parti e sostituisce ogni precedente intesa, scritta o verbale.

**17.2. Qualsiasi modifica o integrazione al presente contratto dovrà essere effettuata per iscritto, a pena di nullità.

**17.3. Il presente contratto è redatto in duplice copia originale, una per ciascuna Parte.



---

**Letto, approvato e sottoscritto.**

**Luogo, ________________

**Data:** ________________

**Per LUCERTAE SRLS**  
(Legale Rappresentante)



**Per Enrico Pascatti**  
(Lo Sviluppatore)





## APPROVAZIONE SPECIFICA DELLE CLAUSOLE VESSATORIE
Ai sensi e per gli effetti degli artt. 1341 e 1342 del Codice Civile, le Parti dichiarano di approvare specificamente le seguenti clausole: Art. 3 (Conformità delle Licenze Open-Source), Art. 4 (Presenza Personale e Divieto di Subappalto), Art. 5 (Milestone, Consegna e Accettazione), Art. 8 (Regime delle Royalties e Opzione di Buyout), Art. 9 (Assistenza, Manutenzione e Formazione), Art. 11 (Garanzie e Limitazione di Responsabilità), Art. 13 (Continuità del Servizio e Restituzione del Codice), Art. 14 (Divieto di Concorrenza), Art. 15 (Durata e Recesso), Art. 16 (Legge Applicabile e Foro Competente).


**Per LUCERTAE SRLS**  
(Legale Rappresentante)



**Per Enrico Pascatti**  
(Lo Sviluppatore)

