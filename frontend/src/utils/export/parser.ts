/**
 * Markdown log parser for Quorum discussion exports.
 * Parses structured markdown into ParsedDiscussionDocument format.
 */

// Structural patterns for identifying markdown elements
// IMPORTANT: These patterns MUST match EXACTLY what i18n translations produce (see translations/*.ts)
// Multi-language support: patterns match all 6 supported languages (EN, SV, DE, FR, ES, IT)
const STRUCTURAL_PATTERNS = {
  // Section headers (en, sv, de, fr, es, it)
  QUESTION: /^## (Question|Fråga|Frage|Question|Pregunta|Domanda)$/,
  DISCUSSION: /^## (Discussion|Diskussion|Diskussion|Discussion|Discusión|Discussione)$/,

  // Result headers - terminology.result.* (all 7 methods × 6 languages)
  // EN: Result, Judgement, Verdict, Aporia, Aggregation, Selected Ideas, Decision
  // SV: Resultat, Dom, Utslag, Apori, Aggregering, Valda idéer, Beslut
  // DE: Ergebnis, Urteil, Verdikt, Aporie, Aggregation, Ausgewählte Ideen, Entscheidung
  // FR: Résultat, Jugement, Verdict, Aporie, Agrégation, Idées Sélectionnées, Décision
  // ES: Resultado, Juicio, Veredicto, Aporía, Agregación, Ideas Seleccionadas, Decisión
  // IT: Risultato, Giudizio, Verdetto, Aporia, Aggregazione, Idee Selezionate, Decisione
  RESULT: /^## (Result|Judgement|Verdict|Aporia|Aggregation|Selected Ideas|Decision|Resultat|Dom|Utslag|Apori|Aggregering|Valda idéer|Beslut|Ergebnis|Urteil|Verdikt|Aporie|Aggregation|Ausgewählte Ideen|Entscheidung|Résultat|Jugement|Verdict|Aporie|Agrégation|Idées Sélectionnées|Décision|Resultado|Juicio|Veredicto|Aporía|Agregación|Ideas Seleccionadas|Decisión|Risultato|Giudizio|Verdetto|Aporia|Aggregazione|Idee Selezionate|Decisione)$/,

  // Phase headers (en/de/fr: Phase, sv: Fas, es/it: Fase)
  PHASE: /^### (Phase|Fas|Fase) (\d+):\s*(.*)$/,

  // Message headers (all variants) - includes translated critique/position labels
  MESSAGE: /^#### (.+?)(?:\s*\[(FOR|AGAINST|ADVOCATE|DEFENDER|QUESTIONER|RESPONDENT|PANELIST|IDEATOR|EVALUATOR)\])?(?:\s*\((Critique|Final Position|Kritik|Slutposition|Kritik|Endposition|Critique|Position finale|Crítica|Posición final|Critica|Posizione finale)\))?$/,

  // Synthesis sub-headers - terminology.synthesis.* (all 7 methods × 6 languages)
  // EN: Synthesis, Adjudication, Ruling, Reflection, Aggregated Estimate, Final Ideas, Recommendation
  // SV: Syntes, Avgörande, Beslut, Reflektion, Aggregerad uppskattning, Slutgiltiga idéer, Rekommendation
  // DE: Synthese, Entscheidung, Urteil, Reflexion, Aggregierte Schätzung, Endgültige Ideen, Empfehlung
  // FR: Synthèse, Jugement, Décision, Réflexion, Estimation Agrégée, Idées Finales, Recommandation
  // ES: Síntesis, Adjudicación, Fallo, Reflexión, Estimación Agregada, Ideas Finales, Recomendación
  // IT: Sintesi, Giudizio, Sentenza, Riflessione, Stima Aggregata, Idee Finali, Raccomandazione
  SYNTHESIS_HEADER: /^### (Synthesis|Adjudication|Ruling|Reflection|Aggregated Estimate|Final Ideas|Recommendation|Syntes|Avgörande|Beslut|Reflektion|Aggregerad uppskattning|Slutgiltiga idéer|Rekommendation|Synthese|Entscheidung|Urteil|Reflexion|Aggregierte Schätzung|Endgültige Ideen|Empfehlung|Synthèse|Jugement|Décision|Réflexion|Estimation Agrégée|Idées Finales|Recommandation|Síntesis|Adjudicación|Fallo|Reflexión|Estimación Agregada|Ideas Finales|Recomendación|Sintesi|Giudizio|Sentenza|Riflessione|Stima Aggregata|Idee Finali|Raccomandazione)$/,

  // Differences sub-headers - terminology.differences.* (all 7 methods × 6 languages)
  // EN: Notable Differences, Key Contentions, Unresolved Questions, Open Questions, Outlier Perspectives, Alternative Directions, Key Tradeoffs
  // SV: Anmärkningsvärda skillnader, Huvudsakliga stridsfrågor, Olösta frågor, Öppna frågor, Avvikande perspektiv, Alternativa riktningar, Huvudsakliga avvägningar
  // DE: Bemerkenswerte Unterschiede, Hauptstreitpunkte, Ungelöste Fragen, Offene Fragen, Abweichende Perspektiven, Alternative Richtungen, Wichtige Kompromisse
  // FR: Différences Notables, Points de Contestation, Questions Non Résolues, Questions Ouvertes, Perspectives Divergentes, Directions Alternatives, Compromis Clés
  // ES: Diferencias Notables, Puntos de Controversia, Preguntas Sin Resolver, Preguntas Abiertas, Perspectivas Atípicas, Direcciones Alternativas, Compensaciones Clave
  // IT: Differenze Notevoli, Punti di Contesa, Domande Irrisolte, Domande Aperte, Prospettive Divergenti, Direzioni Alternative, Compromessi Chiave
  DIFFERENCES_HEADER: /^### (Notable Differences|Key Contentions|Unresolved Questions|Open Questions|Outlier Perspectives|Alternative Directions|Key Tradeoffs|Anmärkningsvärda skillnader|Huvudsakliga stridsfrågor|Olösta frågor|Öppna frågor|Avvikande perspektiv|Alternativa riktningar|Huvudsakliga avvägningar|Bemerkenswerte Unterschiede|Hauptstreitpunkte|Ungelöste Fragen|Offene Fragen|Abweichende Perspektiven|Alternative Richtungen|Wichtige Kompromisse|Différences Notables|Points de Contestation|Questions Non Résolues|Questions Ouvertes|Perspectives Divergentes|Directions Alternatives|Compromis Clés|Diferencias Notables|Puntos de Controversia|Preguntas Sin Resolver|Preguntas Abiertas|Perspectivas Atípicas|Direcciones Alternativas|Compensaciones Clave|Differenze Notevoli|Punti di Contesa|Domande Irrisolte|Domande Aperte|Prospettive Divergenti|Direzioni Alternative|Compromessi Chiave)$/,

  // Metadata patterns in result section - terminology.consensus.* (all methods × 6 languages)
  // EN: Consensus, Decision, Verdict, Aporia Reached, Convergence, Ideas Selected, Agreement
  // SV: Konsensus, Beslut, Utslag, Apori nådd, Konvergens, Idéer valda, Överenskommelse
  // DE: Konsens, Entscheidung, Verdikt, Aporie erreicht, Konvergenz, Ideen ausgewählt, Einigung
  // FR: Consensus, Décision, Verdict, Aporie Atteinte, Convergence, Idées Sélectionnées, Accord
  // ES: Consenso, Decisión, Veredicto, Aporía Alcanzada, Convergencia, Ideas Seleccionadas, Acuerdo
  // IT: Consenso, Decisione, Verdetto, Aporia Raggiunta, Convergenza, Idee Selezionate, Accordo
  CONSENSUS_LINE: /^\*\*(Consensus|Decision|Verdict|Aporia Reached|Convergence|Ideas Selected|Agreement|Konsensus|Beslut|Utslag|Apori nådd|Konvergens|Idéer valda|Överenskommelse|Konsens|Entscheidung|Verdikt|Aporie erreicht|Konvergenz|Ideen ausgewählt|Einigung|Consensus|Décision|Verdict|Aporie Atteinte|Convergence|Idées Sélectionnées|Accord|Consenso|Decisión|Veredicto|Aporía Alcanzada|Convergencia|Ideas Seleccionadas|Acuerdo|Consenso|Decisione|Verdetto|Aporia Raggiunta|Convergenza|Idee Selezionate|Accordo):\*\*\s*(.+)$/,
  // Pattern must match EXACTLY what i18n translations produce (see terminology.by.* in translations/)
  SYNTHESIZER_LINE: /^\*\*(Synthesized by|Adjudicated by|Ruled by|Reflected by|Aggregated by|Compiled by|Analyzed by|Syntetiserad av|Avgjord av|Beslutad av|Reflekterad av|Aggregerad av|Sammanställd av|Analyserad av|Synthetisiert von|Entschieden von|Geurteilt von|Reflektiert von|Aggregiert von|Zusammengestellt von|Analysiert von|Synthétisé par|Jugé par|Décidé par|Réfléchi par|Agrégé par|Compilé par|Analysé par|Sintetizado por|Adjudicado por|Fallado por|Reflejado por|Agregado por|Compilado por|Analizado por|Sintetizzato da|Giudicato da|Sentenziato da|Riflesso da|Aggregato da|Compilato da|Analizzato da):\*\*\s*(.+)$/,

  // Critique section markers (6 languages)
  AGREEMENTS: /^\*\*(Agreements|Överenskommelser|Übereinstimmungen|Accords|Acuerdos|Accordi):\*\*$/,
  DISAGREEMENTS: /^\*\*(Disagreements|Meningsskiljaktigheter|Meinungsverschiedenheiten|Désaccords|Desacuerdos|Disaccordi):\*\*$/,
  MISSING: /^\*\*(Missing|Saknas|Fehlend|Manquant|Faltante|Mancante):\*\*$/,

  // Position confidence (6 languages)
  CONFIDENCE: /^\*\*(Confidence|Konfidens|Konfidenz|Confiance|Confianza|Fiducia):\*\*\s*(.+)$/,

  // End markers (6 languages) - optionally matches [Quorum] link format
  SEPARATOR: /^---$/,
  FOOTER: /^\*(Exported from|Exporterad från|Exportiert von|Exporté depuis|Exportado desde|Esportato da)(?: \[Quorum\])?/,
};

/** Role types across all methods */
export type ParsedRole = "FOR" | "AGAINST" | "ADVOCATE" | "DEFENDER" | "QUESTIONER" | "RESPONDENT" | "PANELIST" | "IDEATOR" | "EVALUATOR" | null;

/** Document metadata */
export interface ParsedMetadata {
  date: string;
  method: string;
  models: string[];
}

/** A parsed message in a phase */
export interface ParsedMessage {
  source: string;
  type: "answer" | "critique" | "position";
  role: ParsedRole;
  content: string;
  // Critique fields
  agreements?: string;
  disagreements?: string;
  missing?: string;
  // Position fields
  confidence?: string;
}

/** A phase containing messages */
export interface ParsedPhase {
  number: number;
  title: string;
  messages: ParsedMessage[];
}

/** Synthesis/result section */
export interface ParsedSynthesis {
  resultLabel: string;
  consensus: string;
  consensusLabel: string;
  synthesizer: string;
  byLabel: string;
  synthesisLabel: string;
  synthesis: string;
  differencesLabel: string;
  differences: string;
  method: string;
}

/** Complete parsed document structure */
export interface ParsedDiscussionDocument {
  metadata: ParsedMetadata;
  question: string;
  phases: ParsedPhase[];
  synthesis: ParsedSynthesis | null;
}

/**
 * Parser for Quorum markdown discussion logs.
 * Encapsulates parsing state and provides clean methods for each section.
 */
export class MarkdownParser {
  private lines: string[];
  private index: number;

  constructor(markdown: string) {
    this.lines = markdown.split("\n");
    this.index = 0;
  }

  /**
   * Parse the complete markdown log into a structured document.
   */
  parse(): ParsedDiscussionDocument {
    const metadata = this.parseMetadata();
    const question = this.parseQuestion();
    const phases = this.parsePhases();
    const synthesis = this.parseSynthesis(metadata.method);

    return { metadata, question, phases, synthesis };
  }

  // === State helpers ===

  private peek(): string {
    return this.lines[this.index]?.trim() ?? "";
  }

  private consume(): string {
    return this.lines[this.index++] ?? "";
  }

  private skipEmpty(): void {
    while (this.index < this.lines.length && !this.lines[this.index]?.trim()) {
      this.index++;
    }
  }

  private hasMore(): boolean {
    return this.index < this.lines.length;
  }

  // === Section parsers ===

  private parseMetadata(): ParsedMetadata {
    const metadata: ParsedMetadata = { date: "", method: "", models: [] };

    // Multi-language metadata patterns (en, sv, de, fr, es, it)
    const DATE_PATTERN = /^\*\*(Date|Datum|Datum|Date|Fecha|Data):\*\*\s*(.+)$/;
    const METHOD_PATTERN = /^\*\*(Method|Metod|Methode|Méthode|Método|Metodo):\*\*\s*(.+)$/;
    const MODELS_PATTERN = /^\*\*(Models|Modeller|Modelle|Modèles|Modelos|Modelli):\*\*\s*(.+)$/;

    while (this.hasMore()) {
      const line = this.peek();

      const dateMatch = line.match(DATE_PATTERN);
      if (dateMatch) {
        metadata.date = dateMatch[2].trim();
        this.consume();
        continue;
      }

      const methodMatch = line.match(METHOD_PATTERN);
      if (methodMatch) {
        metadata.method = methodMatch[2].trim();
        this.consume();
        continue;
      }

      const modelsMatch = line.match(MODELS_PATTERN);
      if (modelsMatch) {
        metadata.models = modelsMatch[2].trim().split(",").map(m => m.trim());
        this.consume();
        continue;
      }

      if (STRUCTURAL_PATTERNS.SEPARATOR.test(line) || STRUCTURAL_PATTERNS.QUESTION.test(line)) {
        break;
      }

      this.consume();
    }

    return metadata;
  }

  private parseQuestion(): string {
    // Skip to Question section
    while (this.hasMore() && !STRUCTURAL_PATTERNS.QUESTION.test(this.peek())) {
      this.consume();
    }
    this.consume(); // Skip "## Question"
    this.skipEmpty();

    // Parse question (blockquote)
    let question = "";
    if (this.peek().startsWith(">")) {
      question = this.consume().replace(/^>\s*/, "");
      while (this.hasMore() && this.peek().startsWith(">")) {
        question += " " + this.consume().replace(/^>\s*/, "");
      }
    }

    return question;
  }

  private parsePhases(): ParsedPhase[] {
    // Skip to Discussion section
    while (this.hasMore() && !STRUCTURAL_PATTERNS.DISCUSSION.test(this.peek())) {
      this.consume();
    }
    this.consume(); // Skip "## Discussion"
    this.skipEmpty();

    const phases: ParsedPhase[] = [];

    while (this.hasMore()) {
      const line = this.peek();

      // Check for end of discussion
      if (STRUCTURAL_PATTERNS.RESULT.test(line)) break;
      if (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead()) break;

      // Parse phase header
      const phaseMatch = line.match(STRUCTURAL_PATTERNS.PHASE);
      if (phaseMatch) {
        const phase = this.parsePhase(phaseMatch);
        phases.push(phase);
        continue;
      }

      this.consume();
    }

    return phases;
  }

  private parsePhase(phaseMatch: RegExpMatchArray): ParsedPhase {
    const phaseLine = this.peek();
    this.consume();
    this.skipEmpty();

    const phase: ParsedPhase = {
      number: parseInt(phaseMatch[2]), // Group 2 is the number (group 1 is the phase word)
      title: phaseLine.replace(/^###\s*/, ""),
      messages: [],
    };

    while (this.hasMore()) {
      const msgLine = this.peek();

      // Check for end of phase
      if (STRUCTURAL_PATTERNS.PHASE.test(msgLine) ||
          STRUCTURAL_PATTERNS.RESULT.test(msgLine) ||
          (STRUCTURAL_PATTERNS.SEPARATOR.test(msgLine) && this.looksLikeResultAhead())) {
        break;
      }

      // Parse message header
      const msgMatch = msgLine.match(STRUCTURAL_PATTERNS.MESSAGE);
      if (msgMatch) {
        const msg = this.parseMessage(msgMatch);
        if (msg) phase.messages.push(msg);
        continue;
      }

      this.consume();
    }

    return phase;
  }

  private parseMessage(msgMatch: RegExpMatchArray): ParsedMessage | null {
    this.consume();
    this.skipEmpty();

    const source = msgMatch[1].trim();
    const role = (msgMatch[2] as ParsedRole) || null;
    const msgType = msgMatch[3]; // "Critique", "Final Position", or translated equivalents

    // Multi-language matching for message types
    const CRITIQUE_LABELS = ["Critique", "Kritik", "Kritik", "Critique", "Crítica", "Critica"];
    const POSITION_LABELS = ["Final Position", "Slutposition", "Endposition", "Position finale", "Posición final", "Posizione finale"];

    if (msgType && CRITIQUE_LABELS.includes(msgType)) {
      return this.parseCritiqueMessage(source, role);
    } else if (msgType && POSITION_LABELS.includes(msgType)) {
      return this.parsePositionMessage(source, role);
    } else {
      return this.parseAnswerMessage(source, role);
    }
  }

  private parseCritiqueMessage(source: string, role: ParsedRole): ParsedMessage {
    const msg: ParsedMessage = {
      source,
      type: "critique",
      role,
      content: "",
      agreements: "",
      disagreements: "",
      missing: "",
    };

    while (this.hasMore() && !this.isMessageOrPhaseEnd()) {
      const critLine = this.peek();
      if (STRUCTURAL_PATTERNS.AGREEMENTS.test(critLine)) {
        this.consume();
        this.skipEmpty();
        msg.agreements = this.collectUntilNextSection();
      } else if (STRUCTURAL_PATTERNS.DISAGREEMENTS.test(critLine)) {
        this.consume();
        this.skipEmpty();
        msg.disagreements = this.collectUntilNextSection();
      } else if (STRUCTURAL_PATTERNS.MISSING.test(critLine)) {
        this.consume();
        this.skipEmpty();
        msg.missing = this.collectUntilNextSection();
      } else {
        this.consume();
      }
    }

    return msg;
  }

  private parsePositionMessage(source: string, role: ParsedRole): ParsedMessage {
    const msg: ParsedMessage = {
      source,
      type: "position",
      role,
      content: "",
      confidence: "",
    };

    const contentLines: string[] = [];
    while (this.hasMore() && !this.isMessageOrPhaseEnd()) {
      const posLine = this.peek();
      const confMatch = posLine.match(STRUCTURAL_PATTERNS.CONFIDENCE);
      if (confMatch) {
        msg.confidence = confMatch[1].trim();
        this.consume();
      } else {
        contentLines.push(this.consume());
      }
    }
    msg.content = contentLines.join("\n").trim();

    return msg;
  }

  private parseAnswerMessage(source: string, role: ParsedRole): ParsedMessage {
    return {
      source,
      type: "answer",
      role,
      content: this.collectMessageContent(),
    };
  }

  private parseSynthesis(method: string): ParsedSynthesis | null {
    // Skip to result section
    while (this.hasMore() && !STRUCTURAL_PATTERNS.RESULT.test(this.peek())) {
      this.consume();
    }

    if (!this.hasMore() || !STRUCTURAL_PATTERNS.RESULT.test(this.peek())) {
      return null;
    }

    const resultMatch = this.peek().match(STRUCTURAL_PATTERNS.RESULT);
    const resultLabel = resultMatch ? resultMatch[1] : "Result";
    this.consume();
    this.skipEmpty();

    const synthesis: ParsedSynthesis = {
      resultLabel,
      consensus: "",
      consensusLabel: "",
      synthesizer: "",
      byLabel: "",
      synthesisLabel: "",
      synthesis: "",
      differencesLabel: "",
      differences: "",
      method: method.toLowerCase(),
    };

    while (this.hasMore()) {
      const line = this.peek();

      if (STRUCTURAL_PATTERNS.SEPARATOR.test(line) || STRUCTURAL_PATTERNS.FOOTER.test(line)) {
        break;
      }

      const consMatch = line.match(STRUCTURAL_PATTERNS.CONSENSUS_LINE);
      if (consMatch) {
        synthesis.consensusLabel = consMatch[1];
        synthesis.consensus = consMatch[2].trim();
        this.consume();
        continue;
      }

      const synthMatch = line.match(STRUCTURAL_PATTERNS.SYNTHESIZER_LINE);
      if (synthMatch) {
        synthesis.byLabel = synthMatch[1];
        synthesis.synthesizer = synthMatch[2].trim();
        this.consume();
        continue;
      }

      const synthHeaderMatch = line.match(STRUCTURAL_PATTERNS.SYNTHESIS_HEADER);
      if (synthHeaderMatch) {
        synthesis.synthesisLabel = synthHeaderMatch[1];
        this.consume();
        this.skipEmpty();
        const synthLines: string[] = [];
        while (this.hasMore() &&
               !STRUCTURAL_PATTERNS.DIFFERENCES_HEADER.test(this.peek()) &&
               !STRUCTURAL_PATTERNS.SEPARATOR.test(this.peek()) &&
               !STRUCTURAL_PATTERNS.FOOTER.test(this.peek())) {
          synthLines.push(this.consume());
        }
        synthesis.synthesis = synthLines.join("\n").trim();
        continue;
      }

      const diffHeaderMatch = line.match(STRUCTURAL_PATTERNS.DIFFERENCES_HEADER);
      if (diffHeaderMatch) {
        synthesis.differencesLabel = diffHeaderMatch[1];
        this.consume();
        this.skipEmpty();
        const diffLines: string[] = [];
        while (this.hasMore() &&
               !STRUCTURAL_PATTERNS.SEPARATOR.test(this.peek()) &&
               !STRUCTURAL_PATTERNS.FOOTER.test(this.peek())) {
          diffLines.push(this.consume());
        }
        synthesis.differences = diffLines.join("\n").trim();
        continue;
      }

      this.consume();
    }

    return synthesis;
  }

  // === Helper methods ===

  private isMessageOrPhaseEnd(): boolean {
    const line = this.peek();
    return STRUCTURAL_PATTERNS.MESSAGE.test(line) ||
           STRUCTURAL_PATTERNS.PHASE.test(line) ||
           STRUCTURAL_PATTERNS.RESULT.test(line) ||
           (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead());
  }

  private looksLikeResultAhead(): boolean {
    let lookAhead = this.index + 1;
    while (lookAhead < this.lines.length && !this.lines[lookAhead]?.trim()) {
      lookAhead++;
    }
    return lookAhead < this.lines.length &&
           STRUCTURAL_PATTERNS.RESULT.test(this.lines[lookAhead].trim());
  }

  private collectUntilNextSection(): string {
    const contentLines: string[] = [];
    while (this.hasMore() &&
           !STRUCTURAL_PATTERNS.AGREEMENTS.test(this.peek()) &&
           !STRUCTURAL_PATTERNS.DISAGREEMENTS.test(this.peek()) &&
           !STRUCTURAL_PATTERNS.MISSING.test(this.peek()) &&
           !this.isMessageOrPhaseEnd()) {
      contentLines.push(this.consume());
    }
    return contentLines.join("\n").trim();
  }

  private collectMessageContent(): string {
    const contentLines: string[] = [];
    while (this.hasMore()) {
      const line = this.peek();

      if (STRUCTURAL_PATTERNS.MESSAGE.test(line) ||
          STRUCTURAL_PATTERNS.PHASE.test(line) ||
          STRUCTURAL_PATTERNS.RESULT.test(line) ||
          (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead())) {
        break;
      }

      contentLines.push(this.consume());
    }
    return contentLines.join("\n").trim();
  }
}

/**
 * Parse a markdown discussion log into a structured document.
 * Convenience function that creates a parser and runs it.
 */
export function parseMarkdownLog(markdown: string): ParsedDiscussionDocument {
  const parser = new MarkdownParser(markdown);
  return parser.parse();
}
