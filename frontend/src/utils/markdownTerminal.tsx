/**
 * Terminal markdown renderer using ink components.
 */

import React from "react";
import { Text, Box } from "ink";
import { parseMarkdown, type ParsedLine, type InlineToken, type TableRow } from "./markdown.js";

// =============================================================================
// Inline Token Renderer
// =============================================================================

function renderToken(token: InlineToken, key: number): React.ReactNode {
  switch (token.type) {
    case "bold":
      return <Text key={key} bold>{token.content}</Text>;
    case "italic":
      return <Text key={key} italic>{token.content}</Text>;
    case "code":
      return <Text key={key} color="cyan">{token.content}</Text>;
    case "link":
      // Show link text with URL in parentheses
      return <Text key={key} color="blue">{token.content}</Text>;
    case "math":
      // Math tokens have Unicode-converted content for terminal display
      return <Text key={key}>{token.content}</Text>;
    case "text":
    default:
      return <Text key={key}>{token.content}</Text>;
  }
}

function renderTokens(tokens: InlineToken[]): React.ReactNode {
  return tokens.map((token, i) => renderToken(token, i));
}

// =============================================================================
// Table Renderer
// =============================================================================

/**
 * Get plain text content from tokens for measuring width.
 */
function getTokensText(tokens: InlineToken[]): string {
  return tokens.map((t) => t.content).join("");
}

/**
 * Render a properly formatted table with box-drawing characters.
 */
function renderTable(rows: TableRow[], key: number): React.ReactNode {
  if (rows.length === 0) return null;

  // Calculate column widths (max width per column, min 3 chars)
  const numCols = Math.max(...rows.map((r) => r.cells.length));
  const colWidths: number[] = Array(numCols).fill(3);

  for (const row of rows) {
    for (let i = 0; i < row.cells.length; i++) {
      const text = getTokensText(row.cells[i]);
      colWidths[i] = Math.max(colWidths[i], text.length);
    }
  }

  // Build horizontal lines
  const topLine = "┌" + colWidths.map((w) => "─".repeat(w + 2)).join("┬") + "┐";
  const sepLine = "├" + colWidths.map((w) => "─".repeat(w + 2)).join("┼") + "┤";
  const botLine = "└" + colWidths.map((w) => "─".repeat(w + 2)).join("┴") + "┘";

  // Render a row with proper padding, preserving inline formatting
  const renderRow = (row: TableRow, rowIndex: number) => {
    const cells = colWidths.map((width, i) => {
      const cellTokens = row.cells[i] || [];
      const text = getTokensText(cellTokens);
      const padding = " ".repeat(Math.max(0, width - text.length));

      // Render tokens with formatting, add padding at end
      return (
        <Text key={i} bold={row.isHeader}>
          {" "}{renderTokens(cellTokens)}{padding}{" "}
        </Text>
      );
    });

    return (
      <Box key={`row-${rowIndex}`}>
        <Text dimColor>│</Text>
        {cells.map((cell, i) => (
          <React.Fragment key={i}>
            {cell}
            <Text dimColor>│</Text>
          </React.Fragment>
        ))}
      </Box>
    );
  };

  // Build the table
  const elements: React.ReactNode[] = [];
  elements.push(<Text key="top" dimColor>{topLine}</Text>);

  for (let i = 0; i < rows.length; i++) {
    elements.push(renderRow(rows[i], i));
    // Add separator after header row
    if (rows[i].isHeader && i < rows.length - 1) {
      elements.push(<Text key="sep" dimColor>{sepLine}</Text>);
    }
  }

  elements.push(<Text key="bot" dimColor>{botLine}</Text>);

  return (
    <Box key={key} flexDirection="column" marginY={1}>
      {elements}
    </Box>
  );
}

// =============================================================================
// Line Renderer
// =============================================================================

function renderLine(line: ParsedLine, key: number): React.ReactNode {
  switch (line.type) {
    case "empty":
      return <Text key={key}>{" "}</Text>;

    case "hr":
      return (
        <Box key={key} marginY={1}>
          <Text dimColor>────────────────────────────────────────</Text>
        </Box>
      );

    case "header":
      // Different colors for header levels (1-6)
      const headerColor = line.level === 1 ? "green"
        : line.level === 2 ? "yellow"
        : line.level === 3 ? "cyan"
        : "white";
      return (
        <Box key={key} marginTop={line.level === 1 ? 1 : 0}>
          <Text bold color={headerColor}>
            {renderTokens(line.tokens)}
          </Text>
        </Box>
      );

    case "blockquote":
      return (
        <Box key={key} marginLeft={2}>
          <Text color="gray">│ </Text>
          <Text italic>{renderTokens(line.tokens)}</Text>
        </Box>
      );

    case "bullet":
      return (
        <Box key={key} marginLeft={2}>
          <Text>• </Text>
          <Text>{renderTokens(line.tokens)}</Text>
        </Box>
      );

    case "numbered":
      return (
        <Box key={key} marginLeft={2}>
          <Text>{line.number}. </Text>
          <Text>{renderTokens(line.tokens)}</Text>
        </Box>
      );

    case "code-block":
      return (
        <Box key={key} flexDirection="column" marginY={1} paddingX={1} borderStyle="single" borderColor="gray">
          {line.language && (
            <Text dimColor>{line.language}</Text>
          )}
          <Text color="cyan">{line.code}</Text>
        </Box>
      );

    case "table":
      return renderTable(line.tableRows || [], key);

    case "paragraph":
    default:
      return (
        <Text key={key}>{renderTokens(line.tokens)}</Text>
      );
  }
}

// =============================================================================
// Main Component
// =============================================================================

interface MarkdownProps {
  children: string;
}

export function Markdown({ children }: MarkdownProps): React.ReactElement {
  const lines = parseMarkdown(children);

  return (
    <Box flexDirection="column">
      {lines.map((line, i) => renderLine(line, i))}
    </Box>
  );
}
