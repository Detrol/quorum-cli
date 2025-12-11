/**
 * Shared markdown parser for terminal and PDF rendering.
 * Supports a minimal subset of markdown for maximum compatibility.
 */

// =============================================================================
// Types
// =============================================================================

export interface InlineToken {
  type: "text" | "bold" | "italic" | "code" | "link" | "math";
  content: string;
  url?: string;  // For link tokens
  raw?: string;  // For math tokens: original LaTeX
}

export interface TableRow {
  cells: InlineToken[][];  // Each cell can have inline formatting
  isHeader: boolean;
}

export interface ParsedLine {
  type: "paragraph" | "header" | "bullet" | "numbered" | "empty" | "hr" | "blockquote" | "code-block" | "table";
  level?: number; // Header level (1-6) or list indent
  number?: number; // For numbered lists
  tokens: InlineToken[];
  raw: string;
  // Code block fields
  language?: string;     // For code-block: "typescript", "python", etc.
  code?: string;         // For code-block: the full code content
  // Table fields
  tableRows?: TableRow[]; // For table: all rows including header
}

// =============================================================================
// LaTeX to Unicode Converter
// =============================================================================

// Unicode subscript and superscript mappings
// Numbers have universal support; letters work in modern terminals with Unicode fonts
// Exported for reuse in export.ts PDF generation
export const SUBSCRIPTS: Record<string, string> = {
  // Numbers (universal support)
  "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
  "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
  // Letters (good support in modern terminals: Windows Terminal, iTerm2, etc.)
  "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ",
  "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ",
  "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ", "u": "ᵤ",
  "v": "ᵥ", "x": "ₓ",
  // Operators and symbols
  "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
  "*": "*", // Keep asterisk visible (e.g., R_* → R* for star formation rate)
};

export const SUPERSCRIPTS: Record<string, string> = {
  // Numbers (universal support)
  "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
  "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
  // Letters (good support in modern terminals)
  "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ",
  "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ",
  "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ",
  "p": "ᵖ", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ",
  "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ",
  // Operators
  "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
};

// LaTeX command replacements
// Exported for reuse in export.ts PDF generation
export const LATEX_COMMANDS: Record<string, string> = {
  "\\rightarrow": "→",
  "\\leftarrow": "←",
  "\\Rightarrow": "⇒",
  "\\Leftarrow": "⇐",
  "\\leftrightarrow": "↔",
  "\\times": "×",
  "\\div": "÷",
  "\\cdot": "·",
  "\\pm": "±",
  "\\mp": "∓",
  "\\approx": "≈",
  "\\neq": "≠",
  "\\leq": "≤",
  "\\geq": "≥",
  "\\ll": "≪",
  "\\gg": "≫",
  "\\infty": "∞",
  "\\sum": "Σ",
  "\\prod": "Π",
  "\\int": "∫",
  "\\partial": "∂",
  "\\nabla": "∇",
  "\\alpha": "α",
  "\\beta": "β",
  "\\gamma": "γ",
  "\\delta": "δ",
  "\\epsilon": "ε",
  "\\zeta": "ζ",
  "\\eta": "η",
  "\\theta": "θ",
  "\\iota": "ι",
  "\\kappa": "κ",
  "\\lambda": "λ",
  "\\mu": "μ",
  "\\nu": "ν",
  "\\xi": "ξ",
  "\\pi": "π",
  "\\rho": "ρ",
  "\\sigma": "σ",
  "\\tau": "τ",
  "\\upsilon": "υ",
  "\\phi": "φ",
  "\\chi": "χ",
  "\\psi": "ψ",
  "\\omega": "ω",
  "\\Delta": "Δ",
  "\\Gamma": "Γ",
  "\\Theta": "Θ",
  "\\Lambda": "Λ",
  "\\Xi": "Ξ",
  "\\Pi": "Π",
  "\\Sigma": "Σ",
  "\\Phi": "Φ",
  "\\Psi": "Ψ",
  "\\Omega": "Ω",
};

/**
 * Convert a string to subscript using Unicode characters.
 * If any character lacks a Unicode subscript, keeps original notation (e.g., _c).
 * This is more authentic for researchers who expect underscore notation as fallback.
 */
function toSubscript(text: string): string {
  // Check if ALL characters can be converted
  const allConvertible = text.split("").every(c => SUBSCRIPTS[c] !== undefined);
  if (allConvertible) {
    return text.split("").map(c => SUBSCRIPTS[c]).join("");
  }
  // Keep underscore notation for academic clarity
  return "_" + text;
}

/**
 * Convert a string to superscript using Unicode characters.
 * If any character lacks a Unicode superscript, keeps original notation (e.g., ^c).
 */
function toSuperscript(text: string): string {
  // Check if ALL characters can be converted
  const allConvertible = text.split("").every(c => SUPERSCRIPTS[c] !== undefined);
  if (allConvertible) {
    return text.split("").map(c => SUPERSCRIPTS[c]).join("");
  }
  // Keep caret notation for clarity
  return "^" + text;
}

/**
 * Convert LaTeX math notation to Unicode for terminal display.
 * Handles $...$ inline math, subscripts, superscripts, and common commands.
 */
function convertLatexToUnicode(text: string): string {
  let result = text;

  // Process inline math: $...$
  result = result.replace(/\$([^$]+)\$/g, (_, math) => {
    let converted = math;

    // Replace LaTeX commands first (before processing sub/superscripts)
    for (const [cmd, symbol] of Object.entries(LATEX_COMMANDS)) {
      // Escape backslash for regex
      const escaped = cmd.replace(/\\/g, "\\\\");
      converted = converted.replace(new RegExp(escaped, "g"), symbol);
    }

    // Handle subscripts: _{...} or _x
    converted = converted.replace(/_\{([^}]+)\}/g, (_: string, sub: string) => toSubscript(sub));
    converted = converted.replace(/_([a-zA-Z0-9])/g, (_: string, sub: string) => toSubscript(sub));

    // Handle superscripts: ^{...} or ^x
    converted = converted.replace(/\^\{([^}]+)\}/g, (_: string, sup: string) => toSuperscript(sup));
    converted = converted.replace(/\^([a-zA-Z0-9])/g, (_: string, sup: string) => toSuperscript(sup));

    return converted;
  });

  return result;
}

/**
 * Convert standalone LaTeX notation outside of $...$ delimiters.
 * Handles: LaTeX commands (\alpha, \rightarrow), subscripts (f_l, R_*), superscripts (10^{-3}).
 */
function convertStandaloneLatex(text: string): string {
  let result = text;

  // Replace LaTeX commands (e.g., \alpha → α)
  for (const [cmd, symbol] of Object.entries(LATEX_COMMANDS)) {
    const escaped = cmd.replace(/\\/g, "\\\\");
    result = result.replace(new RegExp(escaped, "g"), symbol);
  }

  // Convert obvious math subscripts outside of $ delimiters
  // Pattern: single letter/symbol followed by _ and subscript content
  // Examples: f_l, n_e, R_*, f_p, f_i, f_c
  // But NOT: snake_case_variables (multiple underscores)
  result = result.replace(/\b([A-Za-z])_\{([^}]+)\}/g, (_: string, base: string, sub: string) =>
    base + toSubscript(sub)
  );
  result = result.replace(/\b([A-Za-z])_([a-zA-Z0-9*])\b/g, (_: string, base: string, sub: string) =>
    base + toSubscript(sub === "*" ? "*" : sub)
  );

  // Convert obvious math superscripts outside of $ delimiters
  // Examples: 10^{-3}, x^2, n^{th}
  result = result.replace(/(\d+|\b[A-Za-z])\^\{([^}]+)\}/g, (_: string, base: string, sup: string) =>
    base + toSuperscript(sup)
  );
  result = result.replace(/(\d+|\b[A-Za-z])\^([a-zA-Z0-9])\b/g, (_: string, base: string, sup: string) =>
    base + toSuperscript(sup)
  );

  return result;
}

// =============================================================================
// Inline Tokenizer
// =============================================================================

/**
 * Normalize text for consistent LaTeX parsing.
 * Converts all math delimiter styles to $...$ for uniform processing.
 */
function normalizeForLatex(text: string): string {
  let result = text;

  // Convert LaTeX-style delimiters to dollar signs
  // Display math: \[...\] → $...$ ([\s\S]*? matches across newlines)
  result = result.replace(/\\\[([\s\S]*?)\\\]/g, " $$$1$$ ");
  // Inline math: \(...\) → $...$
  result = result.replace(/\\\(([\s\S]*?)\\\)/g, "$$$1$$");
  // Double dollar display math: $$...$$ → $...$ (normalize to single)
  result = result.replace(/\$\$([\s\S]*?)\$\$/g, " $$$1$$ ");

  // Remove backslash escaping of dollar signs: \$ → $
  result = result.replace(/\\(\$)/g, "$1");
  // Normalize Unicode dollar sign variants to ASCII
  result = result.replace(/[\uFE69\uFF04]/g, "$");

  return result;
}

/**
 * Parse inline formatting: **bold**, *italic*, `code`, [link](url), $math$
 */
function parseInline(text: string): InlineToken[] {
  const tokens: InlineToken[] = [];
  // Normalize for consistent LaTeX parsing
  let remaining = normalizeForLatex(text);

  // Regex patterns for inline formatting
  // Order matters: math first, then bold before italic (** before *)
  const patterns: Array<{
    regex: RegExp;
    type: "bold" | "italic" | "code" | "link" | "math";
    processor?: (match: RegExpMatchArray) => { content: string; raw?: string };
  }> = [
    {
      regex: /\$([^$]+)\$/,
      type: "math",
      processor: (match) => ({
        content: convertLatexToUnicode("$" + match[1] + "$"),  // Unicode for terminal
        raw: match[1],  // Original LaTeX for PDF
      }),
    },
    { regex: /\*\*([^*]+)\*\*/, type: "bold" },
    { regex: /\*([^*]+)\*/, type: "italic" },
    { regex: /`([^`]+)`/, type: "code" },
    { regex: /\[([^\]]+)\]\(([^)]+)\)/, type: "link" },
  ];

  // Also convert standalone LaTeX (commands, subscripts, superscripts outside of $...$)
  remaining = convertStandaloneLatex(remaining);

  while (remaining.length > 0) {
    let earliestMatch: {
      index: number;
      length: number;
      content: string;
      raw?: string;
      url?: string;
      type: "bold" | "italic" | "code" | "link" | "math";
      match: RegExpMatchArray;
      processor?: (match: RegExpMatchArray) => { content: string; raw?: string };
    } | null = null;

    // Find the earliest match among all patterns
    for (const pattern of patterns) {
      const match = remaining.match(pattern.regex);
      if (match && match.index !== undefined) {
        if (!earliestMatch || match.index < earliestMatch.index) {
          earliestMatch = {
            index: match.index,
            length: match[0].length,
            content: match[1],
            url: pattern.type === "link" ? match[2] : undefined,
            type: pattern.type,
            match,
            processor: pattern.processor,
          };
        }
      }
    }

    if (earliestMatch) {
      // Add text before the match
      if (earliestMatch.index > 0) {
        tokens.push({
          type: "text",
          content: remaining.slice(0, earliestMatch.index),
        });
      }

      // Add the formatted token
      let token: InlineToken;
      if (earliestMatch.processor) {
        // Use processor for math tokens
        const processed = earliestMatch.processor(earliestMatch.match);
        token = {
          type: earliestMatch.type,
          content: processed.content,
          raw: processed.raw,
        };
      } else {
        token = {
          type: earliestMatch.type,
          content: earliestMatch.content,
        };
        if (earliestMatch.url) {
          token.url = earliestMatch.url;
        }
      }
      tokens.push(token);

      // Continue with remaining text
      remaining = remaining.slice(earliestMatch.index + earliestMatch.length);
    } else {
      // No more matches, add remaining as text
      tokens.push({ type: "text", content: remaining });
      break;
    }
  }

  return tokens;
}

// =============================================================================
// Line Parser
// =============================================================================

/**
 * Parse a single line into a structured format.
 */
function parseLine(line: string): ParsedLine {
  const trimmed = line.trim();

  // Empty line
  if (!trimmed) {
    return { type: "empty", tokens: [], raw: line };
  }

  // Horizontal rule: --- or *** or ___
  if (/^[-*_]{3,}$/.test(trimmed)) {
    return { type: "hr", tokens: [], raw: line };
  }

  // Headers: # ## ### #### ##### ###### (1-6 levels)
  const headerMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
  if (headerMatch) {
    return {
      type: "header",
      level: headerMatch[1].length,
      tokens: parseInline(headerMatch[2]),
      raw: line,
    };
  }

  // Blockquote: > text
  const blockquoteMatch = trimmed.match(/^>\s*(.*)$/);
  if (blockquoteMatch) {
    return {
      type: "blockquote",
      tokens: parseInline(blockquoteMatch[1]),
      raw: line,
    };
  }

  // Bullet points: - or *
  const bulletMatch = trimmed.match(/^[-*]\s+(.+)$/);
  if (bulletMatch) {
    return {
      type: "bullet",
      tokens: parseInline(bulletMatch[1]),
      raw: line,
    };
  }

  // Numbered lists: 1. 2. etc. (allow missing space after period)
  const numberedMatch = trimmed.match(/^(\d+)\.\s*(.+)$/);
  if (numberedMatch) {
    return {
      type: "numbered",
      number: parseInt(numberedMatch[1], 10),
      tokens: parseInline(numberedMatch[2]),
      raw: line,
    };
  }

  // Regular paragraph
  return {
    type: "paragraph",
    tokens: parseInline(trimmed),
    raw: line,
  };
}

// =============================================================================
// Multi-line Block Parsers
// =============================================================================

/**
 * Try to parse a code block starting at the given index.
 * Returns the parsed block and end index, or null if not a code block.
 */
function tryParseCodeBlock(
  lines: string[],
  start: number
): { block: ParsedLine; endIndex: number } | null {
  const line = lines[start];
  // Allow optional leading whitespace for indented code blocks (e.g., inside bullet points)
  const openMatch = line.match(/^\s*```(\w*)\s*$/);
  if (!openMatch) return null;

  const language = openMatch[1] || "";
  const codeLines: string[] = [];
  let i = start + 1;

  // Find the closing ``` (allow leading/trailing whitespace)
  while (i < lines.length && !lines[i].match(/^\s*```\s*$/)) {
    codeLines.push(lines[i]);
    i++;
  }

  // No closing ``` found - not a valid code block
  if (i >= lines.length) return null;

  return {
    block: {
      type: "code-block",
      language: language || undefined,
      code: codeLines.join("\n"),
      tokens: [],
      raw: lines.slice(start, i + 1).join("\n"),
    },
    endIndex: i,
  };
}

/**
 * Parse table cells from a line like "| cell1 | cell2 |"
 */
function parseTableCells(line: string): InlineToken[][] {
  const trimmed = line.trim();
  // Remove outer pipes and split by |
  return trimmed
    .slice(1, -1)
    .split("|")
    .map((cell) => parseInline(cell.trim()));
}

/**
 * Try to parse a table starting at the given index.
 * Returns the parsed table and end index, or null if not a table.
 */
function tryParseTable(
  lines: string[],
  start: number
): { block: ParsedLine; endIndex: number } | null {
  // Need at least 2 lines: header + separator
  if (start + 1 >= lines.length) return null;

  const headerLine = lines[start].trim();
  const separatorLine = lines[start + 1].trim();

  // Check for table pattern: | col | col | and |---|---|
  if (!headerLine.match(/^\|.*\|$/) || !separatorLine.match(/^\|[-:\s|]+\|$/)) {
    return null;
  }

  const rows: TableRow[] = [];

  // Parse header row
  rows.push({
    cells: parseTableCells(headerLine),
    isHeader: true,
  });

  // Parse data rows (skip separator line at start + 1)
  let i = start + 2;
  while (i < lines.length && lines[i].trim().match(/^\|.*\|$/)) {
    rows.push({
      cells: parseTableCells(lines[i]),
      isHeader: false,
    });
    i++;
  }

  return {
    block: {
      type: "table",
      tableRows: rows,
      tokens: [],
      raw: lines.slice(start, i).join("\n"),
    },
    endIndex: i - 1,
  };
}

// =============================================================================
// Main Parser
// =============================================================================

/**
 * Parse markdown text into structured lines.
 * Uses two-pass approach for multi-line blocks (code blocks, tables).
 */
export function parseMarkdown(text: string): ParsedLine[] {
  const lines = text.split("\n");
  const result: ParsedLine[] = [];
  let i = 0;

  while (i < lines.length) {
    // Try to parse a code block first
    const codeBlock = tryParseCodeBlock(lines, i);
    if (codeBlock) {
      result.push(codeBlock.block);
      i = codeBlock.endIndex + 1;
      continue;
    }

    // Try to parse a table
    const table = tryParseTable(lines, i);
    if (table) {
      result.push(table.block);
      i = table.endIndex + 1;
      continue;
    }

    // Fallback: parse as single line
    result.push(parseLine(lines[i]));
    i++;
  }

  return result;
}

// =============================================================================
// Plain Text Converter
// =============================================================================

/**
 * Convert tokens to plain text (strips formatting).
 */
export function tokensToPlainText(tokens: InlineToken[]): string {
  return tokens.map((t) => t.content).join("");
}
