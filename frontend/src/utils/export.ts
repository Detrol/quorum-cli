/**
 * Export discussion to various formats.
 */

import * as fs from "fs";
import * as fsPromises from "fs/promises";
import * as path from "path";
import * as os from "os";
import { fileURLToPath } from "url";
import PDFDocument from "pdfkit";
import type { DiscussionMessage, DiscussionMethod } from "../store/index.js";
import { t, type TranslationKey } from "../i18n/index.js";
import {
  type ConfidenceLevel,
  type RoleValue,
  type StandardConsensus,
  CONFIDENCE_KEYS,
  ROLE_KEYS,
  CONSENSUS_KEYS,
  isConfidenceLevel,
  isStandardConsensus,
  isRoleValue,
} from "../types/protocol-values.js";
import { getMethodTerminology, getResultLabelUppercase } from "./export/method-terminology.js";
import { parseMarkdownLog } from "./export/parser.js";
import { PDFRenderer } from "./export/pdf-renderer.js";
import { highlightCode, CODE_BACKGROUND, type HighlightToken } from "./export/syntax-highlight.js";
import {
  parseMarkdown,
  tokensToPlainText,
  SUBSCRIPTS,
  SUPERSCRIPTS,
  LATEX_COMMANDS,
  type InlineToken,
} from "./markdown.js";
import { formatModelName } from "./modelName.js";

// Get paths to DejaVu Sans fonts (supports Unicode subscripts/superscripts)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FONT_DIR = path.join(__dirname, "..", "..", "assets", "fonts");
const DEJAVU_REGULAR = path.join(FONT_DIR, "DejaVuSans.ttf");
const DEJAVU_BOLD = path.join(FONT_DIR, "DejaVuSans-Bold.ttf");
const DEJAVU_OBLIQUE = path.join(FONT_DIR, "DejaVuSans-Oblique.ttf");
const DEJAVU_BOLD_OBLIQUE = path.join(FONT_DIR, "DejaVuSans-BoldOblique.ttf");

// Check font availability once at module load (avoids sync I/O in async functions)
const FONTS_AVAILABLE = fs.existsSync(DEJAVU_REGULAR);

/**
 * Register DejaVu fonts with a PDF document if available.
 */
function registerFonts(doc: PDFKit.PDFDocument): void {
  if (FONTS_AVAILABLE) {
    doc.registerFont("DejaVu", DEJAVU_REGULAR);
    doc.registerFont("DejaVu-Bold", DEJAVU_BOLD);
    doc.registerFont("DejaVu-Oblique", DEJAVU_OBLIQUE);
    doc.registerFont("DejaVu-BoldOblique", DEJAVU_BOLD_OBLIQUE);
  }
}

// Pre-compiled regex patterns for LaTeX commands (avoids repeated compilation)
// Uses LATEX_COMMANDS imported from markdown.ts
const LATEX_PATTERNS: Array<{ pattern: RegExp; replacement: string }> =
  Object.entries(LATEX_COMMANDS).map(([cmd, symbol]) => ({
    pattern: new RegExp(cmd.replace(/\\/g, "\\\\"), "g"),
    replacement: symbol,
  }));

/**
 * Clean text for PDF: convert LaTeX to Unicode and fix common issues.
 * Simple and robust - just make text readable.
 */
function cleanTextForPdf(text: string): string {
  let result = text;

  // Remove dollar signs around math (inline and display)
  result = result.replace(/\$\$([^$]+)\$\$/g, "$1");
  result = result.replace(/\$([^$]+)\$/g, "$1");
  result = result.replace(/\\\(([^)]+)\\\)/g, "$1");
  result = result.replace(/\\\[([^\]]+)\\\]/g, "$1");

  // Replace LaTeX commands with Unicode (using pre-compiled patterns)
  for (const { pattern, replacement } of LATEX_PATTERNS) {
    result = result.replace(pattern, replacement);
  }

  // Convert subscripts: _{...} or _x
  result = result.replace(/_\{([^}]+)\}/g, (_, content) => {
    return content.split("").map((c: string) => SUBSCRIPTS[c] || c).join("");
  });
  result = result.replace(/_([a-zA-Z0-9])/g, (_, c) => SUBSCRIPTS[c] || c);

  // Convert superscripts: ^{...} or ^x
  result = result.replace(/\^\{([^}]+)\}/g, (_, content) => {
    return content.split("").map((c: string) => SUPERSCRIPTS[c] || c).join("");
  });
  result = result.replace(/\^([a-zA-Z0-9])/g, (_, c) => SUPERSCRIPTS[c] || c);

  // Clean up remaining LaTeX artifacts
  result = result.replace(/\\text\{([^}]+)\}/g, "$1");
  result = result.replace(/\\mathrm\{([^}]+)\}/g, "$1");
  result = result.replace(/\\sim/g, "~");
  result = result.replace(/\\approx/g, "≈");
  result = result.replace(/\\gg/g, "≫");
  result = result.replace(/\\ll/g, "≪");
  result = result.replace(/[{}]/g, "");
  result = result.replace(/\\/g, "");

  return result;
}

/**
 * Render inline tokens to PDF, handling math tokens specially.
 * @param endLine - if true, ends the line after rendering (default: true)
 */
function renderTokensToPdf(
  doc: PDFKit.PDFDocument,
  tokens: InlineToken[],
  baseFontSize: number = 10,
  endLine: boolean = true
): void {
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    const isLast = i === tokens.length - 1;
    const continued = !(isLast && endLine);

    if (token.type === "math" && token.raw) {
      // Convert LaTeX to Unicode and render as plain text
      const unicodeText = cleanTextForPdf(token.raw);
      doc.text(unicodeText, { continued });
    } else if (token.type === "bold") {
      doc.font("DejaVu-Bold").text(token.content, { continued });
      doc.font("DejaVu");
    } else if (token.type === "italic") {
      doc.font("DejaVu-Oblique").text(token.content, { continued });
      doc.font("DejaVu");
    } else if (token.type === "code") {
      doc.font("Courier").text(token.content, { continued });
      doc.font("DejaVu");
    } else {
      doc.text(token.content, { continued });
    }
  }
}

/**
 * Check if tokens contain any math formatting.
 */
function containsMathTokens(tokens: InlineToken[]): boolean {
  return tokens.some(t => t.type === "math");
}

export type ExportFormat = "md" | "text" | "pdf";

interface ExportOptions {
  question: string;
  messages: DiscussionMessage[];
  method: DiscussionMethod;
  models: string[];
}

/**
 * Translate role label for export.
 * Uses centralized ROLE_KEYS mapping from protocol-values.ts.
 */
export function translateRole(role: string | RoleValue): string {
  if (isRoleValue(role)) {
    return t(ROLE_KEYS[role]);
  }
  return role; // Fallback for unknown values
}

/**
 * Translate consensus value for export.
 * Uses centralized CONSENSUS_KEYS mapping from protocol-values.ts.
 */
export function translateConsensus(value: string | StandardConsensus): string {
  if (isStandardConsensus(value)) {
    return t(CONSENSUS_KEYS[value]);
  }
  return value; // Fallback for method-specific values (e.g., Oxford's FOR/AGAINST)
}

/**
 * Translate confidence level for export.
 * Uses centralized CONFIDENCE_KEYS mapping from protocol-values.ts.
 */
export function translateConfidence(level: string | ConfidenceLevel | undefined): string {
  if (isConfidenceLevel(level)) {
    return t(CONFIDENCE_KEYS[level]);
  }
  return level || ""; // Fallback for unknown values
}

/**
 * Strip markdown formatting from text using the shared parser.
 */
function stripMarkdown(text: string): string {
  const lines = parseMarkdown(text);
  return lines
    .map((line) => {
      if (line.type === "empty") return "";
      if (line.type === "bullet") return `  • ${tokensToPlainText(line.tokens)}`;
      if (line.type === "numbered") return `  ${line.number}. ${tokensToPlainText(line.tokens)}`;
      return tokensToPlainText(line.tokens);
    })
    .join("\n");
}

/**
 * Render markdown text to PDF with proper formatting.
 * Handles page breaks automatically within long content.
 */
function renderMarkdownToPdf(doc: PDFKit.PDFDocument, text: string, width?: number): void {
  const lines = parseMarkdown(text);
  const textWidth = width || 495; // Default content width
  const currentX = doc.x || 50;
  const pageBottom = 750; // Leave margin at bottom

  // Helper to check and handle page break
  const checkPageBreak = (estimatedHeight: number = 30) => {
    if (doc.y + estimatedHeight > pageBottom) {
      doc.addPage();
      return true;
    }
    return false;
  };

  for (const line of lines) {
    if (line.type === "empty") {
      doc.moveDown(0.5);
      continue;
    }

    if (line.type === "hr") {
      checkPageBreak(20);
      doc.moveDown(0.3);
      doc.moveTo(currentX, doc.y).lineTo(currentX + textWidth, doc.y).stroke("#d1d5db");
      doc.moveDown(0.3);
      continue;
    }

    if (line.type === "header") {
      checkPageBreak(30);
      // Headers 1-6 with decreasing sizes
      const fontSize = line.level === 1 ? 14
        : line.level === 2 ? 12
        : line.level === 3 ? 11
        : 10;
      doc.fontSize(fontSize).font("DejaVu-Bold");
      // Use token-based rendering for math support
      if (containsMathTokens(line.tokens)) {
        doc.x = currentX;
        renderTokensToPdf(doc, line.tokens, fontSize, true);
      } else {
        doc.text(tokensToPlainText(line.tokens), currentX, doc.y, { width: textWidth });
      }
      doc.moveDown(0.4);
      doc.font("DejaVu").fontSize(10);
      continue;
    }

    if (line.type === "blockquote") {
      const quoteText = tokensToPlainText(line.tokens);
      const quoteHeight = doc.heightOfString(quoteText, { width: textWidth - 15 });
      checkPageBreak(quoteHeight + 10);

      // Draw a left border for blockquote
      const quoteY = doc.y;
      doc.rect(currentX, quoteY, 3, quoteHeight + 4).fill("#9ca3af");
      doc.fontSize(10).font("DejaVu-Oblique").fillColor("#4b5563");
      // Use token-based rendering for math support
      if (containsMathTokens(line.tokens)) {
        doc.x = currentX + 10;
        doc.y = quoteY;
        renderTokensToPdf(doc, line.tokens, 10, true);
      } else {
        doc.text(quoteText, currentX + 10, quoteY, { width: textWidth - 15 });
      }
      doc.font("DejaVu").fillColor("#374151");
      doc.moveDown(0.3);
      continue;
    }

    if (line.type === "bullet") {
      const bulletText = tokensToPlainText(line.tokens);
      const bulletHeight = doc.heightOfString(bulletText, { width: textWidth - 15 });
      checkPageBreak(bulletHeight + 5);

      doc.fontSize(10).font("DejaVu");
      doc.text("•  ", currentX, doc.y, { continued: true });
      // Use token-based rendering for math support
      if (containsMathTokens(line.tokens)) {
        renderTokensToPdf(doc, line.tokens, 10, true);
      } else {
        doc.text(bulletText, { width: textWidth - 15 });
      }
      continue;
    }

    if (line.type === "numbered") {
      const numText = tokensToPlainText(line.tokens);
      const numHeight = doc.heightOfString(numText, { width: textWidth - 20 });
      checkPageBreak(numHeight + 5);

      doc.fontSize(10).font("DejaVu");
      doc.text(`${line.number}.  `, currentX, doc.y, { continued: true });
      // Use token-based rendering for math support
      if (containsMathTokens(line.tokens)) {
        renderTokensToPdf(doc, line.tokens, 10, true);
      } else {
        doc.text(numText, { width: textWidth - 20 });
      }
      continue;
    }

    if (line.type === "code-block") {
      const codeText = line.code || "";
      const codeHeight = doc.heightOfString(codeText, { width: textWidth - 20 }) + 24;
      checkPageBreak(Math.min(codeHeight, 200)); // Don't require too much space

      doc.moveDown(0.3);
      const codeY = doc.y;

      // Dark code background (VS Code Dark+ style)
      doc.rect(currentX, codeY, textWidth, codeHeight).fill(CODE_BACKGROUND);

      // Language label (light text on dark background)
      if (line.language) {
        doc.fontSize(8).font("DejaVu").fillColor("#888888");
        doc.text(line.language, currentX + 8, codeY + 4);
        doc.y = codeY + 16;
      } else {
        doc.y = codeY + 8;
      }

      // Syntax-highlighted code content
      const tokens = highlightCode(codeText, line.language);
      doc.fontSize(9).font("Courier");

      // Render tokens with colors
      const codeStartX = currentX + 8;
      const codeWidth = textWidth - 16;
      let lineX = codeStartX;
      const lineHeight = 11;

      for (const token of tokens) {
        doc.fillColor(token.color);

        // Handle newlines within tokens
        const parts = token.text.split("\n");
        for (let i = 0; i < parts.length; i++) {
          if (i > 0) {
            // New line
            doc.y += lineHeight;
            lineX = codeStartX;
          }

          if (parts[i]) {
            const textWidth = doc.widthOfString(parts[i]);
            // Check if we need to wrap (simple word wrap)
            if (lineX + textWidth > codeStartX + codeWidth && lineX > codeStartX) {
              doc.y += lineHeight;
              lineX = codeStartX;
            }
            doc.text(parts[i], lineX, doc.y, { continued: true, lineBreak: false });
            lineX += textWidth;
          }
        }
      }

      // End the continued text and position after the code block
      doc.text("", { continued: false });
      doc.y = codeY + codeHeight; // Ensure we're positioned after the background box
      doc.font("DejaVu").fontSize(10).fillColor("#374151");
      doc.moveDown(0.4);
      continue;
    }

    if (line.type === "table") {
      checkPageBreak(50);
      doc.moveDown(0.3);
      const rows = line.tableRows || [];
      if (rows.length === 0) continue;

      // Calculate column widths based on content (min 40px, max 200px)
      const numCols = Math.max(...rows.map(r => r.cells.length));
      const colWidths: number[] = Array(numCols).fill(40);

      doc.fontSize(9).font("DejaVu");
      for (const row of rows) {
        for (let i = 0; i < row.cells.length; i++) {
          const text = tokensToPlainText(row.cells[i]);
          const textW = doc.widthOfString(text) + 16; // padding
          colWidths[i] = Math.min(200, Math.max(colWidths[i], textW));
        }
      }

      // Scale if total exceeds available width
      const totalWidth = colWidths.reduce((a, b) => a + b, 0);
      const scale = totalWidth > textWidth ? textWidth / totalWidth : 1;
      const scaledWidths = colWidths.map(w => w * scale);

      const minRowHeight = 18;
      const tableX = currentX;
      const tableStartY = doc.y;

      // Draw top border
      doc.strokeColor("#9ca3af").lineWidth(0.5);
      doc.moveTo(tableX, tableStartY).lineTo(tableX + scaledWidths.reduce((a, b) => a + b, 0), tableStartY).stroke();

      for (let rowIdx = 0; rowIdx < rows.length; rowIdx++) {
        const row = rows[rowIdx];

        // Calculate row height based on content (use correct font for measurement)
        doc.fontSize(9).font(row.isHeader ? "DejaVu-Bold" : "DejaVu");
        let rowHeight = minRowHeight;
        for (let cellIdx = 0; cellIdx < numCols; cellIdx++) {
          const cellTokens = row.cells[cellIdx] || [];
          const cellText = tokensToPlainText(cellTokens);
          const cellWidth = scaledWidths[cellIdx];
          const textHeight = doc.heightOfString(cellText, { width: cellWidth - 8 }) + 8;
          rowHeight = Math.max(rowHeight, textHeight);
        }

        checkPageBreak(rowHeight + 10);
        const rowY = doc.y;

        // Draw row background for header
        if (row.isHeader) {
          doc.rect(tableX, rowY, scaledWidths.reduce((a, b) => a + b, 0), rowHeight).fill("#e5e7eb");
        }

        // Draw cells with vertical borders
        let cellX = tableX;
        doc.strokeColor("#9ca3af").lineWidth(0.5);
        doc.moveTo(cellX, rowY).lineTo(cellX, rowY + rowHeight).stroke(); // Left border

        for (let cellIdx = 0; cellIdx < numCols; cellIdx++) {
          const cellWidth = scaledWidths[cellIdx];
          const cellTokens = row.cells[cellIdx] || [];
          const cellText = tokensToPlainText(cellTokens);

          // Text styling
          if (row.isHeader) {
            doc.font("DejaVu-Bold").fillColor("#1f2937");
          } else {
            doc.font("DejaVu").fillColor("#374151");
          }
          doc.fontSize(9);

          // Render cell content (single-line for table cells)
          doc.text(cellText, cellX + 4, rowY + 4, { width: cellWidth - 8 });

          cellX += cellWidth;
          // Right border for each cell
          doc.moveTo(cellX, rowY).lineTo(cellX, rowY + rowHeight).stroke();
        }

        doc.y = rowY + rowHeight;
        doc.x = currentX; // Reset x position

        // Draw horizontal line after each row
        doc.moveTo(tableX, doc.y).lineTo(tableX + scaledWidths.reduce((a, b) => a + b, 0), doc.y).stroke();
      }

      // Reset position after table
      doc.x = currentX;
      doc.moveDown(0.4);
      doc.fillColor("#374151"); // Reset fill color after stroke operations
      continue;
    }

    // Paragraph - render with proper text wrapping
    const paragraphText = tokensToPlainText(line.tokens);
    if (paragraphText.trim()) {
      const paraHeight = doc.heightOfString(paragraphText, { width: textWidth });
      checkPageBreak(Math.min(paraHeight, 50)); // At least check before starting

      doc.fontSize(10).font("DejaVu");

      // Use token-based rendering for math support
      if (containsMathTokens(line.tokens)) {
        doc.x = currentX;
        renderTokensToPdf(doc, line.tokens, 10, true);
      } else {
        doc.text(paragraphText, currentX, doc.y, { width: textWidth, align: "left" });
      }
      doc.moveDown(0.3);
    }
  }
}


/**
 * Format a discussion as markdown.
 */
export function formatDiscussionAsMarkdown(options: ExportOptions): string {
  const { question, messages, method, models } = options;

  const lines: string[] = [];

  // Header
  lines.push(`# ${t("export.doc.title")}`);
  lines.push("");
  lines.push(`**${t("export.doc.dateLabel")}** ${new Date().toLocaleString()}`);
  lines.push(`**${t("export.doc.methodLabel")}** ${method.charAt(0).toUpperCase() + method.slice(1)}`);
  lines.push(`**${t("export.doc.modelsLabel")}** ${models.map(formatModelName).join(", ")}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  // Question
  lines.push(`## ${t("export.doc.questionHeader")}`);
  lines.push("");
  lines.push(`> ${question}`);
  lines.push("");

  // Discussion
  lines.push(`## ${t("export.doc.discussionHeader")}`);
  lines.push("");

  for (const msg of messages) {
    const source = formatModelName(msg.source || "");

    if (msg.type === "phase") {
      const phaseMsg = msg.phaseMessageKey ? t(msg.phaseMessageKey as TranslationKey, msg.phaseParams || {}) : "";
      lines.push(`### ${t("export.doc.phaseLabel")} ${msg.phase}: ${phaseMsg}`);
      lines.push("");
    } else if (msg.type === "answer" || msg.type === "chat") {
      const roleTag = msg.role ? ` [${translateRole(msg.role)}]` : "";
      lines.push(`#### ${source}${roleTag}`);
      lines.push("");
      // Strip duplicate role prefix from content (e.g., "[DEFENDER] ModelName (Response to X):")
      let content = msg.content || "";
      content = content.replace(/^\s*\[(FOR|AGAINST|ADVOCATE|DEFENDER|QUESTIONER|RESPONDENT|PANELIST|IDEATOR|EVALUATOR)\]\s*[^(]+\([^)]*\):\s*/i, "");
      lines.push(content);
      lines.push("");
    } else if (msg.type === "critique") {
      lines.push(`#### ${source} (${t("export.doc.critiqueLabel")})`);
      lines.push("");
      if (msg.agreements) {
        lines.push(`**${t("export.doc.agreementsLabel")}**`);
        lines.push(msg.agreements);
        lines.push("");
      }
      if (msg.disagreements) {
        lines.push(`**${t("export.doc.disagreementsLabel")}**`);
        lines.push(msg.disagreements);
        lines.push("");
      }
      if (msg.missing) {
        lines.push(`**${t("export.doc.missingLabel")}**`);
        lines.push(msg.missing);
        lines.push("");
      }
    } else if (msg.type === "position") {
      lines.push(`#### ${source} (${t("export.doc.finalPositionLabel")})`);
      lines.push("");
      lines.push(`**${t("export.doc.confidenceLabel")}** ${translateConfidence(msg.confidence || "")}`);
      lines.push("");
      lines.push(msg.position || "");
      lines.push("");
    } else if (msg.type === "synthesis") {
      const term = getMethodTerminology(method);

      lines.push("---");
      lines.push("");
      lines.push(`## ${term.resultLabel}`);
      lines.push("");

      // Show consensus line (skip for Advocate)
      if (term.showConsensus) {
        lines.push(`**${term.consensusLabel}:** ${translateConsensus(msg.consensus || "")}`);
      }

      lines.push(`**${term.byLabel}:** ${formatModelName(msg.synthesizerModel || "")}`);
      lines.push("");
      lines.push(`### ${term.synthesisLabel}`);
      lines.push("");
      lines.push(msg.synthesis || "");
      lines.push("");
      // Skip placeholder differences for Advocate
      if (msg.differences && msg.differences !== "See verdict above for unresolved questions.") {
        lines.push(`### ${term.differencesLabel}`);
        lines.push("");
        lines.push(msg.differences);
        lines.push("");
      }
    }
  }

  // Footer
  lines.push("---");
  lines.push("");
  lines.push(`*${t("export.doc.footer")}*`);

  return lines.join("\n");
}

/**
 * Generate a filename for the export.
 * Format: quorum-{method}-{question}-{timestamp}.{ext}
 */
function generateFilename(question: string, method: string, format: ExportFormat): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const sanitizedQuestion = question
    .slice(0, 40)
    .replace(/[^a-zA-Z0-9\s]/g, "")  // Keep spaces temporarily
    .trim()
    .replace(/\s+/g, "-")            // Spaces to hyphens
    .toLowerCase()
    .replace(/-+/g, "-")             // Collapse multiple hyphens
    .replace(/^-|-$/g, "");          // Remove leading/trailing hyphens
  const extension = format === "text" ? "txt" : format;
  return `quorum-${method}-${sanitizedQuestion}-${timestamp}.${extension}`;
}


/**
 * Validate a path is safe for writing (TOCTOU-safe symlink check).
 * Uses lstat to detect symlinks without following them.
 *
 * Allows paths under:
 * - User's home directory
 * - Current working directory (project folder)
 *
 * @throws Error if path is a symlink or contains symlink components
 */
async function validatePathSecurity(targetPath: string): Promise<void> {
  const resolved = path.resolve(targetPath);
  const homeDir = os.homedir();
  const cwd = process.cwd();

  // Check if path is under home directory OR current working directory
  const isUnderHome = resolved.startsWith(homeDir + path.sep) || resolved === homeDir;
  const isUnderCwd = resolved.startsWith(cwd + path.sep) || resolved === cwd;

  if (!isUnderHome && !isUnderCwd) {
    throw new Error(`Security: Path must be under home directory or project folder: ${targetPath}`);
  }

  // Check each component of the path for symlinks (TOCTOU-safe)
  let currentPath = resolved;
  const pathsToCheck: string[] = [];

  // Determine the base directory to stop at (whichever applies)
  const baseDir = isUnderCwd ? cwd : homeDir;

  // Build list of paths from target up to base dir
  while (currentPath !== baseDir && currentPath !== path.dirname(currentPath)) {
    pathsToCheck.unshift(currentPath);
    currentPath = path.dirname(currentPath);
  }

  // Check each path component for symlinks using lstat (doesn't follow symlinks)
  for (const checkPath of pathsToCheck) {
    try {
      const stat = await fsPromises.lstat(checkPath);
      if (stat.isSymbolicLink()) {
        throw new Error(`Security: Symlinks not allowed for safety: ${checkPath}`);
      }
    } catch (err) {
      // ENOENT is OK (path doesn't exist yet), other errors should propagate
      if ((err as NodeJS.ErrnoException).code !== "ENOENT") {
        throw err;
      }
      // Path doesn't exist yet, which is fine - we'll create it
      break;
    }
  }
}

/**
 * Save discussion to a specific directory (for auto-logging, always markdown).
 * Creates directory if it doesn't exist.
 * Returns the path to the saved file.
 *
 * Security: Validates path just-in-time before write to prevent TOCTOU attacks.
 */
export async function saveDiscussionToDir(options: ExportOptions, dir: string): Promise<string> {
  const markdown = formatDiscussionAsMarkdown(options);
  const filename = generateFilename(options.question, options.method, "md");

  // TOCTOU-safe validation: check just before write
  await validatePathSecurity(dir);

  // Ensure directory exists
  await fsPromises.mkdir(dir, { recursive: true });

  // Re-validate after mkdir to catch race condition where attacker
  // replaces newly created dir with symlink between mkdir and write
  await validatePathSecurity(dir);

  const savePath = path.join(dir, filename);

  // Final validation of the exact file path
  await validatePathSecurity(path.dirname(savePath));

  await fsPromises.writeFile(savePath, markdown, "utf-8");

  return savePath;
}

/**
 * Information about a report file for the export selector.
 */
export interface ReportFileInfo {
  path: string;
  filename: string;
  mtime: Date;
  question: string;
  method: string;
}

/**
 * Extract method from filename (quorum-{method}-{question}-{timestamp}.md)
 */
function extractMethodFromFilename(filename: string): string {
  // Format: quorum-{method}-{question}-{timestamp}.md
  const match = filename.match(/^quorum-([a-z]+)-/);
  return match ? match[1] : "standard";
}

/**
 * Extract the question from a markdown log file.
 */
async function extractQuestionFromLog(logPath: string): Promise<string> {
  try {
    const content = await fsPromises.readFile(logPath, "utf-8");
    // Look for blockquote after "## Question"
    const match = content.match(/## Question\s*\n+>\s*(.+)/);
    if (match) {
      return match[1].slice(0, 60);
    }
    // Fallback: try to extract from filename
    const filename = path.basename(logPath, ".md");
    const parts = filename.replace("quorum-", "").split("-20");
    if (parts.length > 0) {
      return parts[0].replace(/-/g, " ").slice(0, 60);
    }
    return "Unknown question";
  } catch {
    return "Unknown question";
  }
}

/**
 * List recent report files from a directory.
 * Returns the most recent files sorted by modification time.
 */
export async function listRecentReports(dir: string, limit = 10): Promise<ReportFileInfo[]> {
  try {
    await fsPromises.access(dir);
  } catch {
    return [];
  }

  const entries = await fsPromises.readdir(dir);
  const reportFiles = entries.filter(f => f.startsWith("quorum-") && f.endsWith(".md"));

  const files = await Promise.all(
    reportFiles.map(async f => {
      const filePath = path.join(dir, f);
      const stat = await fsPromises.stat(filePath);
      const question = await extractQuestionFromLog(filePath);
      return {
        filename: f,
        path: filePath,
        mtime: stat.mtime,
        question,
        method: extractMethodFromFilename(f),
      };
    })
  );

  files.sort((a, b) => b.mtime.getTime() - a.mtime.getTime());
  return files.slice(0, limit);
}

/**
 * Export a specific log file to a different format.
 * Reads the markdown log and converts to the target format.
 * Returns the path to the exported file.
 *
 * Security: Validates paths just-in-time before write to prevent TOCTOU attacks.
 */
export async function exportSpecificLog(
  logPath: string,
  format: ExportFormat,
  exportDir: string
): Promise<string> {
  try {
    await fsPromises.access(logPath);
  } catch {
    throw new Error(`Log file not found: ${logPath}`);
  }

  const markdown = await fsPromises.readFile(logPath, "utf-8");

  // TOCTOU-safe validation: check just before write
  await validatePathSecurity(exportDir);

  // Ensure directory exists
  await fsPromises.mkdir(exportDir, { recursive: true });

  // Re-validate after mkdir
  await validatePathSecurity(exportDir);

  // Generate export filename with current timestamp
  const reportFilename = path.basename(logPath, ".md");
  const exportTimestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const extension = format === "text" ? "txt" : format;
  const exportFilename = `${reportFilename}-export-${exportTimestamp}.${extension}`;
  const exportPath = path.join(exportDir, exportFilename);

  if (format === "md") {
    await fsPromises.copyFile(logPath, exportPath);
  } else if (format === "text") {
    const plainText = stripMarkdown(markdown);
    await fsPromises.writeFile(exportPath, plainText, "utf-8");
  } else if (format === "pdf") {
    const doc = new PDFDocument({
      size: "A4",
      margins: { top: 50, bottom: 50, left: 50, right: 50 },
    });

    // Register DejaVu Sans fonts for Unicode support
    registerFonts(doc);

    // Use promise-based stream handling
    await new Promise<void>((resolve, reject) => {
      const stream = fs.createWriteStream(exportPath);
      stream.on("finish", resolve);
      stream.on("error", reject);
      doc.pipe(stream);
      renderMarkdownLogToPdf(doc, markdown);
      doc.end();
    });
  }

  return exportPath;
}

/**
 * Render a parsed discussion document to PDF using the PDFRenderer class.
 */
function renderDiscussionToPdf(doc: PDFKit.PDFDocument, document: ReturnType<typeof parseMarkdownLog>): void {
  const renderer = new PDFRenderer(doc, formatModelName, renderMarkdownToPdf);
  renderer.render(document);
}

/**
 * Parse a markdown log file and render it as a styled PDF.
 * Uses the two-step architecture: parse to structure, then render from structure.
 */
function renderMarkdownLogToPdf(doc: PDFKit.PDFDocument, markdown: string): void {
  // Clean all LaTeX in the markdown before parsing
  let cleanedMarkdown = cleanTextForPdf(markdown);

  // Strip the markdown footer before parsing (PDF adds its own footer)
  cleanedMarkdown = cleanedMarkdown.replace(/\n---\n+\*Exported from \[Quorum\][^\n]*\*?\s*$/, "");

  // Parse markdown to structured document
  const parsedDocument = parseMarkdownLog(cleanedMarkdown);

  // Render from structured document
  renderDiscussionToPdf(doc, parsedDocument);
}

