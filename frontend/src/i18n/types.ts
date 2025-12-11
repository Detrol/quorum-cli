/**
 * Type definitions for i18n translations.
 */

export type TranslationKey =
  // Existing keys
  | "thinkingComplete"
  | "thinkingInProgress"
  | "phaseComplete"

  // App-level
  | "app.title"
  | "app.subtitle"
  | "app.loading.backend"
  | "app.loading.models"
  | "app.loading.validating"
  | "app.error.generic"
  | "app.error.selectModels"
  | "app.error.oxfordEven"
  | "app.error.methodMin"
  | "app.error.exportFormat"
  | "app.success.exported"
  | "app.placeholder.selectModels"
  | "app.placeholder.askQuestion"
  | "app.statusBar.commands"
  | "app.statusBar.running"
  | "app.hint.welcome"

  // Commands
  | "cmd.models"
  | "cmd.method"
  | "cmd.synthesizer"
  | "cmd.status"
  | "cmd.export"
  | "cmd.clear"
  | "cmd.help"
  | "cmd.quit"
  | "cmd.turns"

  // Model Selector
  | "selector.model.title"
  | "selector.model.instructions"
  | "selector.model.selected"
  | "selector.model.minimum"
  | "selector.model.warning"
  | "selector.model.none"
  | "selector.model.navigation"
  | "selector.model.noModels"
  | "selector.model.checkApi"

  // Method Selector
  | "selector.method.title"
  | "selector.method.modelsSelected"
  | "selector.method.navigation"
  | "selector.method.needsMin"
  | "selector.method.needsEven"

  // Synthesizer Selector
  | "selector.synthesizer.title"
  | "selector.synthesizer.navigation"

  // Method Names
  | "method.standard.name"
  | "method.standard.desc"
  | "method.standard.useCase"
  | "method.standard.requirement"
  | "method.oxford.name"
  | "method.oxford.desc"
  | "method.oxford.useCase"
  | "method.oxford.requirement"
  | "method.advocate.name"
  | "method.advocate.desc"
  | "method.advocate.useCase"
  | "method.advocate.requirement"
  | "method.socratic.name"
  | "method.socratic.desc"
  | "method.socratic.useCase"
  | "method.socratic.requirement"
  | "method.delphi.name"
  | "method.delphi.desc"
  | "method.delphi.useCase"
  | "method.delphi.requirement"
  | "method.brainstorm.name"
  | "method.brainstorm.desc"
  | "method.brainstorm.useCase"
  | "method.brainstorm.requirement"
  | "method.tradeoff.name"
  | "method.tradeoff.desc"
  | "method.tradeoff.useCase"
  | "method.tradeoff.requirement"

  // Phase label
  | "phase.label"

  // Phase Names - Standard
  | "phase.standard.1"
  | "phase.standard.2"
  | "phase.standard.3"
  | "phase.standard.4"
  | "phase.standard.5"

  // Phase Names - Oxford
  | "phase.oxford.1"
  | "phase.oxford.2"
  | "phase.oxford.3"
  | "phase.oxford.4"

  // Phase Names - Advocate
  | "phase.advocate.1"
  | "phase.advocate.2"
  | "phase.advocate.3"

  // Phase Names - Socratic
  | "phase.socratic.1"
  | "phase.socratic.2"
  | "phase.socratic.3"

  // Phase Names - Delphi
  | "phase.delphi.1"
  | "phase.delphi.2"
  | "phase.delphi.3"
  | "phase.delphi.4"

  // Phase Names - Brainstorm
  | "phase.brainstorm.1"
  | "phase.brainstorm.2"
  | "phase.brainstorm.3"
  | "phase.brainstorm.4"

  // Phase Names - Tradeoff
  | "phase.tradeoff.1"
  | "phase.tradeoff.2"
  | "phase.tradeoff.3"
  | "phase.tradeoff.4"

  // Phase Messages (backend → frontend translation keys)
  | "phase.standard.1.msg"
  | "phase.standard.2.msg"
  | "phase.standard.3.msg"
  | "phase.standard.4.msg"
  | "phase.standard.5.msg"
  | "phase.oxford.1.msg"
  | "phase.oxford.2.msg"
  | "phase.oxford.3.msg"
  | "phase.oxford.4.msg"
  | "phase.advocate.1.msg"
  | "phase.advocate.2.msg"
  | "phase.advocate.3.msg"
  | "phase.socratic.1.msg"
  | "phase.socratic.2.msg"
  | "phase.socratic.3.msg"
  | "phase.delphi.1.msg"
  | "phase.delphi.2.msg"
  | "phase.delphi.3.msg"
  | "phase.delphi.4.msg"
  | "phase.brainstorm.1.msg"
  | "phase.brainstorm.2.msg"
  | "phase.brainstorm.3.msg"
  | "phase.brainstorm.4.msg"
  | "phase.tradeoff.1.msg"
  | "phase.tradeoff.2.msg"
  | "phase.tradeoff.3.msg"
  | "phase.tradeoff.4.msg"

  // Roles
  | "role.for"
  | "role.against"
  | "role.advocate"
  | "role.defender"
  | "role.questioner"
  | "role.respondent"
  | "role.panelist"
  | "role.ideator"
  | "role.evaluator"

  // Rounds
  | "round.opening"
  | "round.rebuttal"
  | "round.closing"

  // Messages
  | "msg.independentAnswer"
  | "msg.critique"
  | "msg.finalPosition"
  | "msg.agreements"
  | "msg.disagreements"
  | "msg.missing"
  | "msg.synthesis"
  | "msg.verdict"
  | "msg.consensus"
  | "msg.participants"
  | "msg.question"
  | "msg.startingDiscussion"
  | "msg.phaseInProgress"
  | "msg.pausePrompt"
  | "msg.discussionComplete"
  | "msg.pressEscNewDiscussion"

  // Confidence
  | "msg.confidence.high"
  | "msg.confidence.medium"
  | "msg.confidence.low"
  | "msg.confidence.breakdown"
  | "msg.confidence.panelist"

  // Consensus values (for export)
  | "consensus.yes"
  | "consensus.no"
  | "consensus.partial"

  // Synthesis labels by method
  | "synthesis.aporia"
  | "synthesis.decision"
  | "synthesis.convergence"
  | "synthesis.selectedIdeas"
  | "synthesis.agreement"
  | "synthesis.consensus"
  | "synthesis.openQuestions"
  | "synthesis.unresolvedQuestions"
  | "synthesis.keyContentions"
  | "synthesis.outlierPerspectives"
  | "synthesis.alternativeDirections"
  | "synthesis.keyTradeoffs"
  | "synthesis.notableDifferences"
  | "synthesis.reflection"
  | "synthesis.ruling"
  | "synthesis.adjudication"
  | "synthesis.aggregatedEstimate"
  | "synthesis.finalIdeas"
  | "synthesis.recommendation"
  | "synthesis.synthesisLabel"
  | "synthesis.reflected"
  | "synthesis.adjudicated"
  | "synthesis.synthesized"
  | "synthesis.ruledBy"

  // Synthesizer Modes
  | "synth.first.name"
  | "synth.first.desc"
  | "synth.random.name"
  | "synth.random.desc"
  | "synth.rotate.name"
  | "synth.rotate.desc"

  // Help
  | "help.title"
  | "help.commands"
  | "help.keyboard"
  | "help.key.esc"
  | "help.key.ctrlC"
  | "help.key.arrows"
  | "help.key.enter"
  | "help.close"

  // Team Preview
  | "team.title"
  | "team.selectRole"
  | "team.chooseAdvocate"
  | "team.chooseRespondent"
  | "team.start"
  | "team.swap"
  | "team.navigation"
  | "team.navigationOxford"
  | "team.forTeam"
  | "team.againstTeam"
  | "team.defenders"

  // Export UI
  | "export.title"
  | "export.loading"
  | "export.noDiscussions"
  | "export.noDiscussionsDir"
  | "export.selectPrompt"
  | "export.navigation"
  | "export.close"

  // Export Document (PDF/Markdown)
  | "export.doc.title"
  | "export.doc.dateLabel"
  | "export.doc.methodLabel"
  | "export.doc.modelsLabel"
  | "export.doc.questionHeader"
  | "export.doc.discussionHeader"
  | "export.doc.phaseLabel"
  | "export.doc.critiqueLabel"
  | "export.doc.finalPositionLabel"
  | "export.doc.agreementsLabel"
  | "export.doc.disagreementsLabel"
  | "export.doc.missingLabel"
  | "export.doc.confidenceLabel"
  | "export.doc.footer"

  // Method Terminology (for synthesis sections)
  | "terminology.result.standard"
  | "terminology.result.oxford"
  | "terminology.result.advocate"
  | "terminology.result.socratic"
  | "terminology.result.delphi"
  | "terminology.result.brainstorm"
  | "terminology.result.tradeoff"
  | "terminology.synthesis.standard"
  | "terminology.synthesis.oxford"
  | "terminology.synthesis.advocate"
  | "terminology.synthesis.socratic"
  | "terminology.synthesis.delphi"
  | "terminology.synthesis.brainstorm"
  | "terminology.synthesis.tradeoff"
  | "terminology.differences.standard"
  | "terminology.differences.oxford"
  | "terminology.differences.advocate"
  | "terminology.differences.socratic"
  | "terminology.differences.delphi"
  | "terminology.differences.brainstorm"
  | "terminology.differences.tradeoff"
  | "terminology.by.standard"
  | "terminology.by.oxford"
  | "terminology.by.advocate"
  | "terminology.by.socratic"
  | "terminology.by.delphi"
  | "terminology.by.brainstorm"
  | "terminology.by.tradeoff"
  | "terminology.consensus.standard"
  | "terminology.consensus.oxford"
  | "terminology.consensus.advocate"
  | "terminology.consensus.socratic"
  | "terminology.consensus.delphi"
  | "terminology.consensus.brainstorm"
  | "terminology.consensus.tradeoff"

  // Method Advisor
  | "advisor.title"
  | "advisor.prompt"
  | "advisor.analyzing"
  | "advisor.recommended"
  | "advisor.navigation"
  | "advisor.analyzedBy"
  | "advisor.error"
  | "advisor.inputHint"

  // Status
  | "status.title"
  | "status.models"
  | "status.method"
  | "status.synthesizer"
  | "status.maxTurns"
  | "status.default"
  | "status.none"

  // Header
  | "header.quickCommands"
  | "header.cmdModels"
  | "header.cmdMethod"
  | "header.cmdExport"
  | "header.cmdHelp"

  // Command Palette
  | "palette.title"
  | "palette.hint"
  | "palette.noMatches"

  // Discussion method titles
  | "discussion.standard"
  | "discussion.oxford"
  | "discussion.advocate"
  | "discussion.socratic"
  | "discussion.delphi"
  | "discussion.brainstorm"
  | "discussion.tradeoff";

export type Translations = Record<TranslationKey, string>;

export type SupportedLanguage = "en" | "sv" | "de" | "fr" | "es" | "it";
