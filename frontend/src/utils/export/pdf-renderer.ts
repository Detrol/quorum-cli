/**
 * PDF rendering for Quorum discussion exports.
 * Encapsulates PDF generation with clean component methods.
 */

import type { ParsedDiscussionDocument, ParsedPhase, ParsedMessage, ParsedSynthesis } from "./parser.js";
import { getMethodTerminology } from "./method-terminology.js";
import { t } from "../../i18n/index.js";
import { translateRole, translateConsensus, translateConfidence } from "../export.js";

// PDF page configuration
const PDF_CONFIG = {
  pageWidth: 595,
  contentWidth: 495, // 595 - 100 (margins)
  leftMargin: 50,
  pageBreakThreshold: 700,
  messagePageBreak: 680,
  colors: {
    title: "#1e3a8a",
    header: "#1e40af",
    metaBox: "#f3f4f6",
    metaText: "#374151",
    questionBg: "#eff6ff",
    questionAccent: "#3b82f6",
    questionText: "#1e3a8a",
    bodyText: "#374151",
    muted: "#6b7280",
    footer: "#9ca3af",
    footerLine: "#d1d5db",
    critique: "#8b5cf6",
    position: "#0891b2",
    agreements: "#16a34a",
    disagreements: "#dc2626",
    missing: "#ca8a04",
    differences: "#b45309",
    // Role colors
    for: "#22c55e",
    against: "#ef4444",
    questioner: "#06b6d4",
    respondent: "#eab308",
    panelist: "#a855f7",
    ideator: "#06b6d4",
    evaluator: "#3b82f6",
    neutral: "#6b7280",
  },
};

/**
 * Get role-specific color for message headers.
 */
function getRoleColor(role: string | null): string {
  const { colors } = PDF_CONFIG;
  switch (role) {
    case "FOR":
    case "DEFENDER":
      return colors.for;
    case "AGAINST":
    case "ADVOCATE":
      return colors.against;
    case "QUESTIONER":
      return colors.questioner;
    case "RESPONDENT":
      return colors.respondent;
    case "PANELIST":
      return colors.panelist;
    case "IDEATOR":
      return colors.ideator;
    case "EVALUATOR":
      return colors.evaluator;
    default:
      return colors.neutral;
  }
}

/**
 * PDF Renderer for Quorum discussion documents.
 * Breaks down rendering into logical component methods.
 */
export class PDFRenderer {
  private doc: PDFKit.PDFDocument;
  private formatModelName: (id: string) => string;
  private renderMarkdown: (doc: PDFKit.PDFDocument, text: string, width?: number) => void;

  constructor(
    doc: PDFKit.PDFDocument,
    formatModelName: (id: string) => string,
    renderMarkdown: (doc: PDFKit.PDFDocument, text: string, width?: number) => void
  ) {
    this.doc = doc;
    this.formatModelName = formatModelName;
    this.renderMarkdown = renderMarkdown;
  }

  /**
   * Render a complete discussion document to PDF.
   */
  render(document: ParsedDiscussionDocument): void {
    const { metadata, question, phases, synthesis } = document;

    this.renderHeader(metadata);
    this.renderQuestion(question);
    this.renderDiscussionHeader();
    this.renderPhases(phases);
    if (synthesis) {
      this.renderSynthesis(synthesis);
    }
    this.renderFooter();
  }

  /**
   * Render document header with title and metadata box.
   */
  private renderHeader(metadata: { date: string; method: string; models: string[] }): void {
    const { leftMargin, contentWidth, colors } = PDF_CONFIG;

    // Title
    this.doc.fontSize(22).font("DejaVu-Bold").fillColor(colors.title)
      .text(t("export.doc.title"), { align: "center" });
    this.doc.fillColor("black").moveDown(0.5);

    // Metadata box
    const formattedModels = metadata.models
      .map(m => this.formatModelName(m.trim()))
      .join(", ");

    const metaY = this.doc.y;
    this.doc.rect(leftMargin, metaY, contentWidth, 50).fill(colors.metaBox);
    this.doc.fillColor(colors.metaText).fontSize(10).font("DejaVu");
    this.doc.text(`${t("export.doc.dateLabel")} ${metadata.date}`, leftMargin + 10, metaY + 10);
    this.doc.text(`${t("export.doc.methodLabel")} ${metadata.method}`, leftMargin + 10, metaY + 22);
    this.doc.text(`${t("export.doc.modelsLabel")} ${formattedModels}`, leftMargin + 10, metaY + 34);
    this.doc.y = metaY + 60;
  }

  /**
   * Render the question section with styled blockquote.
   */
  private renderQuestion(question: string): void {
    const { leftMargin, contentWidth, colors } = PDF_CONFIG;

    this.doc.moveDown(0.5);
    this.doc.fontSize(14).font("DejaVu-Bold").fillColor(colors.header).text(t("export.doc.questionHeader"));
    this.doc.fillColor("black").moveDown(0.3);

    const questionY = this.doc.y;
    this.doc.fontSize(11).font("DejaVu");
    const questionHeight = this.doc.heightOfString(question, { width: contentWidth - 24 }) + 16;

    this.doc.rect(leftMargin, questionY, contentWidth, questionHeight).fill(colors.questionBg);
    this.doc.rect(leftMargin, questionY, 4, questionHeight).fill(colors.questionAccent);
    this.doc.fillColor(colors.questionText);
    this.doc.text(question, leftMargin + 14, questionY + 8, { width: contentWidth - 24 });
    this.doc.y = questionY + questionHeight + 10;
  }

  /**
   * Render the "Discussion" section header.
   */
  private renderDiscussionHeader(): void {
    this.doc.fontSize(16).font("DejaVu-Bold").fillColor(PDF_CONFIG.colors.header).text(t("export.doc.discussionHeader"));
    this.doc.fillColor("black").moveDown(0.5);
  }

  /**
   * Render all phases with their messages.
   */
  private renderPhases(phases: ParsedPhase[]): void {
    for (const phase of phases) {
      if (phase.messages.length === 0) continue;
      this.renderPhase(phase);
    }
  }

  /**
   * Render a single phase with its messages.
   */
  private renderPhase(phase: ParsedPhase): void {
    const { leftMargin, contentWidth, pageBreakThreshold, colors } = PDF_CONFIG;

    if (this.doc.y > pageBreakThreshold) this.doc.addPage();
    this.doc.moveDown(0.8);

    // Phase banner
    this.doc.fontSize(12).font("DejaVu-Bold");
    const textHeight = this.doc.heightOfString(phase.title, { width: contentWidth - 30 });
    const bannerHeight = Math.max(30, textHeight + 16);

    const phaseY = this.doc.y;
    this.doc.rect(leftMargin, phaseY, contentWidth, bannerHeight).fill(colors.header);
    this.doc.fillColor("white");
    this.doc.text(phase.title, leftMargin + 15, phaseY + 8, { width: contentWidth - 30 });
    this.doc.y = phaseY + bannerHeight + 10;

    // Render messages
    for (const msg of phase.messages) {
      this.renderMessage(msg);
    }
  }

  /**
   * Render a single message (answer, critique, or position).
   */
  private renderMessage(msg: ParsedMessage): void {
    const { messagePageBreak } = PDF_CONFIG;
    if (this.doc.y > messagePageBreak) this.doc.addPage();

    if (msg.type === "critique") {
      this.renderCritiqueMessage(msg);
    } else if (msg.type === "position") {
      this.renderPositionMessage(msg);
    } else {
      this.renderAnswerMessage(msg);
    }
  }

  /**
   * Render a critique message with agreements/disagreements/missing sections.
   */
  private renderCritiqueMessage(msg: ParsedMessage): void {
    const { leftMargin, contentWidth, colors } = PDF_CONFIG;
    const source = this.formatModelName(msg.source);

    const msgY = this.doc.y;
    this.doc.rect(leftMargin, msgY, contentWidth, 22).fill(colors.critique);
    this.doc.fillColor("white").fontSize(10).font("DejaVu-Bold");
    this.doc.text(`${source} (${t("export.doc.critiqueLabel")})`, leftMargin + 10, msgY + 6);
    this.doc.y = msgY + 30;

    if (msg.agreements) {
      this.doc.font("DejaVu-Bold").fillColor(colors.agreements).text(`${t("export.doc.agreementsLabel")}`, leftMargin);
      this.doc.font("DejaVu").fillColor(colors.bodyText).fontSize(10);
      this.doc.x = leftMargin;
      this.renderMarkdown(this.doc, msg.agreements, contentWidth);
      this.doc.moveDown(0.3);
    }
    if (msg.disagreements) {
      this.doc.font("DejaVu-Bold").fillColor(colors.disagreements).text(`${t("export.doc.disagreementsLabel")}`, leftMargin);
      this.doc.font("DejaVu").fillColor(colors.bodyText).fontSize(10);
      this.doc.x = leftMargin;
      this.renderMarkdown(this.doc, msg.disagreements, contentWidth);
      this.doc.moveDown(0.3);
    }
    if (msg.missing) {
      this.doc.font("DejaVu-Bold").fillColor(colors.missing).text(`${t("export.doc.missingLabel")}`, leftMargin);
      this.doc.font("DejaVu").fillColor(colors.bodyText).fontSize(10);
      this.doc.x = leftMargin;
      this.renderMarkdown(this.doc, msg.missing, contentWidth);
    }
    this.doc.moveDown(1);
  }

  /**
   * Render a final position message with confidence indicator.
   */
  private renderPositionMessage(msg: ParsedMessage): void {
    const { leftMargin, contentWidth, colors } = PDF_CONFIG;
    const source = this.formatModelName(msg.source);

    const msgY = this.doc.y;
    this.doc.rect(leftMargin, msgY, contentWidth, 22).fill(colors.position);
    this.doc.fillColor("white").fontSize(10).font("DejaVu-Bold");
    this.doc.text(`${source} (${t("export.doc.finalPositionLabel")})`, leftMargin + 10, msgY + 6);

    const confColor = msg.confidence === "HIGH" ? colors.agreements
      : msg.confidence === "MEDIUM" ? colors.missing
      : colors.disagreements;

    this.doc.y = msgY + 28;
    this.doc.fillColor(confColor).fontSize(10).font("DejaVu-Bold");
    this.doc.text(`${t("export.doc.confidenceLabel")} ${translateConfidence(msg.confidence || "")}`, leftMargin);

    this.doc.fillColor(colors.bodyText).font("DejaVu").fontSize(10);
    this.doc.moveDown(0.3);
    this.doc.x = leftMargin;
    this.renderMarkdown(this.doc, msg.content, contentWidth);
    this.doc.moveDown(1);
  }

  /**
   * Render a regular answer/chat message.
   */
  private renderAnswerMessage(msg: ParsedMessage): void {
    const { leftMargin, contentWidth, colors } = PDF_CONFIG;
    const source = this.formatModelName(msg.source);
    const roleColor = getRoleColor(msg.role);

    const msgY = this.doc.y;
    this.doc.rect(leftMargin, msgY, contentWidth, 22).fill(roleColor);
    const roleTag = msg.role ? ` [${translateRole(msg.role)}]` : "";
    this.doc.fillColor("white").fontSize(10).font("DejaVu-Bold");
    this.doc.text(`${source}${roleTag}`, leftMargin + 10, msgY + 6, { width: contentWidth - 20 });

    this.doc.fillColor(colors.bodyText).font("DejaVu").fontSize(10);
    this.doc.y = msgY + 30;
    this.doc.x = leftMargin;
    this.renderMarkdown(this.doc, msg.content, contentWidth);
    this.doc.moveDown(1);
  }

  /**
   * Render the synthesis/result section.
   */
  private renderSynthesis(synthesis: ParsedSynthesis): void {
    const { leftMargin, contentWidth, colors } = PDF_CONFIG;

    if (this.doc.y > 600) this.doc.addPage();
    this.doc.moveDown(1);

    // Get method-specific terminology and banner color
    const term = getMethodTerminology(synthesis.method as any);
    const bannerColor = term?.bannerColor || "#065f46";

    // Result banner
    const resultY = this.doc.y;
    this.doc.rect(leftMargin, resultY, contentWidth, 35).fill(bannerColor);
    this.doc.fillColor("white").fontSize(14).font("DejaVu-Bold");
    this.doc.text(synthesis.resultLabel, leftMargin + 15, resultY + 10);
    this.doc.y = resultY + 45;

    // Consensus (skip for Advocate, and only if consensusLabel was parsed)
    const method = synthesis.method.toLowerCase();
    if (method !== "advocate" && synthesis.consensus && synthesis.consensusLabel) {
      const consensusColor = this.getConsensusColor(method, synthesis.consensus);
      this.doc.fillColor(consensusColor).fontSize(12).font("DejaVu-Bold");
      this.doc.text(`${synthesis.consensusLabel}: ${translateConsensus(synthesis.consensus)}`, leftMargin);
    }

    // Synthesizer attribution (only if byLabel was parsed - prevents stray ":" if pattern mismatch)
    if (synthesis.byLabel && synthesis.synthesizer) {
      this.doc.fillColor(colors.muted).fontSize(10).font("DejaVu");
      this.doc.text(`${synthesis.byLabel}: ${this.formatModelName(synthesis.synthesizer)}`, leftMargin);
    }
    this.doc.moveDown(0.5);

    // Synthesis content
    if (synthesis.synthesisLabel && synthesis.synthesis) {
      this.doc.fillColor(colors.header).fontSize(12).font("DejaVu-Bold").text(synthesis.synthesisLabel);
      this.doc.fillColor(colors.bodyText).fontSize(10).font("DejaVu").moveDown(0.3);
      this.doc.x = leftMargin;
      this.renderMarkdown(this.doc, synthesis.synthesis, contentWidth);
    }

    // Differences (skip placeholder for Advocate)
    if (synthesis.differences && synthesis.differences !== "See verdict above for unresolved questions.") {
      this.doc.moveDown(0.8);
      this.doc.fillColor(colors.differences).fontSize(12).font("DejaVu-Bold").text(synthesis.differencesLabel);
      this.doc.fillColor(colors.bodyText).fontSize(10).font("DejaVu").moveDown(0.3);
      this.doc.x = leftMargin;
      this.renderMarkdown(this.doc, synthesis.differences, contentWidth);
    }
  }

  /**
   * Get consensus color based on method and value.
   */
  private getConsensusColor(method: string, consensus: string): string {
    const { colors } = PDF_CONFIG;
    if (method === "oxford") {
      return consensus === "FOR" ? colors.agreements
        : consensus === "AGAINST" ? colors.disagreements
        : colors.missing;
    }
    if (method === "brainstorm") {
      return colors.position;
    }
    if (method === "tradeoff") {
      return consensus === "YES" ? colors.agreements : colors.missing;
    }
    // Standard/Socratic/Delphi
    return consensus === "YES" ? colors.agreements
      : consensus === "PARTIAL" ? colors.missing
      : colors.disagreements;
  }

  /**
   * Render the document footer.
   */
  private renderFooter(): void {
    const { leftMargin, contentWidth, colors } = PDF_CONFIG;

    this.doc.moveDown(2);
    this.doc.moveTo(leftMargin, this.doc.y).lineTo(leftMargin + contentWidth, this.doc.y).stroke(colors.footerLine);
    this.doc.moveDown(0.5);
    this.doc.fontSize(8).font("DejaVu").fillColor(colors.footer);
    this.doc.text(t("export.doc.footer"), { align: "center" });
  }
}

/** PDF configuration export for external use */
export { PDF_CONFIG };
