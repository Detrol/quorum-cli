/**
 * Help display component.
 */

import React from "react";
import { Box, Text } from "ink";
import { t } from "../i18n/index.js";

export function Help() {
  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="yellow"
      paddingX={2}
      paddingY={1}
    >
      <Text bold color="yellow">
        {t("help.title")}
      </Text>

      <Box marginTop={1} flexDirection="column">
        <Text bold dimColor>{t("help.commands")}</Text>
        <Box>
          <Text color="cyan">{"/models".padEnd(12)}</Text>
          <Text>{t("cmd.models")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{"/method".padEnd(12)}</Text>
          <Text>{t("cmd.method")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{"/synthesizer".padEnd(12)}</Text>
          <Text>{t("cmd.synthesizer")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{"/status".padEnd(12)}</Text>
          <Text>{t("cmd.status")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{"/export".padEnd(12)}</Text>
          <Text>{t("cmd.export")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{"/clear".padEnd(12)}</Text>
          <Text>{t("cmd.clear")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{"/quit".padEnd(12)}</Text>
          <Text>{t("cmd.quit")}</Text>
        </Box>
      </Box>

      <Box marginTop={1} flexDirection="column">
        <Text bold dimColor>{t("help.keyboard")}</Text>
        <Box>
          <Text color="cyan">{"Esc".padEnd(12)}</Text>
          <Text>{t("help.key.esc")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{"Ctrl+C".padEnd(12)}</Text>
          <Text>{t("help.key.ctrlC")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{String.fromCharCode(0x2191) + String.fromCharCode(0x2193).padEnd(10)}</Text>
          <Text>{t("help.key.arrows")}</Text>
        </Box>
        <Box>
          <Text color="cyan">{"Enter".padEnd(12)}</Text>
          <Text>{t("help.key.enter")}</Text>
        </Box>
      </Box>

      <Box marginTop={1}>
        <Text dimColor>{t("help.close")}</Text>
      </Box>
    </Box>
  );
}
