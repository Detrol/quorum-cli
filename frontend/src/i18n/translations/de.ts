/**
 * German translations.
 */
import type { Translations } from "../types.js";

export const de: Translations = {
  // Existing keys
  thinkingComplete: "{model} hat fertig gedacht",
  thinkingInProgress: "{model} denkt nach...",
  phaseComplete: "Phase {phase} abgeschlossen",

  // App-level
  "app.title": "Quorum",
  "app.subtitle": "Multi-Agenten Diskussionssystem",
  "app.loading.backend": "Backend wird gestartet...",
  "app.loading.models": "Modelle werden geladen...",
  "app.loading.validating": "Modelle werden validiert ({current}/{total})...",
  "app.error.generic": "Fehler: {error}",
  "app.error.selectModels": "Wählen Sie zuerst mindestens 2 Modelle (/models)",
  "app.error.oxfordEven": "Oxford erfordert eine gerade Anzahl von Modellen",
  "app.error.methodMin": "{method} erfordert mindestens {min} Modelle",
  "app.error.exportFormat": "Format: md, text, pdf",
  "app.success.exported": "Exportiert nach {path}",
  "app.placeholder.selectModels": "Geben Sie /models ein, um Modelle auszuwählen...",
  "app.placeholder.askQuestion": "Stellen Sie eine Frage...",
  "app.statusBar.commands": "/ Befehle • Tab Berater • Strg+R Neustart • Strg+C Beenden",
  "app.statusBar.running": "ESC/Strg+R Neustart • Strg+C Beenden",
  "app.hint.welcome": "Geben Sie /models ein, um KI-Modelle auszuwählen, oder /help für Befehle",

  // Commands
  "cmd.models": "KI-Modelle auswählen",
  "cmd.method": "Diskussionsmethode auswählen",
  "cmd.synthesizer": "Synthesemodus auswählen",
  "cmd.status": "Aktuelle Einstellungen anzeigen",
  "cmd.export": "Exportieren [md|text|pdf]",
  "cmd.clear": "Bildschirm löschen",
  "cmd.help": "Hilfe anzeigen",
  "cmd.quit": "Quorum beenden",
  "cmd.turns": "Max. Runden festlegen [Zahl]",

  // Model Selector
  "selector.model.title": "Modelle auswählen",
  "selector.model.instructions": "(Leertaste zum Umschalten, Enter zum Bestätigen)",
  "selector.model.selected": "Ausgewählt: ",
  "selector.model.minimum": "(mindestens 2 erforderlich)",
  "selector.model.warning": "Wählen Sie mindestens 2 Modelle für die Diskussion",
  "selector.model.none": "Keine ausgewählt",
  "selector.model.navigation": "↑↓ Navigieren • Leertaste Umschalten • Enter Bestätigen • Esc Abbrechen",
  "selector.model.noModels": "Keine Modelle verfügbar",
  "selector.model.checkApi": "Überprüfen Sie Ihre API-Schlüssel in .env",

  // Method Selector
  "selector.method.title": "Methode auswählen",
  "selector.method.modelsSelected": "{count} Modell{plural} ausgewählt",
  "selector.method.navigation": "↑↓ Navigieren • Enter Auswählen • Esc Schließen",
  "selector.method.needsMin": "Benötigt {min}+ Modelle",
  "selector.method.needsEven": "Benötigt gerade Anzahl",

  // Synthesizer Selector
  "selector.synthesizer.title": "Synthesizer auswählen",
  "selector.synthesizer.navigation": "↑↓ Navigieren • Enter Auswählen • Esc Schließen",

  // Method Names and Descriptions
  "method.standard.name": "Standard",
  "method.standard.desc": "Ausgewogene konsensorientierte Diskussion",
  "method.standard.useCase": "Allgemeine Fragen, Problemlösung",
  "method.standard.requirement": "2+ Modelle",
  "method.oxford.name": "Oxford",
  "method.oxford.desc": "Formelle Debatte mit DAFÜR/DAGEGEN-Teams",
  "method.oxford.useCase": "Binäre Entscheidungen, Pro/Contra-Analyse",
  "method.oxford.requirement": "Gerade Anzahl (2, 4, 6...)",
  "method.advocate.name": "Advokat",
  "method.advocate.desc": "Ein Modell hinterfragt den Konsens",
  "method.advocate.useCase": "Ideen testen, Gruppendenken vermeiden",
  "method.advocate.requirement": "3+ Modelle",
  "method.socratic.name": "Sokratisch",
  "method.socratic.desc": "Fragengesteuerter Dialog mit rotierendem Fragesteller",
  "method.socratic.useCase": "Tiefe Erkundung, Annahmen aufdecken",
  "method.socratic.requirement": "2+ Modelle",
  "method.delphi.name": "Delphi",
  "method.delphi.desc": "Iterative anonyme Schätzungen zur Konvergenz",
  "method.delphi.useCase": "Prognosen, Schätzungen, Vorhersagen",
  "method.delphi.requirement": "3+ Modelle",
  "method.brainstorm.name": "Brainstorm",
  "method.brainstorm.desc": "Divergent→konvergente kreative Ideenfindung (Osborn)",
  "method.brainstorm.useCase": "Ideen generieren, kreative Lösungen",
  "method.brainstorm.requirement": "2+ Modelle",
  "method.tradeoff.name": "Abwägung",
  "method.tradeoff.desc": "Strukturierte Multikriterienanalyse",
  "method.tradeoff.useCase": "Optionen vergleichen, komplexe Entscheidungen",
  "method.tradeoff.requirement": "2+ Modelle",

  // Phase label
  "phase.label": "Phase",

  // Phase Names - Standard
  "phase.standard.1": "Unabhängige Antworten",
  "phase.standard.2": "Strukturierte Kritik",
  "phase.standard.3": "Diskussion",
  "phase.standard.4": "Endpositionen",
  "phase.standard.5": "Synthese",

  // Phase Names - Oxford
  "phase.oxford.1": "Eröffnungsreden",
  "phase.oxford.2": "Erwiderungen",
  "phase.oxford.3": "Schlussplädoyers",
  "phase.oxford.4": "Urteil",

  // Phase Names - Advocate
  "phase.advocate.1": "Ausgangspositionen",
  "phase.advocate.2": "Kreuzverhör",
  "phase.advocate.3": "Urteil",

  // Phase Names - Socratic
  "phase.socratic.1": "Ausgangsthese",
  "phase.socratic.2": "Sokratische Befragung",
  "phase.socratic.3": "Aporie",

  // Phase Names - Delphi
  "phase.delphi.1": "Runde 1: Unabhängige Schätzungen",
  "phase.delphi.2": "Runde 2: Informierte Überarbeitung",
  "phase.delphi.3": "Runde 3: Endgültige Überarbeitung",
  "phase.delphi.4": "Zusammenfassung",

  // Phase Names - Brainstorm
  "phase.brainstorm.1": "Divergieren: Wilde Ideen",
  "phase.brainstorm.2": "Aufbauen: Kombinieren & Erweitern",
  "phase.brainstorm.3": "Konvergieren: Auswählen & Verfeinern",
  "phase.brainstorm.4": "Ideensynthese",

  // Phase Names - Tradeoff
  "phase.tradeoff.1": "Rahmen: Alternativen definieren",
  "phase.tradeoff.2": "Kriterien: Bewertungsdimensionen",
  "phase.tradeoff.3": "Bewerten: Optionen punkten",
  "phase.tradeoff.4": "Entscheidung",

  // Phase Messages (backend → frontend)
  "phase.standard.1.msg": "{count} Teilnehmer werden unabhängig antworten...",
  "phase.standard.2.msg": "Alle Teilnehmer kritisieren nun alle Antworten...",
  "phase.standard.3.msg": "Diskussion beginnt, informiert durch alle Kritiken...",
  "phase.standard.4.msg": "Alle Teilnehmer geben nun ihre Endposition an...",
  "phase.standard.5.msg": "Synthese der Endpositionen...",
  "phase.oxford.1.msg": "Eröffnungsreden beginnen. Jede Seite präsentiert ihren Fall.",
  "phase.oxford.2.msg": "Erwiderungen beginnen. Antworten Sie auf die Argumente der Gegenseite.",
  "phase.oxford.3.msg": "Schlussplädoyers. Die ursprünglichen Redner fassen ihre Fälle zusammen.",
  "phase.oxford.4.msg": "Der Richter wird nun die Debatte bewerten.",
  "phase.advocate.1.msg": "Verteidiger geben ihre Ausgangspositionen zur Prüfung an.",
  "phase.advocate.2.msg": "Der Advocatus Diaboli wird jeden Verteidiger ins Kreuzverhör nehmen.",
  "phase.advocate.3.msg": "Der Advocatus Diaboli verkündet das Urteil.",
  "phase.socratic.1.msg": "Ein Befragter präsentiert seine These zur Frage.",
  "phase.socratic.2.msg": "Die sokratische Befragung beginnt. Fragesteller suchen nach Widersprüchen.",
  "phase.socratic.3.msg": "Aporie: Der Thesenpräsentator reflektiert über die Erkenntnisse.",
  "phase.delphi.1.msg": "Runde 1: Alle Panelmitglieder geben anonyme unabhängige Schätzungen ab.",
  "phase.delphi.2.msg": "Runde 2: Anonyme Gruppenschätzungen prüfen und bei Bedarf revidieren.",
  "phase.delphi.3.msg": "Runde 3: Letzte Revisionsmöglichkeit vor der Zusammenfassung.",
  "phase.delphi.4.msg": "Zusammenfassung der Endschätzungen zum Gruppenkonsens.",
  "phase.brainstorm.1.msg": "Divergieren: Wilde Ideen generieren. KEINE BEWERTUNG - Quantität vor Qualität!",
  "phase.brainstorm.2.msg": "Aufbauen: Ideen kombinieren und erweitern.",
  "phase.brainstorm.3.msg": "Konvergieren: Jetzt dürfen Sie bewerten. Top 3 Ideen wählen.",
  "phase.brainstorm.4.msg": "Synthese der ausgewählten Ideen.",
  "phase.tradeoff.1.msg": "Rahmen: Zu vergleichende Alternativen definieren.",
  "phase.tradeoff.2.msg": "Kriterien: Bewertungsdimensionen festlegen.",
  "phase.tradeoff.3.msg": "Bewerten: Jede Alternative auf jedem Kriterium punkten (1-10).",
  "phase.tradeoff.4.msg": "Synthese der Empfehlung mit Abwägungsanalyse.",

  // Roles
  "role.for": "DAFÜR",
  "role.against": "DAGEGEN",
  "role.advocate": "ADVOKAT",
  "role.defender": "VERTEIDIGER",
  "role.questioner": "FRAGESTELLER",
  "role.respondent": "BEFRAGTER",
  "role.panelist": "PANELMITGLIED",
  "role.ideator": "IDEENGEBER",
  "role.evaluator": "BEWERTER",

  // Rounds
  "round.opening": "Eröffnungsreden",
  "round.rebuttal": "Erwiderungen",
  "round.closing": "Schlussplädoyers",

  // Messages
  "msg.independentAnswer": "(Unabhängige Antwort)",
  "msg.critique": "(Kritik)",
  "msg.finalPosition": "(Endposition)",
  "msg.agreements": "Übereinstimmungen:",
  "msg.disagreements": "Meinungsverschiedenheiten:",
  "msg.missing": "Fehlend:",
  "msg.synthesis": "Synthese",
  "msg.verdict": "Urteil",
  "msg.consensus": "Konsens",
  "msg.participants": "Teilnehmer",
  "msg.question": "F: {question}",
  "msg.startingDiscussion": "Diskussion wird gestartet...",
  "msg.phaseInProgress": "Phase {phase}: {name} läuft...",
  "msg.pausePrompt": "{previousPhase} abgeschlossen. Drücken Sie Enter, um mit {nextPhase} fortzufahren...",
  "msg.discussionComplete": "Diskussion abgeschlossen",
  "msg.pressEscNewDiscussion": "Drücken Sie ESC, um eine neue Diskussion zu starten",

  // Confidence
  "msg.confidence.high": "HOCH",
  "msg.confidence.medium": "MITTEL",
  "msg.confidence.low": "NIEDRIG",
  "msg.confidence.breakdown": "Konfidenzverteilung: ",
  "msg.confidence.panelist": "Panelmitglied-Konfidenz: ",

  // Consensus values (for export)
  "consensus.yes": "JA",
  "consensus.no": "NEIN",
  "consensus.partial": "TEILWEISE",

  // Synthesis labels by method
  "synthesis.aporia": "Aporie erreicht",
  "synthesis.decision": "Entscheidung",
  "synthesis.convergence": "Konvergenz",
  "synthesis.selectedIdeas": "Ausgewählte Ideen",
  "synthesis.agreement": "Übereinstimmung",
  "synthesis.consensus": "Konsens",
  "synthesis.openQuestions": "Offene Fragen",
  "synthesis.unresolvedQuestions": "Ungelöste Fragen",
  "synthesis.keyContentions": "Wichtige Streitpunkte",
  "synthesis.outlierPerspectives": "Abweichende Perspektiven",
  "synthesis.alternativeDirections": "Alternative Richtungen",
  "synthesis.keyTradeoffs": "Wichtige Abwägungen",
  "synthesis.notableDifferences": "Bemerkenswerte Unterschiede",
  "synthesis.reflection": "Reflexion",
  "synthesis.ruling": "Entscheidung",
  "synthesis.adjudication": "Urteilsspruch",
  "synthesis.aggregatedEstimate": "Zusammengefasste Schätzung",
  "synthesis.finalIdeas": "Endgültige Ideen",
  "synthesis.recommendation": "Empfehlung",
  "synthesis.synthesisLabel": "Synthese",
  "synthesis.reflected": "reflektierte",
  "synthesis.adjudicated": "entschied",
  "synthesis.synthesized": "synthetisierte",
  "synthesis.ruledBy": "(entschieden von {model})",

  // Synthesizer Modes
  "synth.first.name": "Erstes",
  "synth.first.desc": "Erstes ausgewähltes Modell synthetisiert",
  "synth.random.name": "Zufällig",
  "synth.random.desc": "Zufälliges Modell jedes Mal",
  "synth.rotate.name": "Rotierend",
  "synth.rotate.desc": "Zwischen Modellen rotieren",

  // Help
  "help.title": "Quorum-Hilfe",
  "help.commands": "Befehle:",
  "help.keyboard": "Tastatur:",
  "help.key.esc": "Overlay schließen / Zurück zur Eingabe",
  "help.key.ctrlC": "Laufende Diskussion abbrechen",
  "help.key.arrows": "In Auswahlen navigieren",
  "help.key.enter": "Absenden / Auswählen",
  "help.close": "Drücken Sie Esc zum Schließen",

  // Team Preview
  "team.title": "Teamzuweisung",
  "team.selectRole": "{role} auswählen",
  "team.chooseAdvocate": "Wählen Sie, welches Modell die anderen herausfordern soll:",
  "team.chooseRespondent": "Wählen Sie, welches Modell die These präsentieren soll:",
  "team.start": "[Enter] Start",
  "team.swap": "[S] Teams tauschen",
  "team.navigation": "↑↓ Navigieren • Enter Auswählen/Starten • Esc Abbrechen",
  "team.navigationOxford": "← → Wechseln • Enter Auswählen • S Tauschen • Esc Abbrechen",
  "team.forTeam": "DAFÜR",
  "team.againstTeam": "DAGEGEN",
  "team.defenders": "VERTEIDIGER",

  // Export
  "export.title": "Diskussion exportieren ({format})",
  "export.loading": "Diskussionen werden geladen...",
  "export.noDiscussions": "Keine Diskussionen gefunden",
  "export.noDiscussionsDir": "Keine Diskussionsberichte in {dir} gefunden",
  "export.selectPrompt": "Wählen Sie eine Diskussion zum Exportieren:",
  "export.navigation": "↑↓ Navigieren  Enter Exportieren  Esc Abbrechen",
  "export.close": "Drücken Sie ESC zum Schließen",

  // Export Document (PDF/Markdown)
  "export.doc.title": "Quorum Diskussionsexport",
  "export.doc.dateLabel": "Datum:",
  "export.doc.methodLabel": "Methode:",
  "export.doc.modelsLabel": "Modelle:",
  "export.doc.questionHeader": "Frage",
  "export.doc.discussionHeader": "Diskussion",
  "export.doc.phaseLabel": "Phase",
  "export.doc.critiqueLabel": "Kritik",
  "export.doc.finalPositionLabel": "Endposition",
  "export.doc.agreementsLabel": "Übereinstimmungen:",
  "export.doc.disagreementsLabel": "Meinungsverschiedenheiten:",
  "export.doc.missingLabel": "Fehlend:",
  "export.doc.confidenceLabel": "Konfidenz:",
  "export.doc.footer": "Exportiert von [Quorum](https://github.com/Detrol/quorum-cli)",

  // Method Terminology - Result Labels
  "terminology.result.standard": "Ergebnis",
  "terminology.result.oxford": "Urteil",
  "terminology.result.advocate": "Verdikt",
  "terminology.result.socratic": "Aporie",
  "terminology.result.delphi": "Aggregation",
  "terminology.result.brainstorm": "Ausgewählte Ideen",
  "terminology.result.tradeoff": "Entscheidung",

  // Method Terminology - Synthesis Labels
  "terminology.synthesis.standard": "Synthese",
  "terminology.synthesis.oxford": "Entscheidung",
  "terminology.synthesis.advocate": "Urteil",
  "terminology.synthesis.socratic": "Reflexion",
  "terminology.synthesis.delphi": "Aggregierte Schätzung",
  "terminology.synthesis.brainstorm": "Endgültige Ideen",
  "terminology.synthesis.tradeoff": "Empfehlung",

  // Method Terminology - Differences Labels
  "terminology.differences.standard": "Bemerkenswerte Unterschiede",
  "terminology.differences.oxford": "Hauptstreitpunkte",
  "terminology.differences.advocate": "Ungelöste Fragen",
  "terminology.differences.socratic": "Offene Fragen",
  "terminology.differences.delphi": "Abweichende Perspektiven",
  "terminology.differences.brainstorm": "Alternative Richtungen",
  "terminology.differences.tradeoff": "Wichtige Kompromisse",

  // Method Terminology - By Labels
  "terminology.by.standard": "Synthetisiert von",
  "terminology.by.oxford": "Entschieden von",
  "terminology.by.advocate": "Geurteilt von",
  "terminology.by.socratic": "Reflektiert von",
  "terminology.by.delphi": "Aggregiert von",
  "terminology.by.brainstorm": "Zusammengestellt von",
  "terminology.by.tradeoff": "Analysiert von",

  // Method Terminology - Consensus Labels
  "terminology.consensus.standard": "Konsens",
  "terminology.consensus.oxford": "Entscheidung",
  "terminology.consensus.advocate": "Verdikt",
  "terminology.consensus.socratic": "Aporie erreicht",
  "terminology.consensus.delphi": "Konvergenz",
  "terminology.consensus.brainstorm": "Ideen ausgewählt",
  "terminology.consensus.tradeoff": "Einigung",

  // Method Advisor
  "advisor.title": "METHODENBERATER",
  "advisor.prompt": "Was ist Ihre Frage?",
  "advisor.analyzing": "Analysiere mit {model}...",
  "advisor.recommended": "EMPFOHLEN:",
  "advisor.navigation": "↑↓ Navigieren • Enter Auswählen • Rücktaste Zurück • Esc Abbrechen",
  "advisor.analyzedBy": "Analysiert von {model}",
  "advisor.error": "Analyse fehlgeschlagen",
  "advisor.inputHint": "Enter zum Analysieren • Esc zum Abbrechen",

  // Status
  "status.title": "Aktuelle Einstellungen",
  "status.models": "Modelle: ",
  "status.method": "Methode: ",
  "status.synthesizer": "Synthesizer: ",
  "status.maxTurns": "Max. Runden: ",
  "status.default": "Standard",
  "status.none": "Keine ausgewählt",

  // Header
  "header.quickCommands": "Schnellbefehle",
  "header.cmdModels": "/models - KI-Modelle auswählen",
  "header.cmdMethod": "/method - Diskussionsstil ändern",
  "header.cmdExport": "/export - Exportieren [md|text|pdf]",
  "header.cmdHelp": "/help - Alle Befehle",

  // Command Palette
  "palette.title": "Befehle",
  "palette.hint": "(↑↓ navigieren, Enter ausführen, Tab ausfüllen, Esc schließen)",
  "palette.noMatches": "Keine passenden Befehle",

  // Discussion method titles
  "discussion.standard": "STANDARD-DISKUSSION",
  "discussion.oxford": "OXFORD-DEBATTE",
  "discussion.advocate": "ADVOCATUS DIABOLI",
  "discussion.socratic": "SOKRATISCHER DIALOG",
  "discussion.delphi": "DELPHI-KONSENS",
  "discussion.brainstorm": "BRAINSTORMING-SITZUNG",
  "discussion.tradeoff": "ABWÄGUNGSANALYSE",
};
