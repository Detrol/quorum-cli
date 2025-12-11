/**
 * Swedish translations.
 */
import type { Translations } from "../types.js";

export const sv: Translations = {
  // Existing keys
  thinkingComplete: "{model} har tänkt klart",
  thinkingInProgress: "{model} tänker...",
  phaseComplete: "Fas {phase} klar",

  // App-level
  "app.title": "Quorum",
  "app.subtitle": "Multi-agent diskussionssystem",
  "app.loading.backend": "Startar backend...",
  "app.loading.models": "Laddar modeller...",
  "app.loading.validating": "Validerar modeller ({current}/{total})...",
  "app.error.generic": "Fel: {error}",
  "app.error.selectModels": "Välj minst 2 modeller först (/models)",
  "app.error.oxfordEven": "Oxford kräver ett jämnt antal modeller",
  "app.error.methodMin": "{method} kräver minst {min} modeller",
  "app.error.exportFormat": "Format: md, text, pdf",
  "app.success.exported": "Exporterat till {path}",
  "app.placeholder.selectModels": "Skriv /models för att välja modeller...",
  "app.placeholder.askQuestion": "Ställ en fråga...",
  "app.statusBar.commands": "/ kommandon • Tab rådgivare • Ctrl+R starta om • Ctrl+C avsluta",
  "app.statusBar.running": "ESC/Ctrl+R starta om • Ctrl+C avsluta",
  "app.hint.welcome": "Skriv /models för att välja AI-modeller, eller /help för kommandon",

  // Commands
  "cmd.models": "Välj AI-modeller",
  "cmd.method": "Välj diskussionsmetod",
  "cmd.synthesizer": "Välj syntetiseringsläge",
  "cmd.status": "Visa nuvarande inställningar",
  "cmd.export": "Exportera [md|text|pdf]",
  "cmd.clear": "Rensa skärmen",
  "cmd.help": "Visa hjälp",
  "cmd.quit": "Avsluta Quorum",
  "cmd.turns": "Sätt max omgångar [nummer]",

  // Model Selector
  "selector.model.title": "Välj modeller",
  "selector.model.instructions": "(Mellanslag för att växla, Enter för att bekräfta)",
  "selector.model.selected": "Valda: ",
  "selector.model.minimum": "(minst 2 krävs)",
  "selector.model.warning": "Välj minst 2 modeller för diskussion",
  "selector.model.none": "Ingen vald",
  "selector.model.navigation": "↑↓ Navigera • Mellanslag Växla • Enter Bekräfta • Esc Avbryt",
  "selector.model.noModels": "Inga modeller tillgängliga",
  "selector.model.checkApi": "Kontrollera dina API-nycklar i .env",

  // Method Selector
  "selector.method.title": "Välj metod",
  "selector.method.modelsSelected": "{count} modell{plural} vald{plural}",
  "selector.method.navigation": "↑↓ Navigera • Enter Välj • Esc Stäng",
  "selector.method.needsMin": "Kräver {min}+ modeller",
  "selector.method.needsEven": "Kräver jämnt antal",

  // Synthesizer Selector
  "selector.synthesizer.title": "Välj syntetiserare",
  "selector.synthesizer.navigation": "↑↓ Navigera • Enter Välj • Esc Stäng",

  // Method Names and Descriptions
  "method.standard.name": "Standard",
  "method.standard.desc": "Balanserad konsensussökande diskussion",
  "method.standard.useCase": "Allmänna frågor, problemlösning",
  "method.standard.requirement": "2+ modeller",
  "method.oxford.name": "Oxford",
  "method.oxford.desc": "Formell debatt med FÖR/EMOT-lag",
  "method.oxford.useCase": "Binära beslut, för/emot-analys",
  "method.oxford.requirement": "Jämnt antal (2, 4, 6...)",
  "method.advocate.name": "Advokat",
  "method.advocate.desc": "En modell utmanar konsensus",
  "method.advocate.useCase": "Stresstesta idéer, undvika grupptänk",
  "method.advocate.requirement": "3+ modeller",
  "method.socratic.name": "Sokratisk",
  "method.socratic.desc": "Frågedriven dialog med roterande frågeställare",
  "method.socratic.useCase": "Djup utforskning, avslöja antaganden",
  "method.socratic.requirement": "2+ modeller",
  "method.delphi.name": "Delphi",
  "method.delphi.desc": "Iterativa anonyma uppskattningar mot konvergens",
  "method.delphi.useCase": "Prognoser, uppskattningar, förutsägelser",
  "method.delphi.requirement": "3+ modeller",
  "method.brainstorm.name": "Brainstorm",
  "method.brainstorm.desc": "Divergent→konvergent kreativ idégenerering (Osborn)",
  "method.brainstorm.useCase": "Generera idéer, kreativa lösningar",
  "method.brainstorm.requirement": "2+ modeller",
  "method.tradeoff.name": "Avvägning",
  "method.tradeoff.desc": "Strukturerad multikriterieanalys",
  "method.tradeoff.useCase": "Jämföra alternativ, komplexa beslut",
  "method.tradeoff.requirement": "2+ modeller",

  // Phase label
  "phase.label": "Fas",

  // Phase Names - Standard
  "phase.standard.1": "Oberoende svar",
  "phase.standard.2": "Strukturerad kritik",
  "phase.standard.3": "Diskussion",
  "phase.standard.4": "Slutpositioner",
  "phase.standard.5": "Syntes",

  // Phase Names - Oxford
  "phase.oxford.1": "Inledningsanföranden",
  "phase.oxford.2": "Repliker",
  "phase.oxford.3": "Slutanföranden",
  "phase.oxford.4": "Bedömning",

  // Phase Names - Advocate
  "phase.advocate.1": "Ursprungliga positioner",
  "phase.advocate.2": "Korsförhör",
  "phase.advocate.3": "Utlåtande",

  // Phase Names - Socratic
  "phase.socratic.1": "Inledande tes",
  "phase.socratic.2": "Sokratiskt utfrågning",
  "phase.socratic.3": "Apori",

  // Phase Names - Delphi
  "phase.delphi.1": "Omgång 1: Oberoende uppskattningar",
  "phase.delphi.2": "Omgång 2: Informerad revidering",
  "phase.delphi.3": "Omgång 3: Slutlig revidering",
  "phase.delphi.4": "Sammanställning",

  // Phase Names - Brainstorm
  "phase.brainstorm.1": "Divergera: Vilda idéer",
  "phase.brainstorm.2": "Bygga: Kombinera & Utvidga",
  "phase.brainstorm.3": "Konvergera: Välj & Förfina",
  "phase.brainstorm.4": "Idésyntes",

  // Phase Names - Tradeoff
  "phase.tradeoff.1": "Ram: Definiera alternativ",
  "phase.tradeoff.2": "Kriterier: Utvärderingsdimensioner",
  "phase.tradeoff.3": "Utvärdera: Poängsätt alternativ",
  "phase.tradeoff.4": "Beslut",

  // Phase Messages (backend → frontend)
  "phase.standard.1.msg": "{count} deltagare kommer att svara oberoende...",
  "phase.standard.2.msg": "Alla deltagare kritiserar nu alla svar...",
  "phase.standard.3.msg": "Diskussion börjar, informerad av alla kritiker...",
  "phase.standard.4.msg": "Alla deltagare anger nu sin slutliga position...",
  "phase.standard.5.msg": "Syntetiserar slutliga positioner...",
  "phase.oxford.1.msg": "Inledningsanföranden börjar. Varje sida presenterar sitt fall.",
  "phase.oxford.2.msg": "Repliker börjar. Svara på motpartens argument.",
  "phase.oxford.3.msg": "Slutanföranden. De ursprungliga talarna sammanfattar sina fall.",
  "phase.oxford.4.msg": "Domaren kommer nu att utvärdera debatten.",
  "phase.advocate.1.msg": "Försvarare anger sina ursprungliga positioner för granskning.",
  "phase.advocate.2.msg": "Advocatus Diaboli kommer att korsförhöra varje försvarare.",
  "phase.advocate.3.msg": "Advocatus Diaboli avger sitt utlåtande.",
  "phase.socratic.1.msg": "En respondent presenterar sin ursprungliga tes om frågan.",
  "phase.socratic.2.msg": "Den sokratiska utfrågningen börjar. Frågeställare söker efter motsägelser.",
  "phase.socratic.3.msg": "Aporia: Tespresentatören reflekterar över vad granskningen avslöjade.",
  "phase.delphi.1.msg": "Omgång 1: Alla paneldeltagare ger oberoende uppskattningar anonymt.",
  "phase.delphi.2.msg": "Omgång 2: Granska anonyma gruppuppskattningar och revidera vid behov.",
  "phase.delphi.3.msg": "Omgång 3: Sista möjligheten att revidera före sammanställning.",
  "phase.delphi.4.msg": "Sammanställer slutliga uppskattningar till gruppkonsensus.",
  "phase.brainstorm.1.msg": "Divergera: Generera vilda idéer. INGEN BEDÖMNING - kvantitet över kvalitet!",
  "phase.brainstorm.2.msg": "Bygga: Kombinera och utveckla varandras idéer.",
  "phase.brainstorm.3.msg": "Konvergera: Nu får ni utvärdera. Välj topp 3 idéer.",
  "phase.brainstorm.4.msg": "Syntetiserar slutligt utvalda idéer.",
  "phase.tradeoff.1.msg": "Ram: Definiera alternativen att jämföra.",
  "phase.tradeoff.2.msg": "Kriterier: Fastställ utvärderingsdimensioner.",
  "phase.tradeoff.3.msg": "Utvärdera: Poängsätt varje alternativ på varje kriterium (1-10).",
  "phase.tradeoff.4.msg": "Syntetiserar rekommendation med avvägningsanalys.",

  // Roles
  "role.for": "FÖR",
  "role.against": "EMOT",
  "role.advocate": "ADVOKAT",
  "role.defender": "FÖRSVARARE",
  "role.questioner": "FRÅGESTÄLLARE",
  "role.respondent": "RESPONDENT",
  "role.panelist": "PANELDELTAGARE",
  "role.ideator": "IDÉSKAPARE",
  "role.evaluator": "UTVÄRDERARE",

  // Rounds
  "round.opening": "Inledningsanföranden",
  "round.rebuttal": "Repliker",
  "round.closing": "Slutanföranden",

  // Messages
  "msg.independentAnswer": "(Oberoende svar)",
  "msg.critique": "(Kritik)",
  "msg.finalPosition": "(Slutposition)",
  "msg.agreements": "Överenskommelser:",
  "msg.disagreements": "Meningsskiljaktigheter:",
  "msg.missing": "Saknas:",
  "msg.synthesis": "Syntes",
  "msg.verdict": "Utlåtande",
  "msg.consensus": "Konsensus",
  "msg.participants": "Deltagare",
  "msg.question": "F: {question}",
  "msg.startingDiscussion": "Startar diskussion...",
  "msg.phaseInProgress": "Fas {phase}: {name} pågår...",
  "msg.pausePrompt": "{previousPhase} klar. Tryck Enter för att fortsätta till {nextPhase}...",
  "msg.discussionComplete": "Diskussion klar",
  "msg.pressEscNewDiscussion": "Tryck ESC för att starta en ny diskussion",

  // Confidence
  "msg.confidence.high": "HÖG",
  "msg.confidence.medium": "MEDEL",
  "msg.confidence.low": "LÅG",
  "msg.confidence.breakdown": "Konfidensfördelning: ",
  "msg.confidence.panelist": "Paneldeltagarens konfidens: ",

  // Consensus values (for export)
  "consensus.yes": "JA",
  "consensus.no": "NEJ",
  "consensus.partial": "DELVIS",

  // Synthesis labels by method
  "synthesis.aporia": "Apori uppnådd",
  "synthesis.decision": "Beslut",
  "synthesis.convergence": "Konvergens",
  "synthesis.selectedIdeas": "Utvalda idéer",
  "synthesis.agreement": "Överenskommelse",
  "synthesis.consensus": "Konsensus",
  "synthesis.openQuestions": "Öppna frågor",
  "synthesis.unresolvedQuestions": "Olösta frågor",
  "synthesis.keyContentions": "Viktiga tvistepunkter",
  "synthesis.outlierPerspectives": "Avvikande perspektiv",
  "synthesis.alternativeDirections": "Alternativa riktningar",
  "synthesis.keyTradeoffs": "Viktiga avvägningar",
  "synthesis.notableDifferences": "Anmärkningsvärda skillnader",
  "synthesis.reflection": "Reflektion",
  "synthesis.ruling": "Avgörande",
  "synthesis.adjudication": "Domslut",
  "synthesis.aggregatedEstimate": "Sammanställd uppskattning",
  "synthesis.finalIdeas": "Slutliga idéer",
  "synthesis.recommendation": "Rekommendation",
  "synthesis.synthesisLabel": "Syntes",
  "synthesis.reflected": "reflekterade",
  "synthesis.adjudicated": "avgjorde",
  "synthesis.synthesized": "syntetiserade",
  "synthesis.ruledBy": "(avgjort av {model})",

  // Synthesizer Modes
  "synth.first.name": "Första",
  "synth.first.desc": "Första valda modellen syntetiserar",
  "synth.random.name": "Slumpmässig",
  "synth.random.desc": "Slumpmässig modell varje gång",
  "synth.rotate.name": "Rotera",
  "synth.rotate.desc": "Rotera mellan modeller",

  // Help
  "help.title": "Quorum-hjälp",
  "help.commands": "Kommandon:",
  "help.keyboard": "Tangentbord:",
  "help.key.esc": "Stäng överlägg / Tillbaka till inmatning",
  "help.key.ctrlC": "Avbryt pågående diskussion",
  "help.key.arrows": "Navigera i väljare",
  "help.key.enter": "Skicka / Välj",
  "help.close": "Tryck Esc för att stänga",

  // Team Preview
  "team.title": "Laguppställning",
  "team.selectRole": "Välj {role}",
  "team.chooseAdvocate": "Välj vilken modell som ska utmana de andra:",
  "team.chooseRespondent": "Välj vilken modell som ska presentera tesen:",
  "team.start": "[Enter] Starta",
  "team.swap": "[S] Byt lag",
  "team.navigation": "↑↓ Navigera • Enter Välj/Starta • Esc Avbryt",
  "team.navigationOxford": "← → Byt • Enter Välj • S Byt lag • Esc Avbryt",
  "team.forTeam": "FÖR",
  "team.againstTeam": "EMOT",
  "team.defenders": "FÖRSVARARE",

  // Export
  "export.title": "Exportera diskussion ({format})",
  "export.loading": "Laddar diskussioner...",
  "export.noDiscussions": "Inga diskussioner hittades",
  "export.noDiscussionsDir": "Inga diskussionsrapporter hittades i {dir}",
  "export.selectPrompt": "Välj en diskussion att exportera:",
  "export.navigation": "↑↓ Navigera  Enter Exportera  Esc Avbryt",
  "export.close": "Tryck ESC för att stänga",

  // Export Document (PDF/Markdown)
  "export.doc.title": "Quorum Diskussionsexport",
  "export.doc.dateLabel": "Datum:",
  "export.doc.methodLabel": "Metod:",
  "export.doc.modelsLabel": "Modeller:",
  "export.doc.questionHeader": "Fråga",
  "export.doc.discussionHeader": "Diskussion",
  "export.doc.phaseLabel": "Fas",
  "export.doc.critiqueLabel": "Kritik",
  "export.doc.finalPositionLabel": "Slutposition",
  "export.doc.agreementsLabel": "Överenskommelser:",
  "export.doc.disagreementsLabel": "Meningsskiljaktigheter:",
  "export.doc.missingLabel": "Saknas:",
  "export.doc.confidenceLabel": "Konfidens:",
  "export.doc.footer": "Exporterad från [Quorum](https://github.com/Detrol/quorum-cli)",

  // Method Terminology - Result Labels
  "terminology.result.standard": "Resultat",
  "terminology.result.oxford": "Dom",
  "terminology.result.advocate": "Utslag",
  "terminology.result.socratic": "Apori",
  "terminology.result.delphi": "Aggregering",
  "terminology.result.brainstorm": "Valda idéer",
  "terminology.result.tradeoff": "Beslut",

  // Method Terminology - Synthesis Labels
  "terminology.synthesis.standard": "Syntes",
  "terminology.synthesis.oxford": "Avgörande",
  "terminology.synthesis.advocate": "Beslut",
  "terminology.synthesis.socratic": "Reflektion",
  "terminology.synthesis.delphi": "Aggregerad uppskattning",
  "terminology.synthesis.brainstorm": "Slutgiltiga idéer",
  "terminology.synthesis.tradeoff": "Rekommendation",

  // Method Terminology - Differences Labels
  "terminology.differences.standard": "Anmärkningsvärda skillnader",
  "terminology.differences.oxford": "Huvudsakliga stridsfrågor",
  "terminology.differences.advocate": "Olösta frågor",
  "terminology.differences.socratic": "Öppna frågor",
  "terminology.differences.delphi": "Avvikande perspektiv",
  "terminology.differences.brainstorm": "Alternativa riktningar",
  "terminology.differences.tradeoff": "Huvudsakliga avvägningar",

  // Method Terminology - By Labels
  "terminology.by.standard": "Syntetiserad av",
  "terminology.by.oxford": "Avgjord av",
  "terminology.by.advocate": "Beslutad av",
  "terminology.by.socratic": "Reflekterad av",
  "terminology.by.delphi": "Aggregerad av",
  "terminology.by.brainstorm": "Sammanställd av",
  "terminology.by.tradeoff": "Analyserad av",

  // Method Terminology - Consensus Labels
  "terminology.consensus.standard": "Konsensus",
  "terminology.consensus.oxford": "Beslut",
  "terminology.consensus.advocate": "Utslag",
  "terminology.consensus.socratic": "Apori nådd",
  "terminology.consensus.delphi": "Konvergens",
  "terminology.consensus.brainstorm": "Idéer valda",
  "terminology.consensus.tradeoff": "Överenskommelse",

  // Method Advisor
  "advisor.title": "METODRÅDGIVARE",
  "advisor.prompt": "Vad är din fråga?",
  "advisor.analyzing": "Analyserar med {model}...",
  "advisor.recommended": "REKOMMENDERAD:",
  "advisor.navigation": "↑↓ Navigera • Enter Välj • Backsteg Tillbaka • Esc Avbryt",
  "advisor.analyzedBy": "Analyserad av {model}",
  "advisor.error": "Analysen misslyckades",
  "advisor.inputHint": "Enter för att analysera • Esc för att avbryta",

  // Status
  "status.title": "Nuvarande inställningar",
  "status.models": "Modeller: ",
  "status.method": "Metod: ",
  "status.synthesizer": "Syntetiserare: ",
  "status.maxTurns": "Max omgångar: ",
  "status.default": "standard",
  "status.none": "Ingen vald",

  // Header
  "header.quickCommands": "Snabbkommandon",
  "header.cmdModels": "/models - Välj AI-modeller",
  "header.cmdMethod": "/method - Ändra diskussionsstil",
  "header.cmdExport": "/export - Exportera [md|text|pdf]",
  "header.cmdHelp": "/help - Alla kommandon",

  // Command Palette
  "palette.title": "Kommandon",
  "palette.hint": "(↑↓ navigera, Enter kör, Tab fyll i, Esc stäng)",
  "palette.noMatches": "Inga matchande kommandon",

  // Discussion method titles
  "discussion.standard": "STANDARDDISKUSSION",
  "discussion.oxford": "OXFORD-DEBATT",
  "discussion.advocate": "DJÄVULENS ADVOKAT",
  "discussion.socratic": "SOKRATISK DIALOG",
  "discussion.delphi": "DELPHI-KONSENSUS",
  "discussion.brainstorm": "BRAINSTORM-SESSION",
  "discussion.tradeoff": "AVVÄGNINGSANALYS",
};
