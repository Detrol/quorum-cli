/**
 * Italian translations.
 */
import type { Translations } from "../types.js";

export const it: Translations = {
  // Existing keys
  thinkingComplete: "{model} ha finito di pensare",
  thinkingInProgress: "{model} sta pensando...",
  phaseComplete: "Fase {phase} completata",

  // App-level
  "app.title": "Quorum",
  "app.subtitle": "Sistema di discussione multi-agente",
  "app.loading.backend": "Avvio del backend...",
  "app.loading.models": "Caricamento modelli...",
  "app.loading.validating": "Validazione modelli ({current}/{total})...",
  "app.error.generic": "Errore: {error}",
  "app.error.selectModels": "Seleziona prima almeno 2 modelli (/models)",
  "app.error.oxfordEven": "Oxford richiede un numero pari di modelli",
  "app.error.methodMin": "{method} richiede almeno {min} modelli",
  "app.error.exportFormat": "Formato: md, text, pdf",
  "app.success.exported": "Esportato in {path}",
  "app.placeholder.selectModels": "Digita /models per selezionare i modelli...",
  "app.placeholder.askQuestion": "Fai una domanda...",
  "app.statusBar.commands": "/ comandi • Tab consulente • Ctrl+R riavvia • Ctrl+C esci",
  "app.statusBar.running": "ESC/Ctrl+R riavvia • Ctrl+C esci",
  "app.hint.welcome": "Digita /models per selezionare i modelli IA, o /help per i comandi",

  // Commands
  "cmd.models": "Seleziona modelli IA",
  "cmd.method": "Seleziona metodo di discussione",
  "cmd.synthesizer": "Seleziona modalità di sintesi",
  "cmd.status": "Mostra impostazioni correnti",
  "cmd.export": "Esporta [md|text|pdf]",
  "cmd.clear": "Pulisci schermo",
  "cmd.help": "Mostra aiuto",
  "cmd.quit": "Esci da Quorum",
  "cmd.turns": "Imposta turni max [numero]",

  // Model Selector
  "selector.model.title": "Seleziona modelli",
  "selector.model.instructions": "(Spazio per alternare, Invio per confermare)",
  "selector.model.selected": "Selezionati: ",
  "selector.model.minimum": "(minimo 2 richiesti)",
  "selector.model.warning": "Seleziona almeno 2 modelli per la discussione",
  "selector.model.none": "Nessuno selezionato",
  "selector.model.navigation": "↑↓ Naviga • Spazio Alterna • Invio Conferma • Esc Annulla",
  "selector.model.noModels": "Nessun modello disponibile",
  "selector.model.checkApi": "Controlla le tue chiavi API in .env",

  // Method Selector
  "selector.method.title": "Seleziona metodo",
  "selector.method.modelsSelected": "{count} modell{plural} selezionat{plural}",
  "selector.method.navigation": "↑↓ Naviga • Invio Seleziona • Esc Chiudi",
  "selector.method.needsMin": "Richiede {min}+ modelli",
  "selector.method.needsEven": "Richiede numero pari",

  // Synthesizer Selector
  "selector.synthesizer.title": "Seleziona sintetizzatore",
  "selector.synthesizer.navigation": "↑↓ Naviga • Invio Seleziona • Esc Chiudi",

  // Method Names and Descriptions
  "method.standard.name": "Standard",
  "method.standard.desc": "Discussione equilibrata orientata al consenso",
  "method.standard.useCase": "Domande generali, risoluzione problemi",
  "method.standard.requirement": "2+ modelli",
  "method.oxford.name": "Oxford",
  "method.oxford.desc": "Dibattito formale con squadre A FAVORE/CONTRO",
  "method.oxford.useCase": "Decisioni binarie, analisi pro/contro",
  "method.oxford.requirement": "Numero pari (2, 4, 6...)",
  "method.advocate.name": "Avvocato",
  "method.advocate.desc": "Un modello sfida il consenso",
  "method.advocate.useCase": "Testare idee, evitare il pensiero di gruppo",
  "method.advocate.requirement": "3+ modelli",
  "method.socratic.name": "Socratico",
  "method.socratic.desc": "Dialogo guidato da domande con interrogatore a rotazione",
  "method.socratic.useCase": "Esplorazione profonda, rivelare presupposti",
  "method.socratic.requirement": "2+ modelli",
  "method.delphi.name": "Delphi",
  "method.delphi.desc": "Stime anonime iterative verso la convergenza",
  "method.delphi.useCase": "Previsioni, stime, predizioni",
  "method.delphi.requirement": "3+ modelli",
  "method.brainstorm.name": "Brainstorm",
  "method.brainstorm.desc": "Ideazione creativa divergente→convergente (Osborn)",
  "method.brainstorm.useCase": "Generare idee, soluzioni creative",
  "method.brainstorm.requirement": "2+ modelli",
  "method.tradeoff.name": "Compromesso",
  "method.tradeoff.desc": "Analisi multicriteria strutturata",
  "method.tradeoff.useCase": "Confrontare opzioni, decisioni complesse",
  "method.tradeoff.requirement": "2+ modelli",

  // Phase label
  "phase.label": "Fase",

  // Phase Names - Standard
  "phase.standard.1": "Risposte indipendenti",
  "phase.standard.2": "Critica strutturata",
  "phase.standard.3": "Discussione",
  "phase.standard.4": "Posizioni finali",
  "phase.standard.5": "Sintesi",

  // Phase Names - Oxford
  "phase.oxford.1": "Dichiarazioni di apertura",
  "phase.oxford.2": "Repliche",
  "phase.oxford.3": "Argomentazioni conclusive",
  "phase.oxford.4": "Giudizio",

  // Phase Names - Advocate
  "phase.advocate.1": "Posizioni iniziali",
  "phase.advocate.2": "Controinterrogatorio",
  "phase.advocate.3": "Verdetto",

  // Phase Names - Socratic
  "phase.socratic.1": "Tesi iniziale",
  "phase.socratic.2": "Indagine socratica",
  "phase.socratic.3": "Aporia",

  // Phase Names - Delphi
  "phase.delphi.1": "Round 1: Stime indipendenti",
  "phase.delphi.2": "Round 2: Revisione informata",
  "phase.delphi.3": "Round 3: Revisione finale",
  "phase.delphi.4": "Aggregazione",

  // Phase Names - Brainstorm
  "phase.brainstorm.1": "Divergere: Idee folli",
  "phase.brainstorm.2": "Costruire: Combinare ed espandere",
  "phase.brainstorm.3": "Convergere: Selezionare e raffinare",
  "phase.brainstorm.4": "Sintesi delle idee",

  // Phase Names - Tradeoff
  "phase.tradeoff.1": "Quadro: Definire alternative",
  "phase.tradeoff.2": "Criteri: Dimensioni di valutazione",
  "phase.tradeoff.3": "Valutare: Punteggio opzioni",
  "phase.tradeoff.4": "Decisione",

  // Phase Messages (backend → frontend)
  "phase.standard.1.msg": "{count} partecipanti risponderanno in modo indipendente...",
  "phase.standard.2.msg": "Tutti i partecipanti ora criticheranno tutte le risposte...",
  "phase.standard.3.msg": "La discussione inizia, informata da tutte le critiche...",
  "phase.standard.4.msg": "Tutti i partecipanti indicheranno ora la loro posizione finale...",
  "phase.standard.5.msg": "Sintetizzando le posizioni finali...",
  "phase.oxford.1.msg": "Iniziano le dichiarazioni di apertura. Ogni parte presenta il suo caso.",
  "phase.oxford.2.msg": "Iniziano le repliche. Rispondete agli argomenti della parte avversa.",
  "phase.oxford.3.msg": "Dichiarazioni conclusive. Gli oratori originali riassumono i loro casi.",
  "phase.oxford.4.msg": "Il giudice valuterà ora il dibattito.",
  "phase.advocate.1.msg": "I difensori espongono le loro posizioni iniziali da esaminare.",
  "phase.advocate.2.msg": "L'Advocatus Diaboli interrogherà ogni difensore.",
  "phase.advocate.3.msg": "L'Advocatus Diaboli emette il verdetto.",
  "phase.socratic.1.msg": "Un rispondente presenterà la sua tesi iniziale sulla domanda.",
  "phase.socratic.2.msg": "L'interrogatorio socratico inizia. Gli interrogatori cercano contraddizioni.",
  "phase.socratic.3.msg": "Aporia: Il presentatore della tesi riflette su ciò che l'esame ha rivelato.",
  "phase.delphi.1.msg": "Round 1: Tutti i panelisti forniscono stime indipendenti anonime.",
  "phase.delphi.2.msg": "Round 2: Rivedere le stime anonime del gruppo e rivedere se necessario.",
  "phase.delphi.3.msg": "Round 3: Ultima opportunità di revisione prima dell'aggregazione.",
  "phase.delphi.4.msg": "Aggregando le stime finali in consenso di gruppo.",
  "phase.brainstorm.1.msg": "Divergere: Generare idee folli. NESSUN GIUDIZIO - quantità sopra qualità!",
  "phase.brainstorm.2.msg": "Costruire: Combinare ed espandere le idee degli altri.",
  "phase.brainstorm.3.msg": "Convergere: Ora potete valutare. Selezionate le 3 migliori idee.",
  "phase.brainstorm.4.msg": "Sintetizzando le idee selezionate finali.",
  "phase.tradeoff.1.msg": "Quadro: Definire le alternative da confrontare.",
  "phase.tradeoff.2.msg": "Criteri: Stabilire le dimensioni di valutazione.",
  "phase.tradeoff.3.msg": "Valutare: Punteggio di ogni alternativa su ogni criterio (1-10).",
  "phase.tradeoff.4.msg": "Sintetizzando la raccomandazione con analisi dei compromessi.",

  // Roles
  "role.for": "A FAVORE",
  "role.against": "CONTRO",
  "role.advocate": "AVVOCATO",
  "role.defender": "DIFENSORE",
  "role.questioner": "INTERROGATORE",
  "role.respondent": "RISPONDENTE",
  "role.panelist": "PANELISTA",
  "role.ideator": "IDEATORE",
  "role.evaluator": "VALUTATORE",

  // Rounds
  "round.opening": "Dichiarazioni di apertura",
  "round.rebuttal": "Repliche",
  "round.closing": "Dichiarazioni conclusive",

  // Messages
  "msg.independentAnswer": "(Risposta indipendente)",
  "msg.critique": "(Critica)",
  "msg.finalPosition": "(Posizione finale)",
  "msg.agreements": "Accordi:",
  "msg.disagreements": "Disaccordi:",
  "msg.missing": "Mancante:",
  "msg.synthesis": "Sintesi",
  "msg.verdict": "Verdetto",
  "msg.consensus": "Consenso",
  "msg.participants": "Partecipanti",
  "msg.question": "D: {question}",
  "msg.startingDiscussion": "Avvio discussione...",
  "msg.phaseInProgress": "Fase {phase}: {name} in corso...",
  "msg.pausePrompt": "{previousPhase} completata. Premi Invio per continuare a {nextPhase}...",
  "msg.discussionComplete": "Discussione completata",
  "msg.pressEscNewDiscussion": "Premi ESC per avviare una nuova discussione",

  // Confidence
  "msg.confidence.high": "ALTA",
  "msg.confidence.medium": "MEDIA",
  "msg.confidence.low": "BASSA",
  "msg.confidence.breakdown": "Distribuzione fiducia: ",
  "msg.confidence.panelist": "Fiducia del panelista: ",

  // Consensus values (for export)
  "consensus.yes": "SÌ",
  "consensus.no": "NO",
  "consensus.partial": "PARZIALE",

  // Synthesis labels by method
  "synthesis.aporia": "Aporia raggiunta",
  "synthesis.decision": "Decisione",
  "synthesis.convergence": "Convergenza",
  "synthesis.selectedIdeas": "Idee selezionate",
  "synthesis.agreement": "Accordo",
  "synthesis.consensus": "Consenso",
  "synthesis.openQuestions": "Domande aperte",
  "synthesis.unresolvedQuestions": "Domande irrisolte",
  "synthesis.keyContentions": "Punti chiave di disaccordo",
  "synthesis.outlierPerspectives": "Prospettive divergenti",
  "synthesis.alternativeDirections": "Direzioni alternative",
  "synthesis.keyTradeoffs": "Compromessi chiave",
  "synthesis.notableDifferences": "Differenze notevoli",
  "synthesis.reflection": "Riflessione",
  "synthesis.ruling": "Decisione",
  "synthesis.adjudication": "Aggiudicazione",
  "synthesis.aggregatedEstimate": "Stima aggregata",
  "synthesis.finalIdeas": "Idee finali",
  "synthesis.recommendation": "Raccomandazione",
  "synthesis.synthesisLabel": "Sintesi",
  "synthesis.reflected": "ha riflettuto",
  "synthesis.adjudicated": "ha aggiudicato",
  "synthesis.synthesized": "ha sintetizzato",
  "synthesis.ruledBy": "(deciso da {model})",

  // Synthesizer Modes
  "synth.first.name": "Primo",
  "synth.first.desc": "Il primo modello selezionato sintetizza",
  "synth.random.name": "Casuale",
  "synth.random.desc": "Modello casuale ogni volta",
  "synth.rotate.name": "Rotazione",
  "synth.rotate.desc": "Ruotare tra i modelli",

  // Help
  "help.title": "Aiuto Quorum",
  "help.commands": "Comandi:",
  "help.keyboard": "Tastiera:",
  "help.key.esc": "Chiudi overlay / Torna all'input",
  "help.key.ctrlC": "Annulla discussione in corso",
  "help.key.arrows": "Naviga nei selettori",
  "help.key.enter": "Invia / Seleziona",
  "help.close": "Premi Esc per chiudere",

  // Team Preview
  "team.title": "Assegnazione squadre",
  "team.selectRole": "Seleziona {role}",
  "team.chooseAdvocate": "Scegli quale modello sfiderà gli altri:",
  "team.chooseRespondent": "Scegli quale modello presenterà la tesi:",
  "team.start": "[Invio] Avvia",
  "team.swap": "[S] Scambia squadre",
  "team.navigation": "↑↓ Naviga • Invio Seleziona/Avvia • Esc Annulla",
  "team.navigationOxford": "← → Cambia • Invio Seleziona • S Scambia • Esc Annulla",
  "team.forTeam": "A FAVORE",
  "team.againstTeam": "CONTRO",
  "team.defenders": "DIFENSORI",

  // Export
  "export.title": "Esporta discussione ({format})",
  "export.loading": "Caricamento discussioni...",
  "export.noDiscussions": "Nessuna discussione trovata",
  "export.noDiscussionsDir": "Nessun report di discussione trovato in {dir}",
  "export.selectPrompt": "Seleziona una discussione da esportare:",
  "export.navigation": "↑↓ Naviga  Invio Esporta  Esc Annulla",
  "export.close": "Premi ESC per chiudere",

  // Export Document (PDF/Markdown)
  "export.doc.title": "Esportazione Discussione Quorum",
  "export.doc.dateLabel": "Data:",
  "export.doc.methodLabel": "Metodo:",
  "export.doc.modelsLabel": "Modelli:",
  "export.doc.questionHeader": "Domanda",
  "export.doc.discussionHeader": "Discussione",
  "export.doc.phaseLabel": "Fase",
  "export.doc.critiqueLabel": "Critica",
  "export.doc.finalPositionLabel": "Posizione Finale",
  "export.doc.agreementsLabel": "Accordi:",
  "export.doc.disagreementsLabel": "Disaccordi:",
  "export.doc.missingLabel": "Mancante:",
  "export.doc.confidenceLabel": "Confidenza:",
  "export.doc.footer": "Esportato da [Quorum](https://github.com/Detrol/quorum-cli)",

  // Method Terminology - Result Labels
  "terminology.result.standard": "Risultato",
  "terminology.result.oxford": "Giudizio",
  "terminology.result.advocate": "Verdetto",
  "terminology.result.socratic": "Aporia",
  "terminology.result.delphi": "Aggregazione",
  "terminology.result.brainstorm": "Idee Selezionate",
  "terminology.result.tradeoff": "Decisione",

  // Method Terminology - Synthesis Labels
  "terminology.synthesis.standard": "Sintesi",
  "terminology.synthesis.oxford": "Giudizio",
  "terminology.synthesis.advocate": "Sentenza",
  "terminology.synthesis.socratic": "Riflessione",
  "terminology.synthesis.delphi": "Stima Aggregata",
  "terminology.synthesis.brainstorm": "Idee Finali",
  "terminology.synthesis.tradeoff": "Raccomandazione",

  // Method Terminology - Differences Labels
  "terminology.differences.standard": "Differenze Notevoli",
  "terminology.differences.oxford": "Punti di Contesa",
  "terminology.differences.advocate": "Domande Irrisolte",
  "terminology.differences.socratic": "Domande Aperte",
  "terminology.differences.delphi": "Prospettive Divergenti",
  "terminology.differences.brainstorm": "Direzioni Alternative",
  "terminology.differences.tradeoff": "Compromessi Chiave",

  // Method Terminology - By Labels
  "terminology.by.standard": "Sintetizzato da",
  "terminology.by.oxford": "Giudicato da",
  "terminology.by.advocate": "Sentenziato da",
  "terminology.by.socratic": "Riflesso da",
  "terminology.by.delphi": "Aggregato da",
  "terminology.by.brainstorm": "Compilato da",
  "terminology.by.tradeoff": "Analizzato da",

  // Method Terminology - Consensus Labels
  "terminology.consensus.standard": "Consenso",
  "terminology.consensus.oxford": "Decisione",
  "terminology.consensus.advocate": "Verdetto",
  "terminology.consensus.socratic": "Aporia Raggiunta",
  "terminology.consensus.delphi": "Convergenza",
  "terminology.consensus.brainstorm": "Idee Selezionate",
  "terminology.consensus.tradeoff": "Accordo",

  // Method Advisor
  "advisor.title": "CONSULENTE METODO",
  "advisor.prompt": "Qual è la tua domanda?",
  "advisor.analyzing": "Analisi con {model}...",
  "advisor.recommended": "RACCOMANDATO:",
  "advisor.navigation": "↑↓ Naviga • Invio Seleziona • Backspace Indietro • Esc Annulla",
  "advisor.analyzedBy": "Analizzato da {model}",
  "advisor.error": "Analisi fallita",
  "advisor.inputHint": "Invio per analizzare • Esc per annullare",

  // Status
  "status.title": "Impostazioni correnti",
  "status.models": "Modelli: ",
  "status.method": "Metodo: ",
  "status.synthesizer": "Sintetizzatore: ",
  "status.maxTurns": "Turni max.: ",
  "status.default": "predefinito",
  "status.none": "Nessuno selezionato",

  // Header
  "header.quickCommands": "Comandi rapidi",
  "header.cmdModels": "/models - Seleziona modelli IA",
  "header.cmdMethod": "/method - Cambia stile discussione",
  "header.cmdExport": "/export - Esporta [md|text|pdf]",
  "header.cmdHelp": "/help - Tutti i comandi",

  // Command Palette
  "palette.title": "Comandi",
  "palette.hint": "(↑↓ naviga, Invio esegui, Tab completa, Esc chiudi)",
  "palette.noMatches": "Nessun comando corrispondente",

  // Discussion method titles
  "discussion.standard": "DISCUSSIONE STANDARD",
  "discussion.oxford": "DIBATTITO OXFORD",
  "discussion.advocate": "AVVOCATO DEL DIAVOLO",
  "discussion.socratic": "DIALOGO SOCRATICO",
  "discussion.delphi": "CONSENSO DELPHI",
  "discussion.brainstorm": "SESSIONE BRAINSTORM",
  "discussion.tradeoff": "ANALISI DEI COMPROMESSI",
};
