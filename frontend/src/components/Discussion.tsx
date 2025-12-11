/**
 * Discussion view showing all messages.
 */

import React, { useEffect, useMemo } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { Message, getModelDisplayName } from "./Message.js";
import { t } from "../i18n/index.js";
import { getPhaseNames } from "../utils/phases.js";
import { useTerminalSpinner } from "../hooks/useSpinner.js";

export function Discussion() {
  const {
    messages,
    currentQuestion,
    isDiscussionRunning,
    isDiscussionComplete,
    currentPhase,
    previousPhase,
    nextPhase,
    currentMethod,
    isPaused,
    thinkingModel,
    completedThinking,
    availableModels,
    resumeDiscussion,
    resumeBackend,
  } = useStore();

  // Get display name for thinking model (memoized to prevent re-computation)
  const thinkingDisplayName = useMemo(
    () => thinkingModel ? getModelDisplayName(thinkingModel, availableModels) : "",
    [thinkingModel, availableModels]
  );

  // Handle Enter/Space to continue when paused
  useInput(async (input, key) => {
    if (isPaused && (key.return || input === " ")) {
      // Signal backend to continue to next phase
      if (resumeBackend) {
        await resumeBackend();
      }
      // Update UI state
      resumeDiscussion();
    }
  });

  // Get phase name based on current method
  const PHASE_NAMES = getPhaseNames();
  const methodPhases = PHASE_NAMES[currentMethod] || PHASE_NAMES.standard;
  const phaseName = methodPhases[currentPhase] || `Phase ${currentPhase}`;
  const previousPhaseName = methodPhases[previousPhase] || `Phase ${previousPhase}`;
  const nextPhaseName = methodPhases[nextPhase] || `Phase ${nextPhase}`;

  // Thinking spinner text
  const thinkingText = useMemo(
    () => t("thinkingInProgress", { model: thinkingDisplayName }),
    [thinkingDisplayName]
  );

  // Phase progress spinner text
  const phaseProgressText = useMemo(
    () =>
      currentPhase === 0
        ? t("msg.startingDiscussion")
        : t("msg.phaseInProgress", { phase: String(currentPhase), name: phaseName }),
    [currentPhase, phaseName]
  );

  // Thinking spinner (yellow) - shows when a model is thinking
  useTerminalSpinner({
    text: thinkingText,
    color: "yellow",
    active: !!thinkingModel && isDiscussionRunning && !isPaused,
    linesUp: 1,
  });

  // Phase progress spinner (green) - shows when no model is actively thinking
  useTerminalSpinner({
    text: phaseProgressText,
    color: "green",
    active: isDiscussionRunning && !isPaused && !thinkingModel,
    linesUp: 1,
  });

  // Should we show spinner placeholder?
  const showSpinner = isDiscussionRunning && !isPaused;

  // Explicit cleanup when discussion ends - clears any residual spinner text
  // and refreshes terminal for clean Input rendering
  useEffect(() => {
    if (!isDiscussionRunning) {
      // Show cursor
      process.stdout.write('\x1b[?25h');
      // Clear from cursor to end of screen - lets React re-render cleanly
      process.stdout.write('\x1b[J');
    }
  }, [isDiscussionRunning]);

  return (
    <Box flexDirection="column" paddingX={1}>
      {/* Question header */}
      <Box marginBottom={1} borderStyle="single" borderColor="green" paddingX={2}>
        <Text bold color="green">
          {t("msg.question", { question: currentQuestion || "" })}
        </Text>
      </Box>

      {/* Messages */}
      <Box flexDirection="column">
        {messages.map((message, index) => (
          <Message key={`msg-${index}`} message={message} />
        ))}
      </Box>

      {/* Thinking complete notifications */}
      {completedThinking.length > 0 && isDiscussionRunning && !isPaused && (
        <Box flexDirection="column" marginTop={1}>
          {completedThinking.map((modelId) => {
            const displayName = getModelDisplayName(modelId, availableModels);
            return (
              <Box key={modelId} borderStyle="round" borderColor="green" paddingX={1} marginBottom={0}>
                <Text color="green">✓</Text>
                <Text> {t("thinkingComplete", { model: displayName })}</Text>
              </Box>
            );
          })}
        </Box>
      )}

      {/* Pause prompt */}
      {isPaused && (
        <Box marginTop={1}>
          <Box borderStyle="round" borderColor="cyan" paddingX={2} paddingY={0}>
            <Text color="cyan" bold>
              ⏸  {t("msg.pausePrompt", { previousPhase: previousPhaseName, nextPhase: nextPhaseName })}
            </Text>
          </Box>
        </Box>
      )}

      {/* Spinner placeholder - actual spinner is rendered via process.stdout.write above this line */}
      {showSpinner && (
        <Text> </Text>
      )}

      {/* Completion screen */}
      {isDiscussionComplete && (
        <Box marginTop={1} flexDirection="column">
          <Box borderStyle="double" borderColor="green" paddingX={2} paddingY={1} flexDirection="column">
            <Text color="green" bold>
              ✓ {t("msg.discussionComplete")}
            </Text>
            <Box marginTop={1}>
              <Text dimColor>
                {t("msg.pressEscNewDiscussion")}
              </Text>
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}
