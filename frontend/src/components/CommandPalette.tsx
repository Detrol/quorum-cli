/**
 * Floating command palette component.
 * Appears above the input when "/" is typed.
 */

import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { t } from "../i18n/index.js";

interface Command {
  name: string;
  description: string;
  shortcut?: string;
  hasParams?: boolean; // If true, requires Enter to confirm (allows typing params)
}

// Commands with translated descriptions
const getCommands = (): Command[] => [
  { name: "/models", description: t("cmd.models"), shortcut: "m" },
  { name: "/method", description: t("cmd.method") },
  { name: "/synthesizer", description: t("cmd.synthesizer") },
  { name: "/status", description: t("cmd.status"), shortcut: "s" },
  { name: "/export", description: t("cmd.export"), hasParams: true },
  { name: "/clear", description: t("cmd.clear"), shortcut: "c" },
  { name: "/help", description: t("cmd.help"), shortcut: "?" },
  { name: "/quit", description: t("cmd.quit"), shortcut: "q" },
  { name: "/maxturns", description: t("cmd.turns"), hasParams: true },
];

interface CommandPaletteProps {
  filter: string;
  onSelect: (command: string, executeNow: boolean) => void;
  onClose: () => void;
}

export function CommandPalette({ filter, onSelect, onClose }: CommandPaletteProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const COMMANDS = getCommands();

  // Filter commands
  const filteredCommands = filter
    ? COMMANDS.filter((cmd) =>
        cmd.name.toLowerCase().includes(filter.toLowerCase())
      )
    : COMMANDS;

  // Reset selection when filter changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [filter]);

  // Handle keyboard navigation
  useInput((input, key) => {
    if (key.escape) {
      onClose();
      return;
    }

    if (key.upArrow) {
      setSelectedIndex((prev) => Math.max(0, prev - 1));
      return;
    }

    if (key.downArrow) {
      setSelectedIndex((prev) => Math.min(filteredCommands.length - 1, prev + 1));
      return;
    }

    if (key.return) {
      if (filteredCommands.length > 0) {
        const cmd = filteredCommands[selectedIndex];
        onSelect(cmd.name, !cmd.hasParams);
      } else {
        // No matches - close palette, let Input handle the command
        onClose();
      }
      return;
    }

    if (key.tab && filteredCommands.length > 0) {
      const cmd = filteredCommands[selectedIndex];
      // Tab always just fills in the command, doesn't execute
      onSelect(cmd.name, false);
      return;
    }
  });

  if (filteredCommands.length === 0) {
    return (
      <Box
        flexDirection="column"
        borderStyle="round"
        borderColor="gray"
        paddingX={1}
      >
        <Text dimColor>{t("palette.noMatches")}</Text>
      </Box>
    );
  }

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="green"
      paddingX={1}
    >
      <Box marginBottom={0}>
        <Text bold color="green">{t("palette.title")}</Text>
        <Text dimColor> {t("palette.hint")}</Text>
      </Box>

      {filteredCommands.map((cmd, index) => {
        const isSelected = index === selectedIndex;
        return (
          <Box key={cmd.name}>
            <Text
              backgroundColor={isSelected ? "green" : undefined}
              color={isSelected ? "black" : "cyan"}
              bold={isSelected}
            >
              {cmd.name.padEnd(12)}
            </Text>
            <Text dimColor={!isSelected}> {cmd.description}</Text>
            {cmd.shortcut && (
              <Text dimColor> [{cmd.shortcut}]</Text>
            )}
          </Box>
        );
      })}
    </Box>
  );
}
