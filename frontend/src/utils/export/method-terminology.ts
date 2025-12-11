/**
 * Method-specific terminology registry for export formatting.
 * Single source of truth for all 7 discussion methods.
 * Uses i18n for translated labels.
 */

import type { DiscussionMethod } from "../../store/index.js";
import { t, type TranslationKey } from "../../i18n/index.js";

/**
 * Labels and configuration for a discussion method's export formatting.
 */
export interface MethodTerminology {
  /** Header for result section (e.g., "Result", "Verdict", "Aporia") */
  resultLabel: string;
  /** Header for synthesis content (e.g., "Synthesis", "Ruling", "Reflection") */
  synthesisLabel: string;
  /** Header for differences section (e.g., "Notable Differences", "Open Questions") */
  differencesLabel: string;
  /** Attribution prefix (e.g., "Synthesized by", "Ruled by") */
  byLabel: string;
  /** Label for consensus line (e.g., "Consensus", "Decision", "Convergence") */
  consensusLabel: string;
  /** Whether to show consensus as separate line (false for Advocate) */
  showConsensus: boolean;
  /** Banner color for PDF export */
  bannerColor: string;
}

/**
 * Static configuration for methods (non-translated properties).
 */
const METHOD_CONFIG: Record<DiscussionMethod, { showConsensus: boolean; bannerColor: string }> = {
  standard: { showConsensus: true, bannerColor: "#065f46" },
  oxford: { showConsensus: true, bannerColor: "#7c3aed" },
  advocate: { showConsensus: false, bannerColor: "#991b1b" },
  socratic: { showConsensus: true, bannerColor: "#0e7490" },
  delphi: { showConsensus: true, bannerColor: "#7e22ce" },
  brainstorm: { showConsensus: true, bannerColor: "#0891b2" },
  tradeoff: { showConsensus: true, bannerColor: "#1d4ed8" },
};

/**
 * Get terminology for a discussion method.
 * Labels are dynamically translated using the current language.
 * @param method - The discussion method
 * @returns Method-specific terminology
 */
export function getMethodTerminology(method: DiscussionMethod): MethodTerminology {
  const config = METHOD_CONFIG[method];

  return {
    resultLabel: t(`terminology.result.${method}` as TranslationKey),
    synthesisLabel: t(`terminology.synthesis.${method}` as TranslationKey),
    differencesLabel: t(`terminology.differences.${method}` as TranslationKey),
    byLabel: t(`terminology.by.${method}` as TranslationKey),
    consensusLabel: config.showConsensus
      ? t(`terminology.consensus.${method}` as TranslationKey)
      : "",
    showConsensus: config.showConsensus,
    bannerColor: config.bannerColor,
  };
}

/**
 * Get result label in uppercase (for plain text export).
 */
export function getResultLabelUppercase(method: DiscussionMethod): string {
  return t(`terminology.result.${method}` as TranslationKey).toUpperCase();
}
