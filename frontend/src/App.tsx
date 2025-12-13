/**
 * Main Quorum application component.
 */

import React, { useEffect, useCallback, useState, useRef } from "react";
import { Box, Text, useApp, useInput } from "ink";
import { writeFileSync } from "node:fs";

// Spinner component
function Spinner({ text }: { text: string }) {
  const [frame, setFrame] = useState(0);
  const frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

  useEffect(() => {
    const timer = setInterval(() => {
      setFrame((f) => (f + 1) % frames.length);
    }, 80);
    return () => clearInterval(timer);
  }, []);

  return (
    <Text color="green">
      {frames[frame]} {text}
    </Text>
  );
}
import { BackendClient } from "./ipc/index.js";
import type { RoleAssignments } from "./ipc/protocol.js";
import { useStore, type DiscussionMethod } from "./store/index.js";
import type { ConfidenceLevel } from "./types/protocol-values.js";
import { Input, Discussion, ModelSelector, MethodSelector, Status, Help, SynthesizerSelector, Header, TeamPreview, ExportSelector, MethodAdvisor } from "./components/index.js";
import { saveDiscussionToDir, exportSpecificLog, type ExportFormat } from "./utils/export.js";
import { setLanguage, t } from "./i18n/index.js";

// Create backend client as singleton
const backend = new BackendClient();

export function App() {
  const { exit } = useApp();
  const [pendingExportFormat, setPendingExportFormat] = useState<ExportFormat>("md");
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [pendingMethodOverride, setPendingMethodOverride] = useState<DiscussionMethod | null>(null);
  const [currentRoleAssignments, setCurrentRoleAssignments] = useState<RoleAssignments | null>(null);
  const roleAssignmentsRef = useRef<RoleAssignments | null>(null);
  const [exportMessage, setExportMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const exportDirRef = useRef<string | null>(null);
  const exportFormatRef = useRef<ExportFormat>("md");

  const {
    viewMode,
    setViewMode,
    inputValue,
    setInputValue,
    selectedModels,
    setSelectedModels,
    discussionMethod,
    setDiscussionMethod,
    synthesizerMode,
    setSynthesizerMode,
    maxTurns,
    setMaxTurns,
    setInputHistory,
    addToHistory,
    navigateHistory,
    setAvailableModels,
    modelsValidating,
    setModelsValidating,
    setValidationProgress,
    markModelValidated,
    markModelInvalid,
    validationProgress,
    backendReady,
    setBackendReady,
    backendError,
    setBackendError,
    isDiscussionRunning,
    startDiscussion,
    addMessage,
    setCurrentPhase,
    setCurrentMethod,
    setTotalPhases,
    setPhaseTransition,
    pauseDiscussion,
    setThinkingModel,
    addCompletedThinking,
    clearCompletedThinking,
    completeDiscussion,
    isDiscussionComplete,
    resetDiscussionState,
    setResumeBackend,
    // Modal states
    showModels,
    showMethods,
    showHelp,
    showSynthesizer,
    showStatus,
    showTeamPreview,
    showExportSelector,
    showAdvisor,
    setShowModels,
    setShowMethods,
    setShowHelp,
    setShowSynthesizer,
    setShowStatus,
    setShowTeamPreview,
    setShowExportSelector,
    setShowAdvisor,
    softReload: storeSoftReload,
    currentDiscussionId,
    setCurrentDiscussionId,
  } = useStore();

  // Soft reload - wraps store's softReload to also cancel backend discussion
  const softReload = useCallback(() => {
    if (isDiscussionRunning) {
      backend.cancelDiscussion();
    }
    storeSoftReload();
  }, [isDiscussionRunning, storeSoftReload]);

  // Connect to backend on mount
  useEffect(() => {
    async function connect() {
      try {
        // Start backend
        await backend.start();

        // Set callback for resuming backend from Discussion component
        setResumeBackend(() => backend.resumeDiscussion());

        // Initialize and get models + user settings + history + config
        await backend.initialize();
        const [modelsResult, userSettings, inputHistory, config] = await Promise.all([
          backend.listModels(),
          backend.getUserSettings(),
          backend.getInputHistory(),
          backend.getConfig(),
        ]);
        setAvailableModels(modelsResult.models);
        setInputHistory(inputHistory);

        // Store config refs
        exportDirRef.current = config.export_dir;
        exportFormatRef.current = (config.export_format as ExportFormat) || "md";
        setLanguage(config.default_language);

        // Restore user settings
        if (userSettings.selected_models?.length) {
          setSelectedModels(userSettings.selected_models);
        }
        if (userSettings.discussion_method) {
          setDiscussionMethod(userSettings.discussion_method);
        }
        if (userSettings.synthesizer_mode) {
          setSynthesizerMode(userSettings.synthesizer_mode);
        }
        if (userSettings.max_turns !== undefined) {
          setMaxTurns(userSettings.max_turns);
        }

        // Settings loaded - show UI
        setBackendReady(true);

        // Signal shell spinner to stop and clear screen for UI
        const signalFile = process.env.QUORUM_SIGNAL_FILE;
        if (signalFile) {
          writeFileSync(signalFile, "ready");
        }
        process.stdout.write('\x1Bc');

        // Mark cached validated models immediately
        const cachedValidated = new Set(modelsResult.validated || []);
        for (const modelId of cachedValidated) {
          markModelValidated(modelId);
        }

        // Find models that need validation (not in cache)
        const allModelIds: string[] = [];
        for (const models of Object.values(modelsResult.models)) {
          for (const model of models) {
            if (!cachedValidated.has(model.id)) {
              allModelIds.push(model.id);
            }
          }
        }

        // Only validate uncached models
        if (allModelIds.length > 0) {
          setModelsValidating(true);
          let sequenceCounter = 0;
          setValidationProgress({ current: 0, total: allModelIds.length, sequence: sequenceCounter++ });

          let completed = 0;
          await Promise.all(
            allModelIds.map(async (modelId) => {
              try {
                const result = await backend.validateModel(modelId);
                if (result.valid) {
                  markModelValidated(modelId);
                } else {
                  markModelInvalid(modelId, result.error || "Validation failed");
                }
              } catch (err) {
                markModelInvalid(modelId, err instanceof Error ? err.message : String(err));
              } finally {
                completed++;
                // Use sequence number to prevent out-of-order updates
                setValidationProgress({ current: completed, total: allModelIds.length, sequence: sequenceCounter++ });
              }
            })
          );

          setModelsValidating(false);
          setValidationProgress(null);
        }
      } catch (err) {
        setBackendError(err instanceof Error ? err.message : String(err));
      }
    }

    // Helper to check if an event belongs to the current discussion
    // Events from cancelled/old discussions should be ignored
    const isStaleEvent = (eventDiscussionId?: string): boolean => {
      if (!eventDiscussionId) return false; // No ID = old backend, accept all
      const currentId = useStore.getState().currentDiscussionId;
      if (!currentId) return false; // No current discussion, accept all
      return eventDiscussionId !== currentId;
    };

    // Define event handlers for cleanup
    const handlePhaseComplete = (params: {
      discussion_id?: string;
      completed_phase: number;
      next_phase: number;
      next_phase_message_key?: string;
      next_phase_params?: Record<string, string>;
      method?: string;
    }) => {
      if (isStaleEvent(params.discussion_id)) return;
      // Backend signals phase is complete - pause and wait for Enter
      setPhaseTransition(params.completed_phase, params.next_phase);
      pauseDiscussion();
    };

    const handlePhaseStart = (params: {
      discussion_id?: string;
      phase: number;
      message_key: string;
      params?: Record<string, string>;
      method?: "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
      total_phases?: number;
    }) => {
      // On phase 1, set the discussion ID for filtering subsequent events
      if (params.phase === 1 && params.discussion_id) {
        setCurrentDiscussionId(params.discussion_id);
      }

      // Filter out events from old/cancelled discussions
      const state = useStore.getState();
      if (params.discussion_id && state.currentDiscussionId && params.discussion_id !== state.currentDiscussionId) {
        return; // Ignore stale event
      }

      // Set method and total phases on first phase
      if (params.method) setCurrentMethod(params.method);
      if (params.total_phases) setTotalPhases(params.total_phases);

      // Inject discussion header as first message on phase 1
      if (params.phase === 1) {
        addMessage({
          type: "discussion_header",
          headerMethod: params.method || state.discussionMethod,
          headerModels: state.selectedModels,
          headerRoleAssignments: roleAssignmentsRef.current || undefined,
        });
      }

      // Phase marker just gets added - pause already happened via phase_complete
      setCurrentPhase(params.phase);
      addMessage({ type: "phase", phase: params.phase, phaseMessageKey: params.message_key, phaseParams: params.params });
      // Clear completed thinking for new phase
      clearCompletedThinking();
    };
    const handleThinking = (params: { discussion_id?: string; model: string }) => {
      if (isStaleEvent(params.discussion_id)) return;
      setThinkingModel(params.model);
    };
    const handleThinkingComplete = (params: { discussion_id?: string; model: string }) => {
      if (isStaleEvent(params.discussion_id)) return;
      addCompletedThinking(params.model);
    };
    const handleAnswer = (params: { discussion_id?: string; source: string; content: string }) => {
      if (isStaleEvent(params.discussion_id)) return;
      addMessage({ type: "answer", source: params.source, content: params.content });
    };
    const handleCritique = (params: { discussion_id?: string; source: string; agreements: string; disagreements: string; missing: string }) => {
      if (isStaleEvent(params.discussion_id)) return;
      addMessage({ type: "critique", source: params.source, agreements: params.agreements, disagreements: params.disagreements, missing: params.missing });
    };
    const handleChat = (params: {
      discussion_id?: string;
      source: string;
      content: string;
      role?: "FOR" | "AGAINST" | "ADVOCATE" | "DEFENDER" | "QUESTIONER" | "RESPONDENT" | "PANELIST" | "IDEATOR" | "EVALUATOR" | null;
      round_type?: "opening" | "rebuttal" | "closing" | null;
      method?: "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
    }) => {
      if (isStaleEvent(params.discussion_id)) return;
      // For Oxford mode: inject round header if round changed
      if (params.method === "oxford" && params.round_type) {
        const messages = useStore.getState().messages;
        const lastChatMsg = [...messages].reverse().find(m => m.type === "chat");
        if (!lastChatMsg || lastChatMsg.roundType !== params.round_type) {
          addMessage({
            type: "round_header",
            roundType: params.round_type as "opening" | "rebuttal" | "closing",
          });
        }
      }
      addMessage({
        type: "chat",
        source: params.source,
        content: params.content,
        role: params.role,
        roundType: params.round_type,
        method: params.method,
      });
    };
    const handlePosition = (params: { discussion_id?: string; source: string; position: string; confidence: ConfidenceLevel }) => {
      if (isStaleEvent(params.discussion_id)) return;
      addMessage({ type: "position", source: params.source, position: params.position, confidence: params.confidence });
    };
    const handleSynthesis = (params: { discussion_id?: string; consensus: string; synthesis: string; differences: string; synthesizer_model: string; confidence_breakdown: Record<string, number>; method?: string }) => {
      if (isStaleEvent(params.discussion_id)) return;
      addMessage({ type: "synthesis", consensus: params.consensus, synthesis: params.synthesis, differences: params.differences, synthesizerModel: params.synthesizer_model, confidenceBreakdown: params.confidence_breakdown, method: params.method as DiscussionMethod | undefined });

      // Auto-save to reports directory
      try {
        const state = useStore.getState();
        if (state.currentQuestion) {
          // Use setTimeout to ensure message is added to store first
          setTimeout(async () => {
            const updatedState = useStore.getState();
            const projectRoot = process.cwd().replace(/\/frontend$/, "");
            await saveDiscussionToDir({
              question: updatedState.currentQuestion!,
              messages: updatedState.messages,
              method: updatedState.discussionMethod,
              models: updatedState.selectedModels,
            }, `${projectRoot}/reports`);
          }, 100);
        }
      } catch (err) {
        // Silently fail - don't interrupt the discussion for logging errors
      }
    };
    const handleComplete = (params: { discussion_id?: string }) => {
      if (isStaleEvent(params.discussion_id)) return;
      completeDiscussion();
    };
    const handleError = (params: { discussion_id?: string; error: string }) => {
      if (isStaleEvent(params.discussion_id)) return;
      setBackendError(params.error);
    };
    const handleCancelled = (params: { discussion_id?: string }) => {
      // Don't filter stale events for cancellation - always acknowledge
      /* App will restart via ESC/Ctrl+R */
    };

    // Register handlers
    backend.onEvent("phase_complete", handlePhaseComplete);
    backend.onEvent("phase_start", handlePhaseStart);
    backend.onEvent("thinking", handleThinking);
    backend.onEvent("thinking_complete", handleThinkingComplete);
    backend.onEvent("independent_answer", handleAnswer);
    backend.onEvent("critique", handleCritique);
    backend.onEvent("chat_message", handleChat);
    backend.onEvent("final_position", handlePosition);
    backend.onEvent("synthesis", handleSynthesis);
    backend.onEvent("discussion_complete", handleComplete);
    backend.onEvent("discussion_error", handleError);
    backend.onEvent("discussion_cancelled", handleCancelled);

    connect();

    return () => {
      // Cleanup event listeners
      backend.offEvent("phase_complete", handlePhaseComplete);
      backend.offEvent("phase_start", handlePhaseStart);
      backend.offEvent("thinking", handleThinking);
      backend.offEvent("thinking_complete", handleThinkingComplete);
      backend.offEvent("independent_answer", handleAnswer);
      backend.offEvent("critique", handleCritique);
      backend.offEvent("chat_message", handleChat);
      backend.offEvent("final_position", handlePosition);
      backend.offEvent("synthesis", handleSynthesis);
      backend.offEvent("discussion_complete", handleComplete);
      backend.offEvent("discussion_error", handleError);
      backend.offEvent("discussion_cancelled", handleCancelled);
      backend.stop();
    };
  }, []);

  // Track if initial settings load is complete
  const settingsLoaded = useRef(false);
  useEffect(() => {
    if (backendReady && !modelsValidating) {
      settingsLoaded.current = true;
    }
  }, [backendReady, modelsValidating]);

  // Save settings when they change (after initial load)
  useEffect(() => {
    if (!settingsLoaded.current) return;
    backend.saveUserSettings({ selected_models: selectedModels });
  }, [selectedModels]);

  useEffect(() => {
    if (!settingsLoaded.current) return;
    backend.saveUserSettings({ discussion_method: discussionMethod });
  }, [discussionMethod]);

  useEffect(() => {
    if (!settingsLoaded.current) return;
    backend.saveUserSettings({ synthesizer_mode: synthesizerMode });
  }, [synthesizerMode]);

  useEffect(() => {
    if (!settingsLoaded.current) return;
    backend.saveUserSettings({ max_turns: maxTurns });
  }, [maxTurns]);

  // Start discussion with optional role assignments and method override
  const startDiscussionWithOptions = useCallback(
    async (question: string, roleAssignments?: RoleAssignments, methodOverride?: DiscussionMethod) => {
      // Add to history (both local and backend)
      addToHistory(question);
      backend.addToInputHistory(question);

      // Clear role assignments ref if not provided (standard mode)
      if (!roleAssignments) {
        roleAssignmentsRef.current = null;
      }

      startDiscussion(question);
      setInputValue("");

      try {
        await backend.runDiscussion({
          question,
          model_ids: selectedModels,
          options: {
            method: methodOverride || useStore.getState().discussionMethod,
            role_assignments: roleAssignments,
          },
        });
      } catch (err) {
        // Reset discussion state on error (e.g., "discussion already in progress")
        resetDiscussionState();
        setBackendError(err instanceof Error ? err.message : String(err));
      }
    },
    [selectedModels, resetDiscussionState]
  );

  // Method requirements for validation
  const METHOD_REQUIREMENTS: Record<DiscussionMethod, { min: number; evenOnly: boolean }> = {
    standard: { min: 2, evenOnly: false },
    oxford: { min: 2, evenOnly: true },
    advocate: { min: 3, evenOnly: false },
    socratic: { min: 2, evenOnly: false },
    delphi: { min: 3, evenOnly: false },
    brainstorm: { min: 2, evenOnly: false },
    tradeoff: { min: 2, evenOnly: false },
  };

  // Start inline method discussion (e.g., /oxford Why is the sky blue?)
  const startInlineMethodDiscussion = useCallback(
    async (method: DiscussionMethod, question: string) => {
      if (selectedModels.length < 2) {
        setBackendError(t("app.error.selectModels"));
        return;
      }

      // Validate method requirements
      const req = METHOD_REQUIREMENTS[method];
      if (selectedModels.length < req.min) {
        setBackendError(t("app.error.methodMin", { method: method.charAt(0).toUpperCase() + method.slice(1), min: String(req.min) }));
        return;
      }
      if (req.evenOnly && selectedModels.length % 2 !== 0) {
        setBackendError(t("app.error.oxfordEven"));
        return;
      }

      // For Oxford, Advocate, Socratic - show team preview with method override
      if (method === "oxford" || method === "advocate" || method === "socratic") {
        try {
          const assignments = await backend.getRoleAssignments(method, selectedModels);
          if (assignments) {
            setPendingQuestion(question);
            setPendingMethodOverride(method);
            setCurrentRoleAssignments(assignments);
            setShowTeamPreview(true);
            return;
          }
        } catch (err) {
          console.error("Failed to get role assignments:", err);
        }
      }

      // Start directly with method override
      await startDiscussionWithOptions(question, undefined, method);
    },
    [selectedModels, startDiscussionWithOptions]
  );

  // Handle commands
  const handleCommand = useCallback(
    (command: string) => {
      const parts = command.slice(1).trim().split(/\s+/);
      const cmd = parts[0]?.toLowerCase();
      const rest = parts.slice(1).join(" ").trim();

      // Check for inline method syntax: /method question
      const inlineMethods: DiscussionMethod[] = ["standard", "oxford", "advocate", "socratic", "delphi", "brainstorm", "tradeoff"];
      if (inlineMethods.includes(cmd as DiscussionMethod) && rest) {
        startInlineMethodDiscussion(cmd as DiscussionMethod, rest);
        return;
      }

      switch (cmd) {
        case "models":
          setShowModels(true);
          break;

        case "status":
          setShowStatus(true);
          break;

        case "quit":
        case "exit":
          backend.stop();
          exit();
          break;

        case "clear":
          useStore.getState().clearMessages();
          setViewMode("input");
          break;

        case "help":
          setShowHelp(true);
          break;

        case "method":
          setShowMethods(true);
          break;

        case "synthesizer":
          setShowSynthesizer(true);
          break;

        case "export": {
          // Parse format argument: /export [md|text|pdf|json]
          const formatArg = parts[1]?.toLowerCase();
          const validFormats: ExportFormat[] = ["md", "text", "pdf", "json"];

          if (formatArg && !validFormats.includes(formatArg as ExportFormat)) {
            setExportMessage({ type: "error", text: t("app.error.exportFormat") });
            setTimeout(() => setExportMessage(null), 3000);
            break;
          }

          // Set format and show selector
          setPendingExportFormat(formatArg ? (formatArg as ExportFormat) : exportFormatRef.current);
          setShowExportSelector(true);
          break;
        }
      }
    },
    [exit, selectedModels, startInlineMethodDiscussion]
  );

  // Handle question submission
  const handleSubmit = useCallback(
    async (question: string) => {
      if (selectedModels.length < 2) {
        setBackendError(t("app.error.selectModels"));
        return;
      }

      const method = useStore.getState().discussionMethod;

      // For Oxford, Advocate, and Socratic modes, show team preview first
      if (method === "oxford" || method === "advocate" || method === "socratic") {
        try {
          const assignments = await backend.getRoleAssignments(method, selectedModels);
          if (assignments) {
            setPendingQuestion(question);
            setCurrentRoleAssignments(assignments);
            setShowTeamPreview(true);
            return;
          }
        } catch (err) {
          // If getting role assignments fails, just continue without preview
          console.error("Failed to get role assignments:", err);
        }
      }

      // For standard or if role assignment fetch failed, start directly
      await startDiscussionWithOptions(question);
    },
    [selectedModels, startDiscussionWithOptions]
  );

  // Handle team preview confirm
  const handleTeamConfirm = useCallback(
    async (assignments: RoleAssignments) => {
      process.stdout.write('\x1b[2J\x1b[3J\x1b[H');
      setShowTeamPreview(false);
      // Store role assignments in ref for header injection
      roleAssignmentsRef.current = assignments;
      if (pendingQuestion) {
        await startDiscussionWithOptions(pendingQuestion, assignments, pendingMethodOverride || undefined);
      }
      setPendingQuestion(null);
      setPendingMethodOverride(null);
      setCurrentRoleAssignments(null);
    },
    [pendingQuestion, pendingMethodOverride, startDiscussionWithOptions]
  );

  // Handle team preview cancel
  const handleTeamCancel = useCallback(() => {
    setPendingQuestion(null);
    setPendingMethodOverride(null);
    setCurrentRoleAssignments(null);
    softReload();
  }, [softReload]);

  // Handle export selection
  const handleExportSelect = useCallback(async (logPath: string) => {
    try {
      const projectRoot = process.cwd().replace(/\/frontend$/, "");
      const exportPath = await exportSpecificLog(logPath, pendingExportFormat, `${projectRoot}/export`);
      setExportMessage({ type: "success", text: t("app.success.exported", { path: exportPath }) });
      setTimeout(() => setExportMessage(null), 5000);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setExportMessage({ type: "error", text: errMsg });
      setTimeout(() => setExportMessage(null), 3000);
    }
    softReload();
  }, [pendingExportFormat, softReload]);

  // Handle export cancel
  const handleExportCancel = useCallback(() => {
    softReload();
  }, [softReload]);

  // Handle advisor open (Tab key)
  const handleAdvisorOpen = useCallback(() => {
    // Only show if we have validated models (selectedModels only contains validated ones)
    if (selectedModels.length > 0) {
      setShowAdvisor(true);
    }
  }, [selectedModels]);

  // Handle advisor method selection (special case - preserves question in input)
  const handleAdvisorSelect = useCallback((method: DiscussionMethod, question: string) => {
    setDiscussionMethod(method);
    // Clear screen and close modals, but preserve the question
    process.stdout.write('\x1b[2J\x1b[3J\x1b[H');
    useStore.setState({
      showAdvisor: false,
      inputValue: question,
    });
  }, [setDiscussionMethod]);

  // Handle advisor cancel
  const handleAdvisorCancel = useCallback(() => {
    softReload();
  }, [softReload]);

  // Global key handler
  useInput((input, key) => {
    // Ctrl+R = Soft reload (always available)
    if (key.ctrl && input === 'r') {
      softReload();
      return;
    }

    // ESC during discussion = Soft reload to exit discussion
    if (key.escape && (isDiscussionRunning || isDiscussionComplete)) {
      softReload();
    }
  });

  // Render nothing while backend starts (shell spinner handles this)
  if (!backendReady) {
    return null;
  }

  // Render loading state only for model validation
  if (modelsValidating) {
    const loadingText = validationProgress
      ? t("app.loading.validating", { current: String(validationProgress.current), total: String(validationProgress.total) })
      : t("app.loading.models");
    return (
      <Box flexDirection="column" padding={1}>
        <Spinner text={loadingText} />
        {backendError && (
          <Text color="red">{t("app.error.generic", { error: backendError })}</Text>
        )}
      </Box>
    );
  }

  return (
    <Box flexDirection="column">
      {/* Header */}
      <Box marginBottom={1}>
        <Header />
      </Box>

      {/* Error display */}
      {backendError && (
        <Box marginBottom={1}>
          <Text color="red">⚠ {backendError}</Text>
        </Box>
      )}

      {/* Export message */}
      {exportMessage && (
        <Box marginBottom={1}>
          <Text color={exportMessage.type === "success" ? "green" : "red"}>
            {exportMessage.type === "success" ? "✓" : "⚠"} {exportMessage.text}
          </Text>
        </Box>
      )}

      {/* Model Selector Overlay */}
      {showModels && (
        <Box marginBottom={1}>
          <ModelSelector onSelect={softReload} />
        </Box>
      )}

      {/* Method Selector Overlay */}
      {showMethods && (
        <Box marginBottom={1}>
          <MethodSelector onSelect={softReload} />
        </Box>
      )}

      {/* Status Overlay */}
      {showStatus && (
        <Box marginBottom={1}>
          <Status />
        </Box>
      )}

      {/* Help Overlay */}
      {showHelp && (
        <Box marginBottom={1}>
          <Help />
        </Box>
      )}

      {/* Synthesizer Overlay */}
      {showSynthesizer && (
        <Box marginBottom={1}>
          <SynthesizerSelector onSelect={softReload} />
        </Box>
      )}

      {/* Team Preview Overlay (Oxford/Advocate/Socratic) */}
      {showTeamPreview && currentRoleAssignments && (
        <Box marginBottom={1}>
          <TeamPreview
            assignments={currentRoleAssignments}
            method={discussionMethod}
            onConfirm={handleTeamConfirm}
            onCancel={handleTeamCancel}
          />
        </Box>
      )}

      {/* Export Selector Overlay */}
      {showExportSelector && (
        <Box marginBottom={1}>
          <ExportSelector
            reportDir={`${process.cwd().replace(/\/frontend$/, "")}/reports`}
            format={pendingExportFormat}
            onExport={handleExportSelect}
            onCancel={handleExportCancel}
          />
        </Box>
      )}

      {/* Method Advisor Overlay */}
      {showAdvisor && (
        <Box marginBottom={1}>
          <MethodAdvisor
            onSelect={handleAdvisorSelect}
            onCancel={handleAdvisorCancel}
            analyzeQuestion={(question) => backend.analyzeQuestion(question)}
          />
        </Box>
      )}

      {/* Main content */}
      {!showModels && !showMethods && !showStatus && !showHelp && !showSynthesizer && !showExportSelector && !showAdvisor && (
        <>
          {viewMode === "discussion" ? (
            <Discussion />
          ) : (
            <Box flexDirection="column">
              {selectedModels.length === 0 && (
                <Box marginBottom={1}>
                  <Text dimColor>
                    {t("app.hint.welcome")}
                  </Text>
                </Box>
              )}
            </Box>
          )}
        </>
      )}

      {/* Input & Footer - only show when not in discussion and not showing completion */}
      {!isDiscussionRunning && !isDiscussionComplete && (
        <>
          <Box marginTop={1}>
            <Input
              value={inputValue}
              onChange={setInputValue}
              onSubmit={handleSubmit}
              onCommand={handleCommand}
              onHistoryNavigate={navigateHistory}
              onAdvisorOpen={handleAdvisorOpen}
              disabled={showModels || showMethods || showStatus || showHelp || showSynthesizer || showTeamPreview || showExportSelector || showAdvisor}
              placeholder={
                selectedModels.length < 2
                  ? t("app.placeholder.selectModels")
                  : t("app.placeholder.askQuestion")
              }
            />
          </Box>

          <Box marginTop={1}>
            <Text dimColor>
              {t("app.statusBar.commands")}
            </Text>
          </Box>
        </>
      )}

      {/* Footer during discussion */}
      {isDiscussionRunning && !isDiscussionComplete && (
        <Box marginTop={1}>
          <Text dimColor>
            {t("app.statusBar.running")}
          </Text>
        </Box>
      )}
    </Box>
  );
}
