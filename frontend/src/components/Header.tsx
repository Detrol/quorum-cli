/**
 * Header component with app info, settings overview, and tips.
 */

import React from "react";
import { Box, Text } from "ink";
import { useStore } from "../store/index.js";
import { t } from "../i18n/index.js";

const VERSION = "1.1.4";

// Width of each half of the two-column layout, in terminal columns
const COLUMN_WIDTH = 22;

// Wide characters (CJK, hangul, fullwidth forms) occupy two terminal columns
const WIDE_RE = /[\u1100-\u115F\u2E80-\u303E\u3041-\u33FF\u3400-\u4DBF\u4E00-\u9FFF\uA000-\uA4CF\uAC00-\uD7A3\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFF60\uFFE0-\uFFE6]/;

function displayWidth(s: string): number {
  let w = 0;
  for (const ch of s) w += WIDE_RE.test(ch) ? 2 : 1;
  return w;
}

function fitWidth(s: string, max: number): string {
  if (displayWidth(s) <= max) return s;
  let out = "";
  let w = 0;
  for (const ch of s) {
    const cw = WIDE_RE.test(ch) ? 2 : 1;
    if (w + cw > max - 1) break;
    out += ch;
    w += cw;
  }
  return out + "…";
}

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
  const modelList = fitWidth(modelNames.join(", "), COLUMN_WIDTH);

  // Localized method name, falling back to the raw method id when untranslated
  const methodKey = `method.${discussionMethod}.name` as const;
  const translatedMethod = t(methodKey);
  const methodLabel = fitWidth(
    translatedMethod === methodKey ? discussionMethod : translatedMethod,
    COLUMN_WIDTH
  );

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
              <Text>{modelList}</Text>
            ) : (
              <Text dimColor italic>
                {t("status.none")}
              </Text>
            )}
          </Box>
          <Box>
            <Text color="cyan">{t("status.method")}</Text>
            <Text color="magenta">{methodLabel}</Text>
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
