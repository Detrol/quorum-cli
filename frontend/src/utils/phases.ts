/**
 * Phase names for different discussion methods.
 * Shared between Discussion.tsx and Message.tsx.
 */

import { t } from "../i18n/index.js";

/**
 * Get method-specific phase names (translated).
 */
export const getPhaseNames = (): Record<string, Record<number, string>> => ({
  standard: {
    1: t("phase.standard.1"),
    2: t("phase.standard.2"),
    3: t("phase.standard.3"),
    4: t("phase.standard.4"),
    5: t("phase.standard.5"),
  },
  oxford: {
    1: t("phase.oxford.1"),
    2: t("phase.oxford.2"),
    3: t("phase.oxford.3"),
    4: t("phase.oxford.4"),
  },
  advocate: {
    1: t("phase.advocate.1"),
    2: t("phase.advocate.2"),
    3: t("phase.advocate.3"),
  },
  socratic: {
    1: t("phase.socratic.1"),
    2: t("phase.socratic.2"),
    3: t("phase.socratic.3"),
  },
  delphi: {
    1: t("phase.delphi.1"),
    2: t("phase.delphi.2"),
    3: t("phase.delphi.3"),
    4: t("phase.delphi.4"),
  },
  brainstorm: {
    1: t("phase.brainstorm.1"),
    2: t("phase.brainstorm.2"),
    3: t("phase.brainstorm.3"),
    4: t("phase.brainstorm.4"),
  },
  tradeoff: {
    1: t("phase.tradeoff.1"),
    2: t("phase.tradeoff.2"),
    3: t("phase.tradeoff.3"),
    4: t("phase.tradeoff.4"),
  },
});
