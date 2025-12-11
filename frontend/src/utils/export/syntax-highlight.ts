/**
 * Syntax highlighting for PDF code blocks using highlight.js.
 * Converts code to colored tokens for rendering in PDFKit.
 */

import hljs from "highlight.js";

/** A token with text and color for PDF rendering */
export interface HighlightToken {
  text: string;
  color: string;
}

/**
 * VS Code Dark+ inspired color palette.
 * Maps highlight.js CSS classes to hex colors.
 */
const TOKEN_COLORS: Record<string, string> = {
  // Keywords and control flow
  keyword: "#569cd6",
  "built_in": "#569cd6",
  type: "#569cd6",
  literal: "#569cd6",

  // Strings and chars
  string: "#ce9178",
  char: "#ce9178",
  regexp: "#d16969",

  // Comments
  comment: "#6a9955",
  doctag: "#608b4e",

  // Numbers
  number: "#b5cea8",

  // Functions and methods
  function: "#dcdcaa",
  "title.function": "#dcdcaa",
  "title.function_": "#dcdcaa",

  // Classes and types
  "title.class": "#4ec9b0",
  "title.class_": "#4ec9b0",
  class: "#4ec9b0",

  // Variables and parameters
  variable: "#9cdcfe",
  params: "#9cdcfe",
  attr: "#9cdcfe",
  property: "#9cdcfe",

  // Operators and punctuation
  operator: "#d4d4d4",
  punctuation: "#d4d4d4",

  // Meta and preprocessor
  meta: "#c586c0",
  "meta keyword": "#c586c0",

  // Tags (HTML/XML)
  tag: "#569cd6",
  name: "#569cd6",
  attribute: "#9cdcfe",

  // Additions/deletions (diff)
  addition: "#b5cea8",
  deletion: "#ce9178",

  // Default
  default: "#d4d4d4",
};

/**
 * Get color for a highlight.js CSS class.
 * Handles nested classes like "hljs-title hljs-function".
 */
function getColorForClass(className: string): string {
  // Remove "hljs-" prefix if present
  const cleanClass = className.replace(/^hljs-/, "");

  // Try exact match first
  if (TOKEN_COLORS[cleanClass]) {
    return TOKEN_COLORS[cleanClass];
  }

  // Try with underscores instead of dots
  const withUnderscores = cleanClass.replace(/\./g, "_");
  if (TOKEN_COLORS[withUnderscores]) {
    return TOKEN_COLORS[withUnderscores];
  }

  // Try first part of compound class
  const firstPart = cleanClass.split(/[.\s]/)[0];
  if (TOKEN_COLORS[firstPart]) {
    return TOKEN_COLORS[firstPart];
  }

  return TOKEN_COLORS.default;
}

/**
 * Parse highlight.js HTML output into colored tokens.
 * Handles nested spans and extracts text with colors.
 */
function parseHighlightedHtml(html: string): HighlightToken[] {
  const tokens: HighlightToken[] = [];
  let currentColor = TOKEN_COLORS.default;
  const colorStack: string[] = [];

  // Simple regex-based parser for highlight.js HTML output
  // Matches: <span class="..."> | </span> | text
  const regex = /<span class="([^"]+)">|<\/span>|([^<]+)/g;
  let match;

  while ((match = regex.exec(html)) !== null) {
    if (match[1]) {
      // Opening span with class
      colorStack.push(currentColor);
      currentColor = getColorForClass(match[1]);
    } else if (match[0] === "</span>") {
      // Closing span
      currentColor = colorStack.pop() || TOKEN_COLORS.default;
    } else if (match[2]) {
      // Text content
      const text = match[2]
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&amp;/g, "&")
        .replace(/&quot;/g, '"')
        .replace(/&#x27;/g, "'")
        .replace(/&#39;/g, "'");

      if (text) {
        tokens.push({ text, color: currentColor });
      }
    }
  }

  return tokens;
}

/**
 * Highlight code and return colored tokens for PDF rendering.
 *
 * @param code - The source code to highlight
 * @param language - Optional language hint (e.g., "python", "typescript")
 * @returns Array of tokens with text and color
 */
export function highlightCode(code: string, language?: string): HighlightToken[] {
  try {
    // Map common language aliases
    const languageMap: Record<string, string> = {
      js: "javascript",
      ts: "typescript",
      py: "python",
      rb: "ruby",
      sh: "bash",
      yml: "yaml",
    };

    const lang = language ? (languageMap[language.toLowerCase()] || language.toLowerCase()) : undefined;

    // Highlight the code
    const result = lang && hljs.getLanguage(lang)
      ? hljs.highlight(code, { language: lang, ignoreIllegals: true })
      : hljs.highlightAuto(code);

    // Parse HTML to tokens
    return parseHighlightedHtml(result.value);
  } catch {
    // Fallback: return plain text with default color
    return [{ text: code, color: TOKEN_COLORS.default }];
  }
}

/** Dark background color for code blocks (VS Code Dark+) */
export const CODE_BACKGROUND = "#1e1e1e";

/** Export color palette for potential customization */
export { TOKEN_COLORS };
