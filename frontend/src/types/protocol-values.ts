/**
 * Centralized type definitions for protocol values exchanged between backend and frontend.
 * These types ensure type safety and provide translation key mappings for i18n.
 */

import type { TranslationKey } from "../i18n/index.js";

// =============================================================================
// Confidence Levels
// =============================================================================

/** Confidence levels from backend FinalPositionEvent */
export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";

/** Translation key mapping for confidence levels */
export const CONFIDENCE_KEYS: Record<ConfidenceLevel, TranslationKey> = {
  HIGH: "msg.confidence.high",
  MEDIUM: "msg.confidence.medium",
  LOW: "msg.confidence.low",
} as const;

// =============================================================================
// Consensus Values
// =============================================================================

/** Standard consensus values (Standard, Socratic, Delphi, Advocate, Tradeoff) */
export type StandardConsensus = "YES" | "NO" | "PARTIAL";

/** Oxford method consensus values */
export type OxfordConsensus = "FOR" | "AGAINST";

/** All possible consensus values */
export type ConsensusValue = StandardConsensus | OxfordConsensus;

/** Translation key mapping for standard consensus values */
export const CONSENSUS_KEYS: Record<StandardConsensus, TranslationKey> = {
  YES: "consensus.yes",
  NO: "consensus.no",
  PARTIAL: "consensus.partial",
} as const;

// =============================================================================
// Role Values
// =============================================================================

/** Role values across all discussion methods */
export type RoleValue =
  | "FOR"          // Oxford
  | "AGAINST"      // Oxford
  | "ADVOCATE"     // Advocate
  | "DEFENDER"     // Advocate
  | "QUESTIONER"   // Socratic
  | "RESPONDENT"   // Socratic
  | "PANELIST"     // Delphi
  | "IDEATOR"      // Brainstorm
  | "EVALUATOR";   // Brainstorm

/** Translation key mapping for role values */
export const ROLE_KEYS: Record<RoleValue, TranslationKey> = {
  FOR: "role.for",
  AGAINST: "role.against",
  ADVOCATE: "role.advocate",
  DEFENDER: "role.defender",
  QUESTIONER: "role.questioner",
  RESPONDENT: "role.respondent",
  PANELIST: "role.panelist",
  IDEATOR: "role.ideator",
  EVALUATOR: "role.evaluator",
} as const;

// =============================================================================
// Type Guards
// =============================================================================

/** Check if a string is a valid ConfidenceLevel */
export function isConfidenceLevel(value: string | undefined | null): value is ConfidenceLevel {
  return value === "HIGH" || value === "MEDIUM" || value === "LOW";
}

/** Check if a string is a valid StandardConsensus */
export function isStandardConsensus(value: string | undefined | null): value is StandardConsensus {
  return value === "YES" || value === "NO" || value === "PARTIAL";
}

/** Check if a string is a valid RoleValue */
export function isRoleValue(value: string | undefined | null): value is RoleValue {
  return value !== null && value !== undefined && value in ROLE_KEYS;
}
