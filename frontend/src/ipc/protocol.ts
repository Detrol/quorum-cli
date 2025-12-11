/**
 * JSON-RPC 2.0 protocol types for Quorum IPC.
 */

// ============================================================================
// Protocol Version
// ============================================================================

/**
 * Protocol version for frontend-backend compatibility.
 * Increment MAJOR for breaking changes, MINOR for additions, PATCH for fixes.
 * Backend checks this to warn about compatibility issues.
 */
export const PROTOCOL_VERSION = "1.0.0";

// ============================================================================
// JSON-RPC Base Types
// ============================================================================

export interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: string | number;
  method: string;
  params?: object;
}

export interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: string | number;
  result?: unknown;
  error?: JsonRpcError;
}

export interface JsonRpcNotification {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, unknown>;
}

export interface JsonRpcError {
  code: number;
  message: string;
  data?: unknown;
}

// ============================================================================
// Request Types
// ============================================================================

export interface InitializeParams {
  protocol_version?: string;  // Frontend can send its version for compatibility check
}

export interface InitializeResult {
  name: string;
  version: string;
  protocol_version: string;  // Backend's protocol version
  providers: string[];
  version_warning?: string;  // Warning if version mismatch detected
}

export interface ListModelsParams {}

export interface ModelInfo {
  id: string;
  provider: string;
  display_name: string | null;
}

export interface ListModelsResult {
  models: Record<string, ModelInfo[]>;
  validated: string[];  // Cached validated model IDs
}

export interface ValidateModelParams {
  model_id: string;
}

export interface ValidateModelResult {
  valid: boolean;
  error: string | null;
}

export interface RunDiscussionParams {
  question: string;
  model_ids: string[];
  options?: {
    method?: "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
    max_turns?: number;
    synthesizer_mode?: "first" | "random" | "rotate";
    role_assignments?: Record<string, string[]>;
  };
}

export interface RunDiscussionResult {
  status: "completed" | "cancelled";
}

export interface UserSettings {
  selected_models?: string[];
  discussion_method?: "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
  synthesizer_mode?: "first" | "random" | "rotate";
  max_turns?: number | null;
}

export type RoleAssignments = Record<string, string[]>;

export interface GetRoleAssignmentsParams {
  method: string;
  model_ids: string[];
}

export interface GetRoleAssignmentsResult {
  assignments: RoleAssignments | null;
}

export interface SwapRoleAssignmentsParams {
  assignments: RoleAssignments;
}

export interface SwapRoleAssignmentsResult {
  assignments: RoleAssignments;
}

export interface AnalyzeQuestionParams {
  question: string;
}

export interface MethodRecommendation {
  method: string;
  confidence: number;
  reason: string;
}

export interface AnalyzeQuestionResult {
  advisor_model: string;
  recommendations: {
    primary: MethodRecommendation;
    alternatives: MethodRecommendation[];
  };
}

export interface GetConfigResult {
  rounds_per_agent: number;
  synthesizer_mode: string;
  default_language: string | null;
  available_providers: string[];
  report_dir: string;
  export_dir: string | null;
  export_format: "md" | "text" | "pdf";
}

// ============================================================================
// Event Types (Notifications from backend)
// ============================================================================

/**
 * All discussion events include an optional discussion_id for filtering.
 * Events from cancelled discussions can be identified and ignored by
 * checking if discussion_id matches the current discussion.
 */

export interface ReadyEvent {
  version: string;
  protocol_version: string;  // Protocol version for compatibility checking
}

export interface PhaseStartEvent {
  discussion_id?: string;
  phase: number;
  message_key: string;
  params?: Record<string, string>;
  num_participants: number;
  method?: "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
  total_phases?: number;
}

export interface IndependentAnswerEvent {
  discussion_id?: string;
  source: string;
  content: string;
}

export interface CritiqueEvent {
  discussion_id?: string;
  source: string;
  agreements: string;
  disagreements: string;
  missing: string;
}

export interface ChatMessageEvent {
  discussion_id?: string;
  source: string;
  content: string;
  role?: "FOR" | "AGAINST" | "ADVOCATE" | "DEFENDER" | "QUESTIONER" | "RESPONDENT" | "PANELIST" | "IDEATOR" | "EVALUATOR" | null;
  round_type?: "opening" | "rebuttal" | "closing" | null;
  method?: "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
}

export interface FinalPositionEvent {
  discussion_id?: string;
  source: string;
  position: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
}

export interface SynthesisEvent {
  discussion_id?: string;
  consensus: string;  // YES/PARTIAL/NO for most, but also FOR/AGAINST for Oxford, "X SELECTED" for brainstorm, etc.
  synthesis: string;
  differences: string;
  synthesizer_model: string;
  confidence_breakdown: Record<string, number>;
  message_count: number;
  method?: "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
}

export interface DiscussionCompleteEvent {
  discussion_id?: string;
  messages_count?: number;
}

export interface DiscussionErrorEvent {
  discussion_id?: string;
  error: string;
}

export interface DiscussionCancelledEvent {
  discussion_id?: string;
}

export interface ThinkingEvent {
  discussion_id?: string;
  model: string;
}

export interface ThinkingCompleteEvent {
  discussion_id?: string;
  model: string;
}

export interface PhaseCompleteEvent {
  discussion_id?: string;
  completed_phase: number;
  next_phase: number;
  next_phase_message_key?: string;
  next_phase_params?: Record<string, string>;
  method?: string;
}

export interface PauseTimeoutEvent {
  discussion_id?: string;
  message: string;
  timeout_seconds: number;
}

// ============================================================================
// Event Map
// ============================================================================

export interface EventMap {
  ready: ReadyEvent;
  phase_complete: PhaseCompleteEvent;
  pause_timeout: PauseTimeoutEvent;
  phase_start: PhaseStartEvent;
  thinking: ThinkingEvent;
  thinking_complete: ThinkingCompleteEvent;
  independent_answer: IndependentAnswerEvent;
  critique: CritiqueEvent;
  chat_message: ChatMessageEvent;
  final_position: FinalPositionEvent;
  synthesis: SynthesisEvent;
  discussion_complete: DiscussionCompleteEvent;
  discussion_error: DiscussionErrorEvent;
  discussion_cancelled: DiscussionCancelledEvent;
}

export type EventType = keyof EventMap;
