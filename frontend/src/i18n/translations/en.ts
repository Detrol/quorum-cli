/**
 * English translations (base language).
 */
import type { Translations } from "../types.js";

export const en: Translations = {
  // Existing keys
  thinkingComplete: "{model} finished thinking",
  thinkingInProgress: "{model} is thinking...",
  phaseComplete: "Phase {phase} complete",

  // App-level
  "app.title": "Quorum",
  "app.subtitle": "Multi-Agent Discussion System",
  "app.loading.backend": "Starting backend...",
  "app.loading.models": "Loading models...",
  "app.loading.validating": "Validating models ({current}/{total})...",
  "app.error.generic": "Error: {error}",
  "app.error.selectModels": "Select at least 2 models first (/models)",
  "app.error.oxfordEven": "Oxford requires an even number of models",
  "app.error.methodMin": "{method} requires at least {min} models",
  "app.error.exportFormat": "Format: md, text, pdf",
  "app.success.exported": "Exported to {path}",
  "app.placeholder.selectModels": "Type /models to select models...",
  "app.placeholder.askQuestion": "Ask a question...",
  "app.statusBar.commands": "/ commands • Tab advisor • Ctrl+R restart • Ctrl+C quit",
  "app.statusBar.running": "ESC/Ctrl+R restart • Ctrl+C quit",
  "app.hint.welcome": "Type /models to select AI models, or /help for commands",

  // Commands
  "cmd.models": "Select AI models",
  "cmd.method": "Select discussion method",
  "cmd.synthesizer": "Select synthesizer mode",
  "cmd.status": "Show current settings",
  "cmd.export": "Export [md|text|pdf]",
  "cmd.clear": "Clear screen",
  "cmd.help": "Show help",
  "cmd.quit": "Exit Quorum",
  "cmd.turns": "Set max turns [number]",

  // Model Selector
  "selector.model.title": "Select Models",
  "selector.model.instructions": "(Space to toggle, Enter to confirm)",
  "selector.model.selected": "Selected: ",
  "selector.model.minimum": "(minimum 2 required)",
  "selector.model.warning": "Select at least 2 models for discussion",
  "selector.model.none": "None selected",
  "selector.model.navigation": "↑↓ Navigate • Space Toggle • Enter Confirm • Esc Cancel",
  "selector.model.noModels": "No models available",
  "selector.model.checkApi": "Check your API keys in .env",

  // Method Selector
  "selector.method.title": "Select Method",
  "selector.method.modelsSelected": "{count} model{plural} selected",
  "selector.method.navigation": "↑↓ Navigate • Enter Select • Esc Close",
  "selector.method.needsMin": "Needs {min}+ models",
  "selector.method.needsEven": "Needs even number",

  // Synthesizer Selector
  "selector.synthesizer.title": "Select Synthesizer",
  "selector.synthesizer.navigation": "↑↓ Navigate • Enter Select • Esc Close",

  // Method Names and Descriptions
  "method.standard.name": "Standard",
  "method.standard.desc": "Balanced consensus-seeking discussion",
  "method.standard.useCase": "General questions, problem-solving",
  "method.standard.requirement": "2+ models",
  "method.oxford.name": "Oxford",
  "method.oxford.desc": "Formal debate with FOR/AGAINST teams",
  "method.oxford.useCase": "Binary decisions, pros/cons analysis",
  "method.oxford.requirement": "Even number (2, 4, 6...)",
  "method.advocate.name": "Advocate",
  "method.advocate.desc": "One model challenges the consensus",
  "method.advocate.useCase": "Stress-testing ideas, avoiding groupthink",
  "method.advocate.requirement": "3+ models",
  "method.socratic.name": "Socratic",
  "method.socratic.desc": "Question-driven dialogue with rotating questioner",
  "method.socratic.useCase": "Deep exploration, exposing assumptions",
  "method.socratic.requirement": "2+ models",
  "method.delphi.name": "Delphi",
  "method.delphi.desc": "Iterative anonymous estimates toward convergence",
  "method.delphi.useCase": "Forecasting, estimation, predictions",
  "method.delphi.requirement": "3+ models",
  "method.brainstorm.name": "Brainstorm",
  "method.brainstorm.desc": "Divergent→convergent creative ideation (Osborn)",
  "method.brainstorm.useCase": "Generating ideas, creative solutions",
  "method.brainstorm.requirement": "2+ models",
  "method.tradeoff.name": "Tradeoff",
  "method.tradeoff.desc": "Structured multi-criteria decision analysis",
  "method.tradeoff.useCase": "Comparing options, complex decisions",
  "method.tradeoff.requirement": "2+ models",

  // Phase label
  "phase.label": "Phase",

  // Phase Names - Standard
  "phase.standard.1": "Independent Answers",
  "phase.standard.2": "Structured Critique",
  "phase.standard.3": "Discussion",
  "phase.standard.4": "Final Positions",
  "phase.standard.5": "Synthesis",

  // Phase Names - Oxford
  "phase.oxford.1": "Opening Statements",
  "phase.oxford.2": "Rebuttals",
  "phase.oxford.3": "Closing Arguments",
  "phase.oxford.4": "Judgement",

  // Phase Names - Advocate
  "phase.advocate.1": "Initial Positions",
  "phase.advocate.2": "Cross-Examination",
  "phase.advocate.3": "Verdict",

  // Phase Names - Socratic
  "phase.socratic.1": "Initial Thesis",
  "phase.socratic.2": "Socratic Inquiry",
  "phase.socratic.3": "Aporia",

  // Phase Names - Delphi
  "phase.delphi.1": "Round 1: Independent Estimates",
  "phase.delphi.2": "Round 2: Informed Revision",
  "phase.delphi.3": "Round 3: Final Revision",
  "phase.delphi.4": "Aggregation",

  // Phase Names - Brainstorm
  "phase.brainstorm.1": "Diverge: Wild Ideas",
  "phase.brainstorm.2": "Build: Combine & Expand",
  "phase.brainstorm.3": "Converge: Select & Refine",
  "phase.brainstorm.4": "Idea Synthesis",

  // Phase Names - Tradeoff
  "phase.tradeoff.1": "Frame: Define Alternatives",
  "phase.tradeoff.2": "Criteria: Evaluation Dimensions",
  "phase.tradeoff.3": "Evaluate: Score Options",
  "phase.tradeoff.4": "Decision",

  // Phase Messages (backend → frontend)
  "phase.standard.1.msg": "{count} participants will answer independently...",
  "phase.standard.2.msg": "All participants will now critique all answers...",
  "phase.standard.3.msg": "Discussion begins, informed by all critiques...",
  "phase.standard.4.msg": "All participants will now state their final position...",
  "phase.standard.5.msg": "Synthesizing final positions...",
  "phase.oxford.1.msg": "Opening statements begin. Each side presents their case.",
  "phase.oxford.2.msg": "Rebuttals begin. Respond to the opposing side's arguments.",
  "phase.oxford.3.msg": "Closing arguments. The original proposer and opposer summarize their cases.",
  "phase.oxford.4.msg": "The judge will now evaluate the debate.",
  "phase.advocate.1.msg": "Defenders state their initial positions to be examined.",
  "phase.advocate.2.msg": "The Advocatus Diaboli will cross-examine each defender.",
  "phase.advocate.3.msg": "The Advocatus Diaboli delivers the verdict.",
  "phase.socratic.1.msg": "A respondent will present their initial thesis on the question.",
  "phase.socratic.2.msg": "The Socratic inquiry begins. Questioners will probe for contradictions.",
  "phase.socratic.3.msg": "Aporia: The thesis presenter reflects on what the examination revealed.",
  "phase.delphi.1.msg": "Round 1: All panelists provide independent estimates anonymously.",
  "phase.delphi.2.msg": "Round 2: Review anonymous group estimates and revise if warranted.",
  "phase.delphi.3.msg": "Round 3: Final revision opportunity before aggregation.",
  "phase.delphi.4.msg": "Aggregating final estimates into group consensus.",
  "phase.brainstorm.1.msg": "Diverge: Generate wild ideas. NO JUDGMENT - quantity over quality!",
  "phase.brainstorm.2.msg": "Build: Combine and expand on each other's ideas.",
  "phase.brainstorm.3.msg": "Converge: Now you may evaluate. Select top 3 ideas.",
  "phase.brainstorm.4.msg": "Synthesizing final selected ideas.",
  "phase.tradeoff.1.msg": "Frame: Define the alternatives to compare.",
  "phase.tradeoff.2.msg": "Criteria: Establish evaluation dimensions.",
  "phase.tradeoff.3.msg": "Evaluate: Score each alternative on each criterion (1-10).",
  "phase.tradeoff.4.msg": "Synthesizing recommendation with tradeoff analysis.",

  // Roles
  "role.for": "FOR",
  "role.against": "AGAINST",
  "role.advocate": "ADVOCATE",
  "role.defender": "DEFENDER",
  "role.questioner": "QUESTIONER",
  "role.respondent": "RESPONDENT",
  "role.panelist": "PANELIST",
  "role.ideator": "IDEATOR",
  "role.evaluator": "EVALUATOR",

  // Rounds
  "round.opening": "Opening Statements",
  "round.rebuttal": "Rebuttals",
  "round.closing": "Closing Statements",

  // Messages
  "msg.independentAnswer": "(Independent Answer)",
  "msg.critique": "(Critique)",
  "msg.finalPosition": "(Final Position)",
  "msg.agreements": "Agreements:",
  "msg.disagreements": "Disagreements:",
  "msg.missing": "Missing:",
  "msg.synthesis": "Synthesis",
  "msg.verdict": "Verdict",
  "msg.consensus": "Consensus",
  "msg.participants": "Participants",
  "msg.question": "Q: {question}",
  "msg.startingDiscussion": "Starting discussion...",
  "msg.phaseInProgress": "Phase {phase}: {name} in progress...",
  "msg.pausePrompt": "{previousPhase} complete. Press Enter to continue to {nextPhase}...",
  "msg.discussionComplete": "Discussion Complete",
  "msg.pressEscNewDiscussion": "Press ESC to start a new discussion",

  // Confidence
  "msg.confidence.high": "HIGH",
  "msg.confidence.medium": "MEDIUM",
  "msg.confidence.low": "LOW",
  "msg.confidence.breakdown": "Confidence breakdown: ",
  "msg.confidence.panelist": "Panelist confidence: ",

  // Consensus values (for export)
  "consensus.yes": "YES",
  "consensus.no": "NO",
  "consensus.partial": "PARTIAL",

  // Synthesis labels by method
  "synthesis.aporia": "Aporia Reached",
  "synthesis.decision": "Decision",
  "synthesis.convergence": "Convergence",
  "synthesis.selectedIdeas": "Selected Ideas",
  "synthesis.agreement": "Agreement",
  "synthesis.consensus": "Consensus",
  "synthesis.openQuestions": "Open Questions",
  "synthesis.unresolvedQuestions": "Unresolved Questions",
  "synthesis.keyContentions": "Key Contentions",
  "synthesis.outlierPerspectives": "Outlier Perspectives",
  "synthesis.alternativeDirections": "Alternative Directions",
  "synthesis.keyTradeoffs": "Key Tradeoffs",
  "synthesis.notableDifferences": "Notable Differences",
  "synthesis.reflection": "Reflection",
  "synthesis.ruling": "Ruling",
  "synthesis.adjudication": "Adjudication",
  "synthesis.aggregatedEstimate": "Aggregated Estimate",
  "synthesis.finalIdeas": "Final Ideas",
  "synthesis.recommendation": "Recommendation",
  "synthesis.synthesisLabel": "Synthesis",
  "synthesis.reflected": "reflected",
  "synthesis.adjudicated": "adjudicated",
  "synthesis.synthesized": "synthesized",
  "synthesis.ruledBy": "(ruled by {model})",

  // Synthesizer Modes
  "synth.first.name": "First",
  "synth.first.desc": "First selected model synthesizes",
  "synth.random.name": "Random",
  "synth.random.desc": "Random model each time",
  "synth.rotate.name": "Rotate",
  "synth.rotate.desc": "Rotate between models",

  // Help
  "help.title": "Quorum Help",
  "help.commands": "Commands:",
  "help.keyboard": "Keyboard:",
  "help.key.esc": "Close overlay / Back to input",
  "help.key.ctrlC": "Cancel running discussion",
  "help.key.arrows": "Navigate in selectors",
  "help.key.enter": "Submit / Select",
  "help.close": "Press Esc to close",

  // Team Preview
  "team.title": "Team Assignments",
  "team.selectRole": "Select {role}",
  "team.chooseAdvocate": "Choose which model will challenge the others:",
  "team.chooseRespondent": "Choose which model will present the thesis:",
  "team.start": "[Enter] Start",
  "team.swap": "[S] Swap Teams",
  "team.navigation": "↑↓ Navigate • Enter Select/Start • Esc Cancel",
  "team.navigationOxford": "← → Switch • Enter Select • S Swap • Esc Cancel",
  "team.forTeam": "FOR",
  "team.againstTeam": "AGAINST",
  "team.defenders": "DEFENDERS",

  // Export
  "export.title": "Export Discussion ({format})",
  "export.loading": "Loading discussions...",
  "export.noDiscussions": "No Discussions Found",
  "export.noDiscussionsDir": "No discussion reports found in {dir}",
  "export.selectPrompt": "Select a discussion to export:",
  "export.navigation": "↑↓ Navigate  Enter Export  Esc Cancel",
  "export.close": "Press ESC to close",

  // Export Document (PDF/Markdown)
  "export.doc.title": "Quorum Discussion Export",
  "export.doc.dateLabel": "Date:",
  "export.doc.methodLabel": "Method:",
  "export.doc.modelsLabel": "Models:",
  "export.doc.questionHeader": "Question",
  "export.doc.discussionHeader": "Discussion",
  "export.doc.phaseLabel": "Phase",
  "export.doc.critiqueLabel": "Critique",
  "export.doc.finalPositionLabel": "Final Position",
  "export.doc.agreementsLabel": "Agreements:",
  "export.doc.disagreementsLabel": "Disagreements:",
  "export.doc.missingLabel": "Missing:",
  "export.doc.confidenceLabel": "Confidence:",
  "export.doc.footer": "Exported from [Quorum](https://github.com/Detrol/quorum-cli)",

  // Method Terminology - Result Labels
  "terminology.result.standard": "Result",
  "terminology.result.oxford": "Judgement",
  "terminology.result.advocate": "Verdict",
  "terminology.result.socratic": "Aporia",
  "terminology.result.delphi": "Aggregation",
  "terminology.result.brainstorm": "Selected Ideas",
  "terminology.result.tradeoff": "Decision",

  // Method Terminology - Synthesis Labels
  "terminology.synthesis.standard": "Synthesis",
  "terminology.synthesis.oxford": "Adjudication",
  "terminology.synthesis.advocate": "Ruling",
  "terminology.synthesis.socratic": "Reflection",
  "terminology.synthesis.delphi": "Aggregated Estimate",
  "terminology.synthesis.brainstorm": "Final Ideas",
  "terminology.synthesis.tradeoff": "Recommendation",

  // Method Terminology - Differences Labels
  "terminology.differences.standard": "Notable Differences",
  "terminology.differences.oxford": "Key Contentions",
  "terminology.differences.advocate": "Unresolved Questions",
  "terminology.differences.socratic": "Open Questions",
  "terminology.differences.delphi": "Outlier Perspectives",
  "terminology.differences.brainstorm": "Alternative Directions",
  "terminology.differences.tradeoff": "Key Tradeoffs",

  // Method Terminology - By Labels
  "terminology.by.standard": "Synthesized by",
  "terminology.by.oxford": "Adjudicated by",
  "terminology.by.advocate": "Ruled by",
  "terminology.by.socratic": "Reflected by",
  "terminology.by.delphi": "Aggregated by",
  "terminology.by.brainstorm": "Compiled by",
  "terminology.by.tradeoff": "Analyzed by",

  // Method Terminology - Consensus Labels
  "terminology.consensus.standard": "Consensus",
  "terminology.consensus.oxford": "Decision",
  "terminology.consensus.advocate": "Verdict",
  "terminology.consensus.socratic": "Aporia Reached",
  "terminology.consensus.delphi": "Convergence",
  "terminology.consensus.brainstorm": "Ideas Selected",
  "terminology.consensus.tradeoff": "Agreement",

  // Method Advisor
  "advisor.title": "METHOD ADVISOR",
  "advisor.prompt": "What's your question?",
  "advisor.analyzing": "Analyzing with {model}...",
  "advisor.recommended": "RECOMMENDED:",
  "advisor.navigation": "↑↓ Navigate • Enter Select • Backspace Back • Esc Cancel",
  "advisor.analyzedBy": "Analyzed by {model}",
  "advisor.error": "Analysis failed",
  "advisor.inputHint": "Enter to analyze • Esc to cancel",

  // Status
  "status.title": "Current Settings",
  "status.models": "Models: ",
  "status.method": "Method: ",
  "status.synthesizer": "Synthesizer: ",
  "status.maxTurns": "Max Turns: ",
  "status.default": "default",
  "status.none": "None selected",

  // Header
  "header.quickCommands": "Quick commands",
  "header.cmdModels": "/models - Select AI models",
  "header.cmdMethod": "/method - Change discussion style",
  "header.cmdExport": "/export - Export [md|text|pdf]",
  "header.cmdHelp": "/help - All commands",

  // Command Palette
  "palette.title": "Commands",
  "palette.hint": "(↑↓ navigate, Enter run, Tab fill, Esc close)",
  "palette.noMatches": "No matching commands",

  // Discussion method titles
  "discussion.standard": "STANDARD DISCUSSION",
  "discussion.oxford": "OXFORD DEBATE",
  "discussion.advocate": "DEVIL'S ADVOCATE",
  "discussion.socratic": "SOCRATIC DIALOGUE",
  "discussion.delphi": "DELPHI CONSENSUS",
  "discussion.brainstorm": "BRAINSTORM SESSION",
  "discussion.tradeoff": "TRADEOFF ANALYSIS",
};
