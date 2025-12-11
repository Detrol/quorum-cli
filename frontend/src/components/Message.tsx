/**
 * Message display components for different message types.
 */

import React, { useMemo } from "react";
import { Box, Text } from "ink";
import { useStore, type DiscussionMessage, type DiscussionMethod } from "../store/index.js";
import { Markdown } from "../utils/markdownTerminal.js";
import { t, type TranslationKey } from "../i18n/index.js";
import { getPhaseNames } from "../utils/phases.js";
import { getModelDisplayName } from "../utils/modelName.js";

// Re-export for backward compatibility (used by Discussion.tsx)
export { getModelDisplayName } from "../utils/modelName.js";

function getProviderColor(source: string): string {
  const s = source.toLowerCase();
  // OpenAI models
  if (s.includes("gpt") || s.includes("o1") || s.includes("o3") || s.includes("o4")) {
    return "green";
  }
  // Anthropic models
  if (s.includes("claude")) {
    return "yellow";
  }
  // Google models
  if (s.includes("gemini")) {
    return "blue";
  }
  return "white";
}

/**
 * Get border color based on debate role.
 * Takes precedence over provider color during team debates.
 */
function getRoleColor(role: string | null | undefined): string | null {
  switch (role) {
    case "FOR":
      return "green";
    case "AGAINST":
      return "red";
    case "ADVOCATE":
      return "red";  // Devil's advocate is challenging
    case "DEFENDER":
      return "green";
    case "QUESTIONER":
      return "cyan";
    case "RESPONDENT":
      return "yellow";
    case "PANELIST":
      return "magenta";  // Delphi panelists
    case "IDEATOR":
      return "cyan";  // Brainstorm ideators
    case "EVALUATOR":
      return "blue";  // Tradeoff evaluators
    default:
      return null;  // Use provider color
  }
}

/**
 * Get role badge text for display.
 */
function getRoleBadge(role: string | null | undefined): string | null {
  switch (role) {
    case "FOR":
      return `[${t("role.for")}]`;
    case "AGAINST":
      return `[${t("role.against")}]`;
    case "ADVOCATE":
      return `[${t("role.advocate")}]`;
    case "DEFENDER":
      return `[${t("role.defender")}]`;
    case "QUESTIONER":
      return `[${t("role.questioner")}]`;
    case "RESPONDENT":
      return `[${t("role.respondent")}]`;
    case "PANELIST":
      return `[${t("role.panelist")}]`;
    case "IDEATOR":
      return `[${t("role.ideator")}]`;
    case "EVALUATOR":
      return `[${t("role.evaluator")}]`;
    default:
      return null;
  }
}

/**
 * Get round display name for Oxford mode.
 */
function getRoundLabel(roundType: string | null | undefined): string | null {
  switch (roundType) {
    case "opening":
      return `(${t("round.opening")})`;
    case "rebuttal":
      return `(${t("round.rebuttal")})`;
    case "closing":
      return `(${t("round.closing")})`;
    default:
      return null;
  }
}

// ============================================================================
// Round Header (Oxford mode)
// ============================================================================

interface RoundHeaderProps {
  roundType: "opening" | "rebuttal" | "closing";
}

function RoundHeader({ roundType }: RoundHeaderProps) {
  const getLabel = (type: string): string => {
    switch (type) {
      case "opening": return t("round.opening");
      case "rebuttal": return t("round.rebuttal");
      case "closing": return t("round.closing");
      default: return type;
    }
  };

  return (
    <Box marginY={1} paddingX={2}>
      <Text bold color="magenta">
        ═══ {getLabel(roundType)} ═══
      </Text>
    </Box>
  );
}

// ============================================================================
// Phase Marker
// ============================================================================

interface PhaseMarkerProps {
  phase: number;
  messageKey: string;
  params?: Record<string, string>;
}

export function PhaseMarker({ phase, messageKey, params }: PhaseMarkerProps) {
  const { currentMethod } = useStore();
  const PHASE_NAMES = useMemo(() => getPhaseNames(), []);
  const methodPhases = PHASE_NAMES[currentMethod] || PHASE_NAMES.standard;
  const phaseName = methodPhases[phase] || `Phase ${phase}`;
  const displayMessage = t(messageKey as TranslationKey, params || {});

  return (
    <Box
      flexDirection="column"
      marginY={1}
      borderStyle="single"
      borderColor="blue"
      paddingX={2}
    >
      <Text bold color="blue">
        ━━━ {t("phase.label")} {phase}: {phaseName} ━━━
      </Text>
      <Text dimColor>{displayMessage}</Text>
    </Box>
  );
}

// ============================================================================
// Independent Answer
// ============================================================================

interface IndependentAnswerProps {
  source: string;
  content: string;
}

export function IndependentAnswer({ source, content }: IndependentAnswerProps) {
  const color = getProviderColor(source);

  return (
    <Box
      flexDirection="column"
      marginY={1}
      borderStyle="round"
      borderColor={color}
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text bold color={color}>
          {source}
        </Text>
        <Text dimColor> {t("msg.independentAnswer")}</Text>
      </Box>
      <Markdown>{content}</Markdown>
    </Box>
  );
}

// ============================================================================
// Critique
// ============================================================================

interface CritiqueProps {
  source: string;
  agreements: string;
  disagreements: string;
  missing: string;
}

export function Critique({ source, agreements, disagreements, missing }: CritiqueProps) {
  const color = getProviderColor(source);

  return (
    <Box
      flexDirection="column"
      marginY={1}
      borderStyle="round"
      borderColor={color}
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text bold color={color}>
          {source}
        </Text>
        <Text dimColor> {t("msg.critique")}</Text>
      </Box>
      <Box flexDirection="column">
        {agreements && (
          <Box flexDirection="column" marginBottom={1}>
            <Text color="green" bold>✓ {t("msg.agreements")}</Text>
            <Box marginLeft={2}>
              <Markdown>{agreements}</Markdown>
            </Box>
          </Box>
        )}
        {disagreements && (
          <Box flexDirection="column" marginBottom={1}>
            <Text color="red" bold>✗ {t("msg.disagreements")}</Text>
            <Box marginLeft={2}>
              <Markdown>{disagreements}</Markdown>
            </Box>
          </Box>
        )}
        {missing && (
          <Box flexDirection="column">
            <Text color="yellow" bold>? {t("msg.missing")}</Text>
            <Box marginLeft={2}>
              <Markdown>{missing}</Markdown>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
}

// ============================================================================
// Chat Message (Phase 3)
// ============================================================================

interface ChatMessageProps {
  source: string;
  content: string;
  role?: string | null;
  roundType?: string | null;
}

export function ChatMessage({ source, content, role, roundType }: ChatMessageProps) {
  // Use role color if available, otherwise provider color
  const roleColor = getRoleColor(role);
  const color = roleColor || getProviderColor(source);
  const badge = getRoleBadge(role);
  const roundLabel = getRoundLabel(roundType);

  return (
    <Box
      flexDirection="column"
      marginY={1}
      borderStyle="round"
      borderColor={color}
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text bold color={color}>
          {source}
        </Text>
        {badge && (
          <>
            <Text> </Text>
            <Text bold color={color}>{badge}</Text>
          </>
        )}
        {roundLabel && (
          <>
            <Text> </Text>
            <Text dimColor>{roundLabel}</Text>
          </>
        )}
      </Box>
      <Markdown>{content}</Markdown>
    </Box>
  );
}

// ============================================================================
// Final Position
// ============================================================================

interface FinalPositionProps {
  source: string;
  position: string;
  confidence: string;
}

export function FinalPosition({ source, position, confidence }: FinalPositionProps) {
  const color = getProviderColor(source);
  const confidenceColor =
    confidence === "HIGH" ? "green" : confidence === "MEDIUM" ? "yellow" : "red";

  return (
    <Box
      flexDirection="column"
      marginY={1}
      borderStyle="round"
      borderColor={color}
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text bold color={color}>
          {source}
        </Text>
        <Text dimColor> {t("msg.finalPosition")}</Text>
        <Text> </Text>
        <Text color={confidenceColor} bold>
          [{confidence === "HIGH" ? t("msg.confidence.high") : confidence === "MEDIUM" ? t("msg.confidence.medium") : t("msg.confidence.low")}]
        </Text>
      </Box>
      <Markdown>{position}</Markdown>
    </Box>
  );
}

// ============================================================================
// Synthesis
// ============================================================================

interface SynthesisProps {
  consensus: string;
  synthesis: string;
  differences: string;
  synthesizerModel: string;
  confidenceBreakdown?: Record<string, number>;
  method?: string;
}

export function Synthesis({
  consensus,
  synthesis,
  differences,
  synthesizerModel,
  confidenceBreakdown,
  method,
}: SynthesisProps) {
  const isSocratic = method === "socratic";
  const isAdvocate = method === "advocate";
  const isOxford = method === "oxford";
  const isDelphi = method === "delphi";
  const isBrainstorm = method === "brainstorm";
  const isTradeoff = method === "tradeoff";

  // Method-specific result handling
  // Oxford: FOR (green), AGAINST (red), PARTIAL (yellow)
  // Advocate: No consensus display - just show the verdict
  // Delphi: Convergence YES/PARTIAL/NO
  // Brainstorm: "X SELECTED" (count of ideas)
  // Tradeoff: Agreement YES/NO
  // Standard/Socratic: YES (green), NO (red), PARTIAL (yellow)
  const getResultColor = () => {
    if (isOxford) {
      return consensus === "FOR" ? "green"
        : consensus === "AGAINST" ? "red"
        : "yellow";
    }
    if (isBrainstorm) {
      return "cyan";  // Always cyan for brainstorm ideas
    }
    if (isTradeoff) {
      return consensus === "YES" ? "green" : "yellow";
    }
    return consensus === "YES" ? "green"
      : consensus === "PARTIAL" ? "yellow"
      : "red";
  };

  const getResultIcon = () => {
    if (isOxford) {
      return consensus === "FOR" ? "✓ FOR"
        : consensus === "AGAINST" ? "✗ AGAINST"
        : "◐ PARTIAL";
    }
    if (isSocratic) {
      return consensus === "YES" ? "✓"
        : consensus === "PARTIAL" ? "◐"
        : "✗";
    }
    if (isDelphi) {
      return consensus === "YES" ? "✓"
        : consensus === "PARTIAL" ? "◐"
        : "✗";
    }
    if (isBrainstorm) {
      return "💡";  // Light bulb for ideas
    }
    if (isTradeoff) {
      return consensus === "YES" ? "✓" : "◐";
    }
    return consensus === "YES" ? "✓"
      : consensus === "PARTIAL" ? "◐"
      : "✗";
  };

  const resultColor = getResultColor();

  // Method-specific terminology for authentic presentation
  const resultLabel = isSocratic ? t("synthesis.aporia")
    : isOxford ? t("synthesis.decision")
    : isDelphi ? t("synthesis.convergence")
    : isBrainstorm ? t("synthesis.selectedIdeas")
    : isTradeoff ? t("synthesis.agreement")
    : t("synthesis.consensus");
  const differencesLabel = isSocratic ? t("synthesis.openQuestions")
    : isAdvocate ? t("synthesis.unresolvedQuestions")
    : isOxford ? t("synthesis.keyContentions")
    : isDelphi ? t("synthesis.outlierPerspectives")
    : isBrainstorm ? t("synthesis.alternativeDirections")
    : isTradeoff ? t("synthesis.keyTradeoffs")
    : t("synthesis.notableDifferences");
  const synthesisLabel = isSocratic ? t("synthesis.reflection")
    : isAdvocate ? t("synthesis.ruling")
    : isOxford ? t("synthesis.adjudication")
    : isDelphi ? t("synthesis.aggregatedEstimate")
    : isBrainstorm ? t("synthesis.finalIdeas")
    : isTradeoff ? t("synthesis.recommendation")
    : t("synthesis.synthesisLabel");

  return (
    <Box
      flexDirection="column"
      marginY={1}
      borderStyle="double"
      borderColor={isAdvocate ? "red" : resultColor}
      paddingX={2}
      paddingY={1}
    >
      {/* Advocate: Skip consensus display - the verdict IS the result */}
      {/* Other methods: Show result/consensus status */}
      {!isAdvocate && (
        <Box marginBottom={1}>
          <Text bold color={resultColor}>
            {isOxford ? getResultIcon() : `${getResultIcon()} ${resultLabel}: ${consensus}`}
          </Text>
          <Text dimColor>
            {" "}({isSocratic ? t("synthesis.reflected") : isOxford ? t("synthesis.adjudicated") : t("synthesis.synthesized")} by {synthesizerModel})
          </Text>
        </Box>
      )}

      {/* Advocate: Show who delivered the verdict */}
      {isAdvocate && (
        <Box marginBottom={1}>
          <Text bold color="red">⚖ {t("msg.verdict")}</Text>
          <Text dimColor> {t("synthesis.ruledBy", { model: synthesizerModel })}</Text>
        </Box>
      )}

      {/* Confidence breakdown shown for Standard and Delphi (methods with confidence levels) */}
      {confidenceBreakdown && (method === "standard" || method === "delphi") && (
        <Box marginBottom={1}>
          <Text dimColor>{isDelphi ? t("msg.confidence.panelist") : t("msg.confidence.breakdown")}</Text>
          <Text color="green">{t("msg.confidence.high")}: {confidenceBreakdown.HIGH || 0} </Text>
          <Text color="yellow">{t("msg.confidence.medium")}: {confidenceBreakdown.MEDIUM || 0} </Text>
          <Text color="red">{t("msg.confidence.low")}: {confidenceBreakdown.LOW || 0}</Text>
        </Box>
      )}

      <Box flexDirection="column" marginBottom={1}>
        <Text bold>{synthesisLabel}:</Text>
        <Box marginLeft={2}>
          <Markdown>{synthesis}</Markdown>
        </Box>
      </Box>

      {differences && differences !== "None" && differences !== "See verdict above for unresolved questions." && (
        <Box flexDirection="column">
          <Text bold color="yellow">
            {differencesLabel}:
          </Text>
          <Box marginLeft={2}>
            <Markdown>{differences}</Markdown>
          </Box>
        </Box>
      )}
    </Box>
  );
}

// ============================================================================
// Discussion Header
// ============================================================================

const getMethodTitles = (): Record<DiscussionMethod, string> => ({
  standard: t("discussion.standard"),
  oxford: t("discussion.oxford"),
  advocate: t("discussion.advocate"),
  socratic: t("discussion.socratic"),
  delphi: t("discussion.delphi"),
  brainstorm: t("discussion.brainstorm"),
  tradeoff: t("discussion.tradeoff"),
});

interface DiscussionHeaderProps {
  method: DiscussionMethod;
  models: string[];
  roleAssignments?: Record<string, string[]>;
}

export function DiscussionHeader({ method, models, roleAssignments }: DiscussionHeaderProps) {
  const { availableModels } = useStore();
  const METHOD_TITLES = getMethodTitles();

  const getDisplayName = (modelId: string) =>
    getModelDisplayName(modelId, availableModels);

  const title = METHOD_TITLES[method] || "DISCUSSION";

  // Get method-specific color
  const methodColor = method === "oxford" ? "magenta"
    : method === "advocate" ? "red"
    : method === "socratic" ? "cyan"
    : method === "delphi" ? "magenta"
    : method === "brainstorm" ? "cyan"
    : method === "tradeoff" ? "blue"
    : "blue";

  // Render based on method type
  const renderParticipants = () => {
    if (!roleAssignments || Object.keys(roleAssignments).length === 0) {
      // Standard - no roles, just list participants
      return (
        <Box flexDirection="column">
          <Text dimColor>{t("msg.participants")}</Text>
          <Box flexDirection="row" flexWrap="wrap" marginTop={1}>
            {models.map((model, i) => (
              <Box key={model} marginRight={2}>
                <Text color={getProviderColor(model)}>● {getDisplayName(model)}</Text>
              </Box>
            ))}
          </Box>
        </Box>
      );
    }

    // Role-based methods
    const roles = Object.keys(roleAssignments);

    if (method === "socratic") {
      // Socratic: One respondent, multiple questioners
      const respondent = roleAssignments["Respondent"]?.[0];
      const questioners = roleAssignments["Questioners"] || [];

      return (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text color="yellow" bold>{t("role.respondent")}</Text>
          </Box>
          {respondent && (
            <Box marginLeft={2} marginBottom={1}>
              <Text color={getProviderColor(respondent)}>● {getDisplayName(respondent)}</Text>
            </Box>
          )}
          <Box marginBottom={1}>
            <Text color="cyan" bold>{t("role.questioner")}</Text>
          </Box>
          <Box marginLeft={2} flexDirection="column">
            {questioners.map((model) => (
              <Text key={model} color={getProviderColor(model)}>● {getDisplayName(model)}</Text>
            ))}
          </Box>
        </Box>
      );
    }

    // Oxford/Advocate: Two columns
    // Note: Keys match TeamPreview format - Oxford uses "FOR"/"AGAINST", Advocate uses "Defenders"/"Advocate"
    const leftRole = method === "oxford" ? "FOR" : "Defenders";
    const rightRole = method === "oxford" ? "AGAINST" : "Advocate";
    const leftLabel = method === "oxford" ? t("team.forTeam") : t("team.defenders");
    const rightLabel = method === "oxford" ? t("team.againstTeam") : t("role.advocate");
    const leftColor = "green";
    const rightColor = "red";
    const leftModels = roleAssignments[leftRole] || [];
    const rightModels = roleAssignments[rightRole] || [];

    return (
      <Box>
        <Box flexDirection="column" width="50%">
          <Text color={leftColor} bold>{leftLabel}</Text>
          <Box marginLeft={2} marginTop={1} flexDirection="column">
            {leftModels.map((model) => (
              <Text key={model} color={getProviderColor(model)}>● {getDisplayName(model)}</Text>
            ))}
          </Box>
        </Box>
        <Box flexDirection="column" width="50%">
          <Text color={rightColor} bold>{rightLabel}</Text>
          <Box marginLeft={2} marginTop={1} flexDirection="column">
            {rightModels.map((model) => (
              <Text key={model} color={getProviderColor(model)}>● {getDisplayName(model)}</Text>
            ))}
          </Box>
        </Box>
      </Box>
    );
  };

  return (
    <Box
      flexDirection="column"
      marginY={1}
      borderStyle="double"
      borderColor={methodColor}
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text bold color={methodColor}>{title}</Text>
      </Box>
      {renderParticipants()}
    </Box>
  );
}

// ============================================================================
// Generic Message Renderer
// ============================================================================

interface MessageProps {
  message: DiscussionMessage;
}

/**
 * Memoized Message component to prevent unnecessary re-renders.
 * Only re-renders when the message prop actually changes.
 */
export const Message = React.memo(function Message({ message }: MessageProps) {
  const { availableModels } = useStore();

  // Get display name for any model source
  const getDisplayName = (modelId: string) =>
    getModelDisplayName(modelId, availableModels);

  switch (message.type) {
    case "phase":
      return (
        <PhaseMarker
          phase={message.phase || 0}
          messageKey={message.phaseMessageKey || ""}
          params={message.phaseParams}
        />
      );

    case "answer":
      return (
        <IndependentAnswer
          source={getDisplayName(message.source || "")}
          content={message.content || ""}
        />
      );

    case "critique":
      return (
        <Critique
          source={getDisplayName(message.source || "")}
          agreements={message.agreements || ""}
          disagreements={message.disagreements || ""}
          missing={message.missing || ""}
        />
      );

    case "chat":
      return (
        <ChatMessage
          source={getDisplayName(message.source || "")}
          content={message.content || ""}
          role={message.role}
          roundType={message.roundType}
        />
      );

    case "round_header":
      return (
        <RoundHeader
          roundType={message.roundType as "opening" | "rebuttal" | "closing"}
        />
      );

    case "position":
      return (
        <FinalPosition
          source={getDisplayName(message.source || "")}
          position={message.position || ""}
          confidence={message.confidence || "MEDIUM"}
        />
      );

    case "synthesis":
      return (
        <Synthesis
          consensus={message.consensus || "PARTIAL"}
          synthesis={message.synthesis || ""}
          differences={message.differences || "None"}
          synthesizerModel={getDisplayName(message.synthesizerModel || "")}
          confidenceBreakdown={message.confidenceBreakdown}
          method={message.method}
        />
      );

    case "discussion_header":
      return (
        <DiscussionHeader
          method={message.headerMethod || "standard"}
          models={message.headerModels || []}
          roleAssignments={message.headerRoleAssignments}
        />
      );

    default:
      return null;
  }
});
