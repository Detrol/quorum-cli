/**
 * Export selector for choosing which discussion to export.
 * Shows the 10 most recent discussions with navigation.
 */

import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { listRecentReports, type ReportFileInfo, type ExportFormat } from "../utils/export.js";
import { t } from "../i18n/index.js";

interface ExportSelectorProps {
  reportDir: string;
  format: ExportFormat;
  onExport: (reportPath: string) => void;
  onCancel: () => void;
}

/**
 * Format a date for display.
 */
function formatDate(date: Date): string {
  return date.toLocaleString("sv-SE", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ExportSelector({ reportDir, format, onExport, onCancel }: ExportSelectorProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [reports, setReports] = useState<ReportFileInfo[]>([]);
  const [loading, setLoading] = useState(true);

  // Load report files asynchronously
  useEffect(() => {
    let mounted = true;
    async function loadReports() {
      try {
        const loadedReports = await listRecentReports(reportDir, 10);
        if (mounted) {
          setReports(loadedReports);
          setLoading(false);
        }
      } catch {
        if (mounted) {
          setReports([]);
          setLoading(false);
        }
      }
    }
    loadReports();
    return () => { mounted = false; };
  }, [reportDir]);

  useInput((input, key) => {
    if (key.escape) {
      onCancel();
      return;
    }

    if (loading) return;

    if (key.upArrow) {
      setSelectedIndex(prev => Math.max(0, prev - 1));
      return;
    }

    if (key.downArrow) {
      setSelectedIndex(prev => Math.min(reports.length - 1, prev + 1));
      return;
    }

    if (key.return && reports.length > 0) {
      onExport(reports[selectedIndex].path);
      return;
    }
  });

  // Loading state
  if (loading) {
    return (
      <Box
        flexDirection="column"
        borderStyle="round"
        borderColor="blue"
        paddingX={2}
        paddingY={1}
      >
        <Text color="blue" bold>{t("export.loading")}</Text>
      </Box>
    );
  }

  // No reports found
  if (reports.length === 0) {
    return (
      <Box
        flexDirection="column"
        borderStyle="round"
        borderColor="yellow"
        paddingX={2}
        paddingY={1}
      >
        <Text color="yellow" bold>{t("export.noDiscussions")}</Text>
        <Box marginTop={1}>
          <Text dimColor>{t("export.noDiscussionsDir", { dir: reportDir })}</Text>
        </Box>
        <Box marginTop={1}>
          <Text dimColor>{t("export.close")}</Text>
        </Box>
      </Box>
    );
  }

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="blue"
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text bold color="blue">
          {t("export.title", { format: format.toUpperCase() })}
        </Text>
      </Box>

      <Box marginBottom={1}>
        <Text dimColor>{t("export.selectPrompt")}</Text>
      </Box>

      {reports.map((log, index) => {
        const isCursor = index === selectedIndex;
        const methodLabel = log.method.toUpperCase();

        return (
          <Box key={log.path} flexDirection="column">
            <Box>
              <Text
                backgroundColor={isCursor ? "blue" : undefined}
                color={isCursor ? "white" : undefined}
                bold={isCursor}
              >
                {isCursor ? " > " : "   "}
                {index + 1}. {log.question}
                {log.question.length >= 60 ? "..." : ""}
              </Text>
            </Box>
            <Box marginLeft={5}>
              <Text
                color={isCursor ? "cyan" : "yellow"}
                bold
              >
                [{methodLabel}]
              </Text>
              <Text> </Text>
              <Text
                color={isCursor ? "blue" : "gray"}
                dimColor={!isCursor}
              >
                {formatDate(log.mtime)}
              </Text>
            </Box>
          </Box>
        );
      })}

      <Box marginTop={1}>
        <Text dimColor>
          {t("export.navigation")}
        </Text>
      </Box>
    </Box>
  );
}
