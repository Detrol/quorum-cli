/**
 * Header component with app info, settings overview, and tips.
 */

import React from "react";
import { Box, Text } from "ink";
import { useStore } from "../store/index.js";
import { t } from "../i18n/index.js";

const VERSION = "1.0.0";

export function Header() {
  const { selectedModels, discussionMethod, availableModels } = useStore();

  // Get display names for selected models
  const getModelName = (modelId: string): string => {
    for (const models of Object.values(availableModels)) {
      const model = models.find((m) => m.id === modelId);
      if (model?.display_name) return model.display_name;
    }
    // Fallback: extract readable name from ID
    return modelId.split("/").pop()?.split(":")[0] || modelId;
  };

  const modelNames = selectedModels.map(getModelName);

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="green"
      paddingX={2}
      paddingY={0}
    >
      {/* Title row */}
      <Box justifyContent="space-between">
        <Box>
          <Text bold color="green">
            {t("app.title")}
          </Text>
          <Text dimColor> v{VERSION}</Text>
        </Box>
        <Text dimColor>{t("app.subtitle")}</Text>
      </Box>

      {/* Divider */}
      <Box marginY={0}>
        <Text dimColor>{"─".repeat(70)}</Text>
      </Box>

      {/* Two-column layout */}
      <Box>
        {/* Left column - Current settings */}
        <Box flexDirection="column" width="50%">
          <Box>
            <Text color="cyan">{t("status.models")}</Text>
            {modelNames.length > 0 ? (
              <Text>{modelNames.join(", ")}</Text>
            ) : (
              <Text dimColor italic>
                {t("status.none")}
              </Text>
            )}
          </Box>
          <Box>
            <Text color="cyan">{t("status.method")}</Text>
            <Text color="magenta">{discussionMethod}</Text>
          </Box>
        </Box>

        {/* Right column - Quick tips */}
        <Box flexDirection="column" width="50%">
          <Text dimColor bold>
            {t("header.quickCommands")}
          </Text>
          <Text dimColor>
            {t("header.cmdModels")}
          </Text>
          <Text dimColor>
            {t("header.cmdMethod")}
          </Text>
          <Text dimColor>
            {t("header.cmdExport")}
          </Text>
          <Text dimColor>
            {t("header.cmdHelp")}
          </Text>
        </Box>
      </Box>
    </Box>
  );
}
