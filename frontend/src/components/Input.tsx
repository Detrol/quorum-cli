/**
 * Text input component with command palette integration.
 */

import React, { useState, useCallback } from "react";
import { Box, Text, useInput } from "ink";
import { CommandPalette } from "./CommandPalette.js";

interface InputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  onCommand: (command: string) => void;
  onHistoryNavigate?: (direction: "up" | "down") => void;
  onAdvisorOpen?: () => void;
  placeholder?: string;
  disabled?: boolean;
}

export function Input({
  value,
  onChange,
  onSubmit,
  onCommand,
  onHistoryNavigate,
  onAdvisorOpen,
  placeholder = "Ask a question...",
  disabled = false,
}: InputProps) {
  const [showPalette, setShowPalette] = useState(false);
  const [cursorPosition, setCursorPosition] = useState(value.length);

  // Update cursor when value changes externally
  React.useEffect(() => {
    setCursorPosition(value.length);
  }, [value]);

  useInput(
    (input, key) => {
      if (disabled) return;

      // Handle Tab to open Method Advisor
      if (key.tab && !showPalette && onAdvisorOpen) {
        onAdvisorOpen();
        return;
      }

      // Handle Escape to close palette
      if (key.escape && showPalette) {
        setShowPalette(false);
        return;
      }

      // Handle Enter
      if (key.return) {
        // If palette is shown and has exact match for command without params,
        // let palette handle it. Otherwise execute the full typed command.
        if (showPalette && value === "/") {
          // Just "/" typed - let palette handle selection
          return;
        }

        if (value.trim()) {
          if (value.startsWith("/")) {
            onCommand(value);
          } else {
            onSubmit(value);
          }
          onChange("");
          setCursorPosition(0);
          setShowPalette(false);
        }
        return;
      }

      // Handle Backspace
      if (key.backspace || key.delete) {
        if (cursorPosition > 0) {
          const newValue =
            value.slice(0, cursorPosition - 1) + value.slice(cursorPosition);
          onChange(newValue);
          setCursorPosition(cursorPosition - 1);

          // Hide palette if we delete the "/"
          if (!newValue.startsWith("/")) {
            setShowPalette(false);
          }
        }
        return;
      }

      // Handle arrow keys
      if (key.leftArrow) {
        setCursorPosition(Math.max(0, cursorPosition - 1));
        return;
      }

      if (key.rightArrow) {
        setCursorPosition(Math.min(value.length, cursorPosition + 1));
        return;
      }

      // Up/Down arrows for history navigation (when palette is not shown)
      if (key.upArrow && !showPalette && onHistoryNavigate) {
        onHistoryNavigate("up");
        return;
      }

      if (key.downArrow && !showPalette && onHistoryNavigate) {
        onHistoryNavigate("down");
        return;
      }

      // Handle regular character input
      if (input && !key.ctrl && !key.meta) {
        const newValue =
          value.slice(0, cursorPosition) + input + value.slice(cursorPosition);
        onChange(newValue);
        setCursorPosition(cursorPosition + input.length);

        // Show palette when "/" is typed at start
        if (input === "/" && cursorPosition === 0) {
          setShowPalette(true);
        } else if (newValue.startsWith("/")) {
          setShowPalette(true);
        }
      }
    },
    { isActive: !disabled }
  );

  const handlePaletteSelect = useCallback(
    (command: string, executeNow: boolean) => {
      if (executeNow) {
        // Execute immediately for commands without params
        onCommand(command);
        onChange("");
        setCursorPosition(0);
        setShowPalette(false);
      } else {
        // Just fill in command, let user add params
        onChange(command + " ");
        setCursorPosition(command.length + 1);
        setShowPalette(false);
      }
    },
    [onChange, onCommand]
  );

  const handlePaletteClose = useCallback(() => {
    setShowPalette(false);
  }, []);

  // Build display with cursor
  const displayValue = value || placeholder;
  const showPlaceholder = !value;

  return (
    <Box flexDirection="column">
      {/* Command Palette (above input) */}
      {showPalette && value.startsWith("/") && (
        <Box marginBottom={1}>
          <CommandPalette
            filter={value.slice(1)}
            onSelect={handlePaletteSelect}
            onClose={handlePaletteClose}
          />
        </Box>
      )}

      {/* Input line */}
      <Box>
        <Text color="green" bold>
          {"› "}
        </Text>
        {showPlaceholder ? (
          <Text dimColor>{placeholder}</Text>
        ) : (
          <>
            <Text>{value.slice(0, cursorPosition)}</Text>
            <Text backgroundColor="white" color="black">
              {value[cursorPosition] || " "}
            </Text>
            <Text>{value.slice(cursorPosition + 1)}</Text>
          </>
        )}
      </Box>
    </Box>
  );
}
