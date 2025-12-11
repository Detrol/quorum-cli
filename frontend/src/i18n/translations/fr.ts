/**
 * French translations.
 */
import type { Translations } from "../types.js";

export const fr: Translations = {
  // Existing keys
  thinkingComplete: "{model} a fini de réfléchir",
  thinkingInProgress: "{model} réfléchit...",
  phaseComplete: "Phase {phase} terminée",

  // App-level
  "app.title": "Quorum",
  "app.subtitle": "Système de discussion multi-agents",
  "app.loading.backend": "Démarrage du backend...",
  "app.loading.models": "Chargement des modèles...",
  "app.loading.validating": "Validation des modèles ({current}/{total})...",
  "app.error.generic": "Erreur : {error}",
  "app.error.selectModels": "Sélectionnez d'abord au moins 2 modèles (/models)",
  "app.error.oxfordEven": "Oxford nécessite un nombre pair de modèles",
  "app.error.methodMin": "{method} nécessite au moins {min} modèles",
  "app.error.exportFormat": "Format : md, text, pdf",
  "app.success.exported": "Exporté vers {path}",
  "app.placeholder.selectModels": "Tapez /models pour sélectionner des modèles...",
  "app.placeholder.askQuestion": "Posez une question...",
  "app.statusBar.commands": "/ commandes • Tab conseiller • Ctrl+R redémarrer • Ctrl+C quitter",
  "app.statusBar.running": "ESC/Ctrl+R redémarrer • Ctrl+C quitter",
  "app.hint.welcome": "Tapez /models pour sélectionner des modèles IA, ou /help pour les commandes",

  // Commands
  "cmd.models": "Sélectionner les modèles IA",
  "cmd.method": "Sélectionner la méthode de discussion",
  "cmd.synthesizer": "Sélectionner le mode de synthèse",
  "cmd.status": "Afficher les paramètres actuels",
  "cmd.export": "Exporter [md|text|pdf]",
  "cmd.clear": "Effacer l'écran",
  "cmd.help": "Afficher l'aide",
  "cmd.quit": "Quitter Quorum",
  "cmd.turns": "Définir le max. de tours [nombre]",

  // Model Selector
  "selector.model.title": "Sélectionner les modèles",
  "selector.model.instructions": "(Espace pour basculer, Entrée pour confirmer)",
  "selector.model.selected": "Sélectionnés : ",
  "selector.model.minimum": "(minimum 2 requis)",
  "selector.model.warning": "Sélectionnez au moins 2 modèles pour la discussion",
  "selector.model.none": "Aucun sélectionné",
  "selector.model.navigation": "↑↓ Naviguer • Espace Basculer • Entrée Confirmer • Échap Annuler",
  "selector.model.noModels": "Aucun modèle disponible",
  "selector.model.checkApi": "Vérifiez vos clés API dans .env",

  // Method Selector
  "selector.method.title": "Sélectionner la méthode",
  "selector.method.modelsSelected": "{count} modèle{plural} sélectionné{plural}",
  "selector.method.navigation": "↑↓ Naviguer • Entrée Sélectionner • Échap Fermer",
  "selector.method.needsMin": "Nécessite {min}+ modèles",
  "selector.method.needsEven": "Nécessite un nombre pair",

  // Synthesizer Selector
  "selector.synthesizer.title": "Sélectionner le synthétiseur",
  "selector.synthesizer.navigation": "↑↓ Naviguer • Entrée Sélectionner • Échap Fermer",

  // Method Names and Descriptions
  "method.standard.name": "Standard",
  "method.standard.desc": "Discussion équilibrée orientée consensus",
  "method.standard.useCase": "Questions générales, résolution de problèmes",
  "method.standard.requirement": "2+ modèles",
  "method.oxford.name": "Oxford",
  "method.oxford.desc": "Débat formel avec équipes POUR/CONTRE",
  "method.oxford.useCase": "Décisions binaires, analyse pour/contre",
  "method.oxford.requirement": "Nombre pair (2, 4, 6...)",
  "method.advocate.name": "Avocat",
  "method.advocate.desc": "Un modèle remet en question le consensus",
  "method.advocate.useCase": "Tester les idées, éviter la pensée de groupe",
  "method.advocate.requirement": "3+ modèles",
  "method.socratic.name": "Socratique",
  "method.socratic.desc": "Dialogue guidé par les questions avec questionneur tournant",
  "method.socratic.useCase": "Exploration approfondie, révéler les hypothèses",
  "method.socratic.requirement": "2+ modèles",
  "method.delphi.name": "Delphi",
  "method.delphi.desc": "Estimations anonymes itératives vers la convergence",
  "method.delphi.useCase": "Prévisions, estimations, prédictions",
  "method.delphi.requirement": "3+ modèles",
  "method.brainstorm.name": "Brainstorm",
  "method.brainstorm.desc": "Idéation créative divergente→convergente (Osborn)",
  "method.brainstorm.useCase": "Générer des idées, solutions créatives",
  "method.brainstorm.requirement": "2+ modèles",
  "method.tradeoff.name": "Compromis",
  "method.tradeoff.desc": "Analyse multicritère structurée",
  "method.tradeoff.useCase": "Comparer les options, décisions complexes",
  "method.tradeoff.requirement": "2+ modèles",

  // Phase label
  "phase.label": "Phase",

  // Phase Names - Standard
  "phase.standard.1": "Réponses indépendantes",
  "phase.standard.2": "Critique structurée",
  "phase.standard.3": "Discussion",
  "phase.standard.4": "Positions finales",
  "phase.standard.5": "Synthèse",

  // Phase Names - Oxford
  "phase.oxford.1": "Déclarations d'ouverture",
  "phase.oxford.2": "Réfutations",
  "phase.oxford.3": "Arguments de clôture",
  "phase.oxford.4": "Jugement",

  // Phase Names - Advocate
  "phase.advocate.1": "Positions initiales",
  "phase.advocate.2": "Contre-interrogatoire",
  "phase.advocate.3": "Verdict",

  // Phase Names - Socratic
  "phase.socratic.1": "Thèse initiale",
  "phase.socratic.2": "Questionnement socratique",
  "phase.socratic.3": "Aporie",

  // Phase Names - Delphi
  "phase.delphi.1": "Tour 1 : Estimations indépendantes",
  "phase.delphi.2": "Tour 2 : Révision informée",
  "phase.delphi.3": "Tour 3 : Révision finale",
  "phase.delphi.4": "Agrégation",

  // Phase Names - Brainstorm
  "phase.brainstorm.1": "Diverger : Idées folles",
  "phase.brainstorm.2": "Construire : Combiner et étendre",
  "phase.brainstorm.3": "Converger : Sélectionner et affiner",
  "phase.brainstorm.4": "Synthèse des idées",

  // Phase Names - Tradeoff
  "phase.tradeoff.1": "Cadre : Définir les alternatives",
  "phase.tradeoff.2": "Critères : Dimensions d'évaluation",
  "phase.tradeoff.3": "Évaluer : Noter les options",
  "phase.tradeoff.4": "Décision",

  // Phase Messages (backend → frontend)
  "phase.standard.1.msg": "{count} participants répondront de manière indépendante...",
  "phase.standard.2.msg": "Tous les participants vont maintenant critiquer toutes les réponses...",
  "phase.standard.3.msg": "La discussion commence, informée par toutes les critiques...",
  "phase.standard.4.msg": "Tous les participants indiquent maintenant leur position finale...",
  "phase.standard.5.msg": "Synthèse des positions finales...",
  "phase.oxford.1.msg": "Les déclarations d'ouverture commencent. Chaque côté présente son cas.",
  "phase.oxford.2.msg": "Les réfutations commencent. Répondez aux arguments du côté adverse.",
  "phase.oxford.3.msg": "Déclarations de clôture. Les orateurs initiaux résument leurs cas.",
  "phase.oxford.4.msg": "Le juge va maintenant évaluer le débat.",
  "phase.advocate.1.msg": "Les défenseurs énoncent leurs positions initiales à examiner.",
  "phase.advocate.2.msg": "L'Advocatus Diaboli va contre-interroger chaque défenseur.",
  "phase.advocate.3.msg": "L'Advocatus Diaboli rend son verdict.",
  "phase.socratic.1.msg": "Un répondant présentera sa thèse initiale sur la question.",
  "phase.socratic.2.msg": "L'interrogatoire socratique commence. Les questionneurs cherchent les contradictions.",
  "phase.socratic.3.msg": "Aporie : Le présentateur de thèse réfléchit à ce que l'examen a révélé.",
  "phase.delphi.1.msg": "Tour 1 : Tous les panélistes fournissent des estimations anonymes indépendantes.",
  "phase.delphi.2.msg": "Tour 2 : Examiner les estimations anonymes du groupe et réviser si nécessaire.",
  "phase.delphi.3.msg": "Tour 3 : Dernière opportunité de révision avant l'agrégation.",
  "phase.delphi.4.msg": "Agrégation des estimations finales en consensus de groupe.",
  "phase.brainstorm.1.msg": "Diverger : Générer des idées folles. PAS DE JUGEMENT - la quantité avant la qualité !",
  "phase.brainstorm.2.msg": "Construire : Combiner et développer les idées des autres.",
  "phase.brainstorm.3.msg": "Converger : Vous pouvez maintenant évaluer. Sélectionnez le top 3 des idées.",
  "phase.brainstorm.4.msg": "Synthèse des idées sélectionnées.",
  "phase.tradeoff.1.msg": "Cadre : Définir les alternatives à comparer.",
  "phase.tradeoff.2.msg": "Critères : Établir les dimensions d'évaluation.",
  "phase.tradeoff.3.msg": "Évaluer : Noter chaque alternative sur chaque critère (1-10).",
  "phase.tradeoff.4.msg": "Synthèse de la recommandation avec analyse des compromis.",

  // Roles
  "role.for": "POUR",
  "role.against": "CONTRE",
  "role.advocate": "AVOCAT",
  "role.defender": "DÉFENSEUR",
  "role.questioner": "QUESTIONNEUR",
  "role.respondent": "RÉPONDANT",
  "role.panelist": "PANÉLISTE",
  "role.ideator": "IDÉATEUR",
  "role.evaluator": "ÉVALUATEUR",

  // Rounds
  "round.opening": "Déclarations d'ouverture",
  "round.rebuttal": "Réfutations",
  "round.closing": "Déclarations de clôture",

  // Messages
  "msg.independentAnswer": "(Réponse indépendante)",
  "msg.critique": "(Critique)",
  "msg.finalPosition": "(Position finale)",
  "msg.agreements": "Accords :",
  "msg.disagreements": "Désaccords :",
  "msg.missing": "Manquant :",
  "msg.synthesis": "Synthèse",
  "msg.verdict": "Verdict",
  "msg.consensus": "Consensus",
  "msg.participants": "Participants",
  "msg.question": "Q : {question}",
  "msg.startingDiscussion": "Démarrage de la discussion...",
  "msg.phaseInProgress": "Phase {phase} : {name} en cours...",
  "msg.pausePrompt": "{previousPhase} terminée. Appuyez sur Entrée pour continuer vers {nextPhase}...",
  "msg.discussionComplete": "Discussion terminée",
  "msg.pressEscNewDiscussion": "Appuyez sur ESC pour démarrer une nouvelle discussion",

  // Confidence
  "msg.confidence.high": "ÉLEVÉE",
  "msg.confidence.medium": "MOYENNE",
  "msg.confidence.low": "FAIBLE",
  "msg.confidence.breakdown": "Répartition de la confiance : ",
  "msg.confidence.panelist": "Confiance du panéliste : ",

  // Consensus values (for export)
  "consensus.yes": "OUI",
  "consensus.no": "NON",
  "consensus.partial": "PARTIEL",

  // Synthesis labels by method
  "synthesis.aporia": "Aporie atteinte",
  "synthesis.decision": "Décision",
  "synthesis.convergence": "Convergence",
  "synthesis.selectedIdeas": "Idées sélectionnées",
  "synthesis.agreement": "Accord",
  "synthesis.consensus": "Consensus",
  "synthesis.openQuestions": "Questions ouvertes",
  "synthesis.unresolvedQuestions": "Questions non résolues",
  "synthesis.keyContentions": "Points de désaccord clés",
  "synthesis.outlierPerspectives": "Perspectives divergentes",
  "synthesis.alternativeDirections": "Directions alternatives",
  "synthesis.keyTradeoffs": "Compromis clés",
  "synthesis.notableDifferences": "Différences notables",
  "synthesis.reflection": "Réflexion",
  "synthesis.ruling": "Décision",
  "synthesis.adjudication": "Arbitrage",
  "synthesis.aggregatedEstimate": "Estimation agrégée",
  "synthesis.finalIdeas": "Idées finales",
  "synthesis.recommendation": "Recommandation",
  "synthesis.synthesisLabel": "Synthèse",
  "synthesis.reflected": "a réfléchi",
  "synthesis.adjudicated": "a arbitré",
  "synthesis.synthesized": "a synthétisé",
  "synthesis.ruledBy": "(décidé par {model})",

  // Synthesizer Modes
  "synth.first.name": "Premier",
  "synth.first.desc": "Le premier modèle sélectionné synthétise",
  "synth.random.name": "Aléatoire",
  "synth.random.desc": "Modèle aléatoire à chaque fois",
  "synth.rotate.name": "Rotation",
  "synth.rotate.desc": "Alterner entre les modèles",

  // Help
  "help.title": "Aide Quorum",
  "help.commands": "Commandes :",
  "help.keyboard": "Clavier :",
  "help.key.esc": "Fermer la superposition / Retour à la saisie",
  "help.key.ctrlC": "Annuler la discussion en cours",
  "help.key.arrows": "Naviguer dans les sélecteurs",
  "help.key.enter": "Soumettre / Sélectionner",
  "help.close": "Appuyez sur Échap pour fermer",

  // Team Preview
  "team.title": "Attribution des équipes",
  "team.selectRole": "Sélectionner {role}",
  "team.chooseAdvocate": "Choisissez quel modèle va défier les autres :",
  "team.chooseRespondent": "Choisissez quel modèle va présenter la thèse :",
  "team.start": "[Entrée] Démarrer",
  "team.swap": "[S] Échanger les équipes",
  "team.navigation": "↑↓ Naviguer • Entrée Sélectionner/Démarrer • Échap Annuler",
  "team.navigationOxford": "← → Changer • Entrée Sélectionner • S Échanger • Échap Annuler",
  "team.forTeam": "POUR",
  "team.againstTeam": "CONTRE",
  "team.defenders": "DÉFENSEURS",

  // Export
  "export.title": "Exporter la discussion ({format})",
  "export.loading": "Chargement des discussions...",
  "export.noDiscussions": "Aucune discussion trouvée",
  "export.noDiscussionsDir": "Aucun rapport de discussion trouvé dans {dir}",
  "export.selectPrompt": "Sélectionnez une discussion à exporter :",
  "export.navigation": "↑↓ Naviguer  Entrée Exporter  Échap Annuler",
  "export.close": "Appuyez sur ESC pour fermer",

  // Export Document (PDF/Markdown)
  "export.doc.title": "Export de Discussion Quorum",
  "export.doc.dateLabel": "Date :",
  "export.doc.methodLabel": "Méthode :",
  "export.doc.modelsLabel": "Modèles :",
  "export.doc.questionHeader": "Question",
  "export.doc.discussionHeader": "Discussion",
  "export.doc.phaseLabel": "Phase",
  "export.doc.critiqueLabel": "Critique",
  "export.doc.finalPositionLabel": "Position Finale",
  "export.doc.agreementsLabel": "Accords :",
  "export.doc.disagreementsLabel": "Désaccords :",
  "export.doc.missingLabel": "Manquant :",
  "export.doc.confidenceLabel": "Confiance :",
  "export.doc.footer": "Exporté depuis [Quorum](https://github.com/Detrol/quorum-cli)",

  // Method Terminology - Result Labels
  "terminology.result.standard": "Résultat",
  "terminology.result.oxford": "Jugement",
  "terminology.result.advocate": "Verdict",
  "terminology.result.socratic": "Aporie",
  "terminology.result.delphi": "Agrégation",
  "terminology.result.brainstorm": "Idées Sélectionnées",
  "terminology.result.tradeoff": "Décision",

  // Method Terminology - Synthesis Labels
  "terminology.synthesis.standard": "Synthèse",
  "terminology.synthesis.oxford": "Jugement",
  "terminology.synthesis.advocate": "Décision",
  "terminology.synthesis.socratic": "Réflexion",
  "terminology.synthesis.delphi": "Estimation Agrégée",
  "terminology.synthesis.brainstorm": "Idées Finales",
  "terminology.synthesis.tradeoff": "Recommandation",

  // Method Terminology - Differences Labels
  "terminology.differences.standard": "Différences Notables",
  "terminology.differences.oxford": "Points de Contestation",
  "terminology.differences.advocate": "Questions Non Résolues",
  "terminology.differences.socratic": "Questions Ouvertes",
  "terminology.differences.delphi": "Perspectives Divergentes",
  "terminology.differences.brainstorm": "Directions Alternatives",
  "terminology.differences.tradeoff": "Compromis Clés",

  // Method Terminology - By Labels
  "terminology.by.standard": "Synthétisé par",
  "terminology.by.oxford": "Jugé par",
  "terminology.by.advocate": "Décidé par",
  "terminology.by.socratic": "Réfléchi par",
  "terminology.by.delphi": "Agrégé par",
  "terminology.by.brainstorm": "Compilé par",
  "terminology.by.tradeoff": "Analysé par",

  // Method Terminology - Consensus Labels
  "terminology.consensus.standard": "Consensus",
  "terminology.consensus.oxford": "Décision",
  "terminology.consensus.advocate": "Verdict",
  "terminology.consensus.socratic": "Aporie Atteinte",
  "terminology.consensus.delphi": "Convergence",
  "terminology.consensus.brainstorm": "Idées Sélectionnées",
  "terminology.consensus.tradeoff": "Accord",

  // Method Advisor
  "advisor.title": "CONSEILLER DE MÉTHODE",
  "advisor.prompt": "Quelle est votre question ?",
  "advisor.analyzing": "Analyse avec {model}...",
  "advisor.recommended": "RECOMMANDÉ :",
  "advisor.navigation": "↑↓ Naviguer • Entrée Sélectionner • Retour Précédent • Échap Annuler",
  "advisor.analyzedBy": "Analysé par {model}",
  "advisor.error": "Échec de l'analyse",
  "advisor.inputHint": "Entrée pour analyser • Échap pour annuler",

  // Status
  "status.title": "Paramètres actuels",
  "status.models": "Modèles : ",
  "status.method": "Méthode : ",
  "status.synthesizer": "Synthétiseur : ",
  "status.maxTurns": "Tours max. : ",
  "status.default": "par défaut",
  "status.none": "Aucun sélectionné",

  // Header
  "header.quickCommands": "Commandes rapides",
  "header.cmdModels": "/models - Sélectionner les modèles IA",
  "header.cmdMethod": "/method - Changer le style de discussion",
  "header.cmdExport": "/export - Exporter [md|text|pdf]",
  "header.cmdHelp": "/help - Toutes les commandes",

  // Command Palette
  "palette.title": "Commandes",
  "palette.hint": "(↑↓ naviguer, Entrée exécuter, Tab compléter, Échap fermer)",
  "palette.noMatches": "Aucune commande correspondante",

  // Discussion method titles
  "discussion.standard": "DISCUSSION STANDARD",
  "discussion.oxford": "DÉBAT OXFORD",
  "discussion.advocate": "AVOCAT DU DIABLE",
  "discussion.socratic": "DIALOGUE SOCRATIQUE",
  "discussion.delphi": "CONSENSUS DELPHI",
  "discussion.brainstorm": "SESSION BRAINSTORM",
  "discussion.tradeoff": "ANALYSE DES COMPROMIS",
};
