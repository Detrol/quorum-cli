/**
 * Method Advisor - AI-powered method recommendation panel.
 * Triggered by Tab key, analyzes a question and recommends the best discussion method.
 */

import React, { useState, useEffect, useCallback } from "react";
import { Box, Text, useInput } from "ink";
import type { DiscussionMethod } from "../store/index.js";
import type { MethodRecommendation, AnalyzeQuestionResult } from "../ipc/protocol.js";
import { t } from "../i18n/index.js";
import { SPINNER_FRAMES, SPINNER_INTERVAL_MS } from "../hooks/useSpinner.js";

interface MethodAdvisorProps {
  onSelect: (method: DiscussionMethod, question: string) => void;
  onCancel: () => void;
  analyzeQuestion: (question: string) => Promise<AnalyzeQuestionResult>;
}

// Method display info
const METHOD_INFO: Record<string, { name: string; color: string }> = {
  standard: { name: "Standard", color: "white" },
  oxford: { name: "Oxford Debate", color: "yellow" },
  advocate: { name: "Devil's Advocate", color: "red" },
  socratic: { name: "Socratic", color: "cyan" },
  delphi: { name: "Delphi", color: "magenta" },
  brainstorm: { name: "Brainstorm", color: "green" },
  tradeoff: { name: "Tradeoff", color: "blue" },
};

// Spinner component
function Spinner({ text }: { text: string }) {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setFrame((f) => (f + 1) % SPINNER_FRAMES.length);
    }, SPINNER_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);

  return (
    <Text color="cyan">
      {SPINNER_FRAMES[frame]} {text}
    </Text>
  );
}

type Phase = "input" | "analyzing" | "results";

export function MethodAdvisor({ onSelect, onCancel, analyzeQuestion }: MethodAdvisorProps) {
  const [phase, setPhase] = useState<Phase>("input");
  const [question, setQuestion] = useState("");
  const [cursorPosition, setCursorPosition] = useState(0);
  const [advisorModel, setAdvisorModel] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<{
    primary: MethodRecommendation;
    alternatives: MethodRecommendation[];
  } | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Get all recommendations as a flat list for navigation
  const allRecommendations = recommendations
    ? [recommendations.primary, ...recommendations.alternatives]
    : [];

  const handleAnalyze = useCallback(async () => {
    if (!question.trim()) return;

    setPhase("analyzing");
    setError(null);

    try {
      const result = await analyzeQuestion(question);
      setAdvisorModel(result.advisor_model);
      setRecommendations(result.recommendations);
      setPhase("results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setPhase("input");
    }
  }, [question, analyzeQuestion]);

  useInput((input, key) => {
    if (key.escape) {
      onCancel();
      return;
    }

    if (phase === "input") {
      // Handle Enter to analyze
      if (key.return && question.trim()) {
        handleAnalyze();
        return;
      }

      // Handle Backspace
      if (key.backspace || key.delete) {
        if (cursorPosition > 0) {
          const newValue =
            question.slice(0, cursorPosition - 1) + question.slice(cursorPosition);
          setQuestion(newValue);
          setCursorPosition(cursorPosition - 1);
        }
        return;
      }

      // Handle arrow keys for cursor
      if (key.leftArrow) {
        setCursorPosition(Math.max(0, cursorPosition - 1));
        return;
      }

      if (key.rightArrow) {
        setCursorPosition(Math.min(question.length, cursorPosition + 1));
        return;
      }

      // Handle regular character input
      if (input && !key.ctrl && !key.meta && !key.tab) {
        const newValue =
          question.slice(0, cursorPosition) + input + question.slice(cursorPosition);
        setQuestion(newValue);
        setCursorPosition(cursorPosition + input.length);
      }
    } else if (phase === "results") {
      // Navigate recommendations
      if (key.upArrow) {
        setSelectedIndex(Math.max(0, selectedIndex - 1));
        return;
      }

      if (key.downArrow) {
        setSelectedIndex(Math.min(allRecommendations.length - 1, selectedIndex + 1));
        return;
      }

      // Select recommendation
      if (key.return) {
        const selected = allRecommendations[selectedIndex];
        if (selected) {
          onSelect(selected.method as DiscussionMethod, question);
        }
        return;
      }

      // Go back to input
      if (key.backspace) {
        setPhase("input");
        setRecommendations(null);
        setSelectedIndex(0);
        return;
      }
    }
  });

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="cyan"
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text bold color="cyan">
          {t("advisor.title")}
        </Text>
      </Box>

      {phase === "input" && (
        <>
          <Box marginBottom={1}>
            <Text dimColor>{t("advisor.prompt")}</Text>
          </Box>

          <Box>
            <Text color="cyan" bold>
              {"› "}
            </Text>
            {question ? (
              <>
                <Text>{question.slice(0, cursorPosition)}</Text>
                <Text backgroundColor="white" color="black">
                  {question[cursorPosition] || " "}
                </Text>
                <Text>{question.slice(cursorPosition + 1)}</Text>
              </>
            ) : (
              <Text backgroundColor="white" color="black">
                {" "}
              </Text>
            )}
          </Box>

          {error && (
            <Box marginTop={1}>
              <Text color="red">{t("advisor.error")}: {error}</Text>
            </Box>
          )}

          <Box marginTop={1}>
            <Text dimColor>{t("advisor.inputHint")}</Text>
          </Box>
        </>
      )}

      {phase === "analyzing" && (
        <Box>
          <Spinner text={t("advisor.analyzing", { model: advisorModel || "AI" })} />
        </Box>
      )}

      {phase === "results" && recommendations && (
        <>
          <Box marginBottom={1}>
            <Text dimColor>"{question}"</Text>
          </Box>

          <Box marginBottom={1}>
            <Text bold>{t("advisor.recommended")}</Text>
          </Box>

          {allRecommendations.map((rec, index) => {
            const info = METHOD_INFO[rec.method] || { name: rec.method, color: "white" };
            const isSelected = index === selectedIndex;
            const isPrimary = index === 0;

            return (
              <Box key={rec.method} flexDirection="column" marginBottom={isPrimary ? 1 : 0}>
                <Box>
                  <Text
                    backgroundColor={isSelected ? "cyan" : undefined}
                    color={isSelected ? "black" : info.color}
                    bold={isPrimary}
                  >
                    {isPrimary ? "● " : "○ "}
                    {info.name} ({rec.confidence}%)
                  </Text>
                </Box>
                {(isPrimary || isSelected) && (
                  <Box marginLeft={2}>
                    <Text dimColor wrap="wrap">
                      {rec.reason}
                    </Text>
                  </Box>
                )}
              </Box>
            );
          })}

          <Box marginTop={1}>
            <Text dimColor>
              {t("advisor.navigation")}
            </Text>
          </Box>

          {advisorModel && (
            <Box marginTop={1}>
              <Text dimColor italic>
                {t("advisor.analyzedBy", { model: advisorModel })}
              </Text>
            </Box>
          )}
        </>
      )}
    </Box>
  );
}
