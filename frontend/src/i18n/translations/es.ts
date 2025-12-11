/**
 * Spanish translations.
 */
import type { Translations } from "../types.js";

export const es: Translations = {
  // Existing keys
  thinkingComplete: "{model} ha terminado de pensar",
  thinkingInProgress: "{model} está pensando...",
  phaseComplete: "Fase {phase} completada",

  // App-level
  "app.title": "Quorum",
  "app.subtitle": "Sistema de discusión multi-agente",
  "app.loading.backend": "Iniciando backend...",
  "app.loading.models": "Cargando modelos...",
  "app.loading.validating": "Validando modelos ({current}/{total})...",
  "app.error.generic": "Error: {error}",
  "app.error.selectModels": "Seleccione al menos 2 modelos primero (/models)",
  "app.error.oxfordEven": "Oxford requiere un número par de modelos",
  "app.error.methodMin": "{method} requiere al menos {min} modelos",
  "app.error.exportFormat": "Formato: md, text, pdf",
  "app.success.exported": "Exportado a {path}",
  "app.placeholder.selectModels": "Escriba /models para seleccionar modelos...",
  "app.placeholder.askQuestion": "Haga una pregunta...",
  "app.statusBar.commands": "/ comandos • Tab asesor • Ctrl+R reiniciar • Ctrl+C salir",
  "app.statusBar.running": "ESC/Ctrl+R reiniciar • Ctrl+C salir",
  "app.hint.welcome": "Escriba /models para seleccionar modelos IA, o /help para comandos",

  // Commands
  "cmd.models": "Seleccionar modelos IA",
  "cmd.method": "Seleccionar método de discusión",
  "cmd.synthesizer": "Seleccionar modo de síntesis",
  "cmd.status": "Mostrar configuración actual",
  "cmd.export": "Exportar [md|text|pdf]",
  "cmd.clear": "Limpiar pantalla",
  "cmd.help": "Mostrar ayuda",
  "cmd.quit": "Salir de Quorum",
  "cmd.turns": "Establecer turnos máx. [número]",

  // Model Selector
  "selector.model.title": "Seleccionar modelos",
  "selector.model.instructions": "(Espacio para alternar, Enter para confirmar)",
  "selector.model.selected": "Seleccionados: ",
  "selector.model.minimum": "(mínimo 2 requeridos)",
  "selector.model.warning": "Seleccione al menos 2 modelos para la discusión",
  "selector.model.none": "Ninguno seleccionado",
  "selector.model.navigation": "↑↓ Navegar • Espacio Alternar • Enter Confirmar • Esc Cancelar",
  "selector.model.noModels": "No hay modelos disponibles",
  "selector.model.checkApi": "Verifique sus claves API en .env",

  // Method Selector
  "selector.method.title": "Seleccionar método",
  "selector.method.modelsSelected": "{count} modelo{plural} seleccionado{plural}",
  "selector.method.navigation": "↑↓ Navegar • Enter Seleccionar • Esc Cerrar",
  "selector.method.needsMin": "Necesita {min}+ modelos",
  "selector.method.needsEven": "Necesita número par",

  // Synthesizer Selector
  "selector.synthesizer.title": "Seleccionar sintetizador",
  "selector.synthesizer.navigation": "↑↓ Navegar • Enter Seleccionar • Esc Cerrar",

  // Method Names and Descriptions
  "method.standard.name": "Estándar",
  "method.standard.desc": "Discusión equilibrada orientada al consenso",
  "method.standard.useCase": "Preguntas generales, resolución de problemas",
  "method.standard.requirement": "2+ modelos",
  "method.oxford.name": "Oxford",
  "method.oxford.desc": "Debate formal con equipos A FAVOR/EN CONTRA",
  "method.oxford.useCase": "Decisiones binarias, análisis pros/contras",
  "method.oxford.requirement": "Número par (2, 4, 6...)",
  "method.advocate.name": "Abogado",
  "method.advocate.desc": "Un modelo desafía el consenso",
  "method.advocate.useCase": "Probar ideas, evitar pensamiento grupal",
  "method.advocate.requirement": "3+ modelos",
  "method.socratic.name": "Socrático",
  "method.socratic.desc": "Diálogo guiado por preguntas con cuestionador rotativo",
  "method.socratic.useCase": "Exploración profunda, revelar supuestos",
  "method.socratic.requirement": "2+ modelos",
  "method.delphi.name": "Delphi",
  "method.delphi.desc": "Estimaciones anónimas iterativas hacia convergencia",
  "method.delphi.useCase": "Pronósticos, estimaciones, predicciones",
  "method.delphi.requirement": "3+ modelos",
  "method.brainstorm.name": "Lluvia de ideas",
  "method.brainstorm.desc": "Ideación creativa divergente→convergente (Osborn)",
  "method.brainstorm.useCase": "Generar ideas, soluciones creativas",
  "method.brainstorm.requirement": "2+ modelos",
  "method.tradeoff.name": "Compensación",
  "method.tradeoff.desc": "Análisis multicriterio estructurado",
  "method.tradeoff.useCase": "Comparar opciones, decisiones complejas",
  "method.tradeoff.requirement": "2+ modelos",

  // Phase label
  "phase.label": "Fase",

  // Phase Names - Standard
  "phase.standard.1": "Respuestas independientes",
  "phase.standard.2": "Crítica estructurada",
  "phase.standard.3": "Discusión",
  "phase.standard.4": "Posiciones finales",
  "phase.standard.5": "Síntesis",

  // Phase Names - Oxford
  "phase.oxford.1": "Declaraciones de apertura",
  "phase.oxford.2": "Refutaciones",
  "phase.oxford.3": "Argumentos de cierre",
  "phase.oxford.4": "Juicio",

  // Phase Names - Advocate
  "phase.advocate.1": "Posiciones iniciales",
  "phase.advocate.2": "Interrogatorio cruzado",
  "phase.advocate.3": "Veredicto",

  // Phase Names - Socratic
  "phase.socratic.1": "Tesis inicial",
  "phase.socratic.2": "Indagación socrática",
  "phase.socratic.3": "Aporía",

  // Phase Names - Delphi
  "phase.delphi.1": "Ronda 1: Estimaciones independientes",
  "phase.delphi.2": "Ronda 2: Revisión informada",
  "phase.delphi.3": "Ronda 3: Revisión final",
  "phase.delphi.4": "Agregación",

  // Phase Names - Brainstorm
  "phase.brainstorm.1": "Divergir: Ideas locas",
  "phase.brainstorm.2": "Construir: Combinar y expandir",
  "phase.brainstorm.3": "Converger: Seleccionar y refinar",
  "phase.brainstorm.4": "Síntesis de ideas",

  // Phase Names - Tradeoff
  "phase.tradeoff.1": "Marco: Definir alternativas",
  "phase.tradeoff.2": "Criterios: Dimensiones de evaluación",
  "phase.tradeoff.3": "Evaluar: Puntuar opciones",
  "phase.tradeoff.4": "Decisión",

  // Phase Messages (backend → frontend)
  "phase.standard.1.msg": "{count} participantes responderán de forma independiente...",
  "phase.standard.2.msg": "Todos los participantes criticarán ahora todas las respuestas...",
  "phase.standard.3.msg": "La discusión comienza, informada por todas las críticas...",
  "phase.standard.4.msg": "Todos los participantes indicarán ahora su posición final...",
  "phase.standard.5.msg": "Sintetizando posiciones finales...",
  "phase.oxford.1.msg": "Comienzan las declaraciones de apertura. Cada lado presenta su caso.",
  "phase.oxford.2.msg": "Comienzan las refutaciones. Responda a los argumentos del lado opuesto.",
  "phase.oxford.3.msg": "Declaraciones de cierre. Los oradores originales resumen sus casos.",
  "phase.oxford.4.msg": "El juez evaluará ahora el debate.",
  "phase.advocate.1.msg": "Los defensores exponen sus posiciones iniciales para ser examinadas.",
  "phase.advocate.2.msg": "El Advocatus Diaboli interrogará a cada defensor.",
  "phase.advocate.3.msg": "El Advocatus Diaboli emite su veredicto.",
  "phase.socratic.1.msg": "Un encuestado presentará su tesis inicial sobre la pregunta.",
  "phase.socratic.2.msg": "Comienza el interrogatorio socrático. Los cuestionadores buscan contradicciones.",
  "phase.socratic.3.msg": "Aporía: El presentador de la tesis reflexiona sobre lo que reveló el examen.",
  "phase.delphi.1.msg": "Ronda 1: Todos los panelistas proporcionan estimaciones independientes anónimas.",
  "phase.delphi.2.msg": "Ronda 2: Revisar estimaciones anónimas del grupo y revisar si es necesario.",
  "phase.delphi.3.msg": "Ronda 3: Última oportunidad de revisión antes de la agregación.",
  "phase.delphi.4.msg": "Agregando estimaciones finales en consenso grupal.",
  "phase.brainstorm.1.msg": "Divergir: Generar ideas locas. ¡SIN JUICIOS - cantidad sobre calidad!",
  "phase.brainstorm.2.msg": "Construir: Combinar y expandir las ideas de los demás.",
  "phase.brainstorm.3.msg": "Converger: Ahora pueden evaluar. Seleccionen las 3 mejores ideas.",
  "phase.brainstorm.4.msg": "Sintetizando ideas seleccionadas finales.",
  "phase.tradeoff.1.msg": "Marco: Definir las alternativas a comparar.",
  "phase.tradeoff.2.msg": "Criterios: Establecer dimensiones de evaluación.",
  "phase.tradeoff.3.msg": "Evaluar: Puntuar cada alternativa en cada criterio (1-10).",
  "phase.tradeoff.4.msg": "Sintetizando recomendación con análisis de compensaciones.",

  // Roles
  "role.for": "A FAVOR",
  "role.against": "EN CONTRA",
  "role.advocate": "ABOGADO",
  "role.defender": "DEFENSOR",
  "role.questioner": "CUESTIONADOR",
  "role.respondent": "ENCUESTADO",
  "role.panelist": "PANELISTA",
  "role.ideator": "IDEADOR",
  "role.evaluator": "EVALUADOR",

  // Rounds
  "round.opening": "Declaraciones de apertura",
  "round.rebuttal": "Refutaciones",
  "round.closing": "Declaraciones de cierre",

  // Messages
  "msg.independentAnswer": "(Respuesta independiente)",
  "msg.critique": "(Crítica)",
  "msg.finalPosition": "(Posición final)",
  "msg.agreements": "Acuerdos:",
  "msg.disagreements": "Desacuerdos:",
  "msg.missing": "Faltante:",
  "msg.synthesis": "Síntesis",
  "msg.verdict": "Veredicto",
  "msg.consensus": "Consenso",
  "msg.participants": "Participantes",
  "msg.question": "P: {question}",
  "msg.startingDiscussion": "Iniciando discusión...",
  "msg.phaseInProgress": "Fase {phase}: {name} en progreso...",
  "msg.pausePrompt": "{previousPhase} completada. Presione Enter para continuar a {nextPhase}...",
  "msg.discussionComplete": "Discusión completada",
  "msg.pressEscNewDiscussion": "Presione ESC para iniciar una nueva discusión",

  // Confidence
  "msg.confidence.high": "ALTA",
  "msg.confidence.medium": "MEDIA",
  "msg.confidence.low": "BAJA",
  "msg.confidence.breakdown": "Desglose de confianza: ",
  "msg.confidence.panelist": "Confianza del panelista: ",

  // Consensus values (for export)
  "consensus.yes": "SÍ",
  "consensus.no": "NO",
  "consensus.partial": "PARCIAL",

  // Synthesis labels by method
  "synthesis.aporia": "Aporía alcanzada",
  "synthesis.decision": "Decisión",
  "synthesis.convergence": "Convergencia",
  "synthesis.selectedIdeas": "Ideas seleccionadas",
  "synthesis.agreement": "Acuerdo",
  "synthesis.consensus": "Consenso",
  "synthesis.openQuestions": "Preguntas abiertas",
  "synthesis.unresolvedQuestions": "Preguntas sin resolver",
  "synthesis.keyContentions": "Puntos clave de desacuerdo",
  "synthesis.outlierPerspectives": "Perspectivas divergentes",
  "synthesis.alternativeDirections": "Direcciones alternativas",
  "synthesis.keyTradeoffs": "Compensaciones clave",
  "synthesis.notableDifferences": "Diferencias notables",
  "synthesis.reflection": "Reflexión",
  "synthesis.ruling": "Fallo",
  "synthesis.adjudication": "Adjudicación",
  "synthesis.aggregatedEstimate": "Estimación agregada",
  "synthesis.finalIdeas": "Ideas finales",
  "synthesis.recommendation": "Recomendación",
  "synthesis.synthesisLabel": "Síntesis",
  "synthesis.reflected": "reflexionó",
  "synthesis.adjudicated": "adjudicó",
  "synthesis.synthesized": "sintetizó",
  "synthesis.ruledBy": "(decidido por {model})",

  // Synthesizer Modes
  "synth.first.name": "Primero",
  "synth.first.desc": "El primer modelo seleccionado sintetiza",
  "synth.random.name": "Aleatorio",
  "synth.random.desc": "Modelo aleatorio cada vez",
  "synth.rotate.name": "Rotar",
  "synth.rotate.desc": "Rotar entre modelos",

  // Help
  "help.title": "Ayuda de Quorum",
  "help.commands": "Comandos:",
  "help.keyboard": "Teclado:",
  "help.key.esc": "Cerrar superposición / Volver a entrada",
  "help.key.ctrlC": "Cancelar discusión en curso",
  "help.key.arrows": "Navegar en selectores",
  "help.key.enter": "Enviar / Seleccionar",
  "help.close": "Presione Esc para cerrar",

  // Team Preview
  "team.title": "Asignación de equipos",
  "team.selectRole": "Seleccionar {role}",
  "team.chooseAdvocate": "Elija qué modelo desafiará a los demás:",
  "team.chooseRespondent": "Elija qué modelo presentará la tesis:",
  "team.start": "[Enter] Iniciar",
  "team.swap": "[S] Intercambiar equipos",
  "team.navigation": "↑↓ Navegar • Enter Seleccionar/Iniciar • Esc Cancelar",
  "team.navigationOxford": "← → Cambiar • Enter Seleccionar • S Intercambiar • Esc Cancelar",
  "team.forTeam": "A FAVOR",
  "team.againstTeam": "EN CONTRA",
  "team.defenders": "DEFENSORES",

  // Export
  "export.title": "Exportar discusión ({format})",
  "export.loading": "Cargando discusiones...",
  "export.noDiscussions": "No se encontraron discusiones",
  "export.noDiscussionsDir": "No se encontraron informes de discusión en {dir}",
  "export.selectPrompt": "Seleccione una discusión para exportar:",
  "export.navigation": "↑↓ Navegar  Enter Exportar  Esc Cancelar",
  "export.close": "Presione ESC para cerrar",

  // Export Document (PDF/Markdown)
  "export.doc.title": "Exportación de Discusión Quorum",
  "export.doc.dateLabel": "Fecha:",
  "export.doc.methodLabel": "Método:",
  "export.doc.modelsLabel": "Modelos:",
  "export.doc.questionHeader": "Pregunta",
  "export.doc.discussionHeader": "Discusión",
  "export.doc.phaseLabel": "Fase",
  "export.doc.critiqueLabel": "Crítica",
  "export.doc.finalPositionLabel": "Posición Final",
  "export.doc.agreementsLabel": "Acuerdos:",
  "export.doc.disagreementsLabel": "Desacuerdos:",
  "export.doc.missingLabel": "Faltante:",
  "export.doc.confidenceLabel": "Confianza:",
  "export.doc.footer": "Exportado desde [Quorum](https://github.com/Detrol/quorum-cli)",

  // Method Terminology - Result Labels
  "terminology.result.standard": "Resultado",
  "terminology.result.oxford": "Juicio",
  "terminology.result.advocate": "Veredicto",
  "terminology.result.socratic": "Aporía",
  "terminology.result.delphi": "Agregación",
  "terminology.result.brainstorm": "Ideas Seleccionadas",
  "terminology.result.tradeoff": "Decisión",

  // Method Terminology - Synthesis Labels
  "terminology.synthesis.standard": "Síntesis",
  "terminology.synthesis.oxford": "Adjudicación",
  "terminology.synthesis.advocate": "Fallo",
  "terminology.synthesis.socratic": "Reflexión",
  "terminology.synthesis.delphi": "Estimación Agregada",
  "terminology.synthesis.brainstorm": "Ideas Finales",
  "terminology.synthesis.tradeoff": "Recomendación",

  // Method Terminology - Differences Labels
  "terminology.differences.standard": "Diferencias Notables",
  "terminology.differences.oxford": "Puntos de Controversia",
  "terminology.differences.advocate": "Preguntas Sin Resolver",
  "terminology.differences.socratic": "Preguntas Abiertas",
  "terminology.differences.delphi": "Perspectivas Atípicas",
  "terminology.differences.brainstorm": "Direcciones Alternativas",
  "terminology.differences.tradeoff": "Compensaciones Clave",

  // Method Terminology - By Labels
  "terminology.by.standard": "Sintetizado por",
  "terminology.by.oxford": "Adjudicado por",
  "terminology.by.advocate": "Fallado por",
  "terminology.by.socratic": "Reflejado por",
  "terminology.by.delphi": "Agregado por",
  "terminology.by.brainstorm": "Compilado por",
  "terminology.by.tradeoff": "Analizado por",

  // Method Terminology - Consensus Labels
  "terminology.consensus.standard": "Consenso",
  "terminology.consensus.oxford": "Decisión",
  "terminology.consensus.advocate": "Veredicto",
  "terminology.consensus.socratic": "Aporía Alcanzada",
  "terminology.consensus.delphi": "Convergencia",
  "terminology.consensus.brainstorm": "Ideas Seleccionadas",
  "terminology.consensus.tradeoff": "Acuerdo",

  // Method Advisor
  "advisor.title": "ASESOR DE MÉTODO",
  "advisor.prompt": "¿Cuál es su pregunta?",
  "advisor.analyzing": "Analizando con {model}...",
  "advisor.recommended": "RECOMENDADO:",
  "advisor.navigation": "↑↓ Navegar • Enter Seleccionar • Retroceso Atrás • Esc Cancelar",
  "advisor.analyzedBy": "Analizado por {model}",
  "advisor.error": "Análisis fallido",
  "advisor.inputHint": "Enter para analizar • Esc para cancelar",

  // Status
  "status.title": "Configuración actual",
  "status.models": "Modelos: ",
  "status.method": "Método: ",
  "status.synthesizer": "Sintetizador: ",
  "status.maxTurns": "Turnos máx.: ",
  "status.default": "predeterminado",
  "status.none": "Ninguno seleccionado",

  // Header
  "header.quickCommands": "Comandos rápidos",
  "header.cmdModels": "/models - Seleccionar modelos IA",
  "header.cmdMethod": "/method - Cambiar estilo de discusión",
  "header.cmdExport": "/export - Exportar [md|text|pdf]",
  "header.cmdHelp": "/help - Todos los comandos",

  // Command Palette
  "palette.title": "Comandos",
  "palette.hint": "(↑↓ navegar, Enter ejecutar, Tab completar, Esc cerrar)",
  "palette.noMatches": "No hay comandos coincidentes",

  // Discussion method titles
  "discussion.standard": "DISCUSIÓN ESTÁNDAR",
  "discussion.oxford": "DEBATE OXFORD",
  "discussion.advocate": "ABOGADO DEL DIABLO",
  "discussion.socratic": "DIÁLOGO SOCRÁTICO",
  "discussion.delphi": "CONSENSO DELPHI",
  "discussion.brainstorm": "SESIÓN DE LLUVIA DE IDEAS",
  "discussion.tradeoff": "ANÁLISIS DE COMPENSACIONES",
};
