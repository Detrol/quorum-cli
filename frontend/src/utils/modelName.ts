/**
 * Shared model name formatting utilities.
 * Consolidates duplicate formatting logic from Message.tsx and export.ts.
 */

import type { ModelInfo } from "../ipc/protocol.js";

// Cache for formatted model names (memoization)
const modelNameCache = new Map<string, string>();

// Known model name capitalizations
const CAPITALIZATIONS: Record<string, string> = {
  gpt: "GPT",
  claude: "Claude",
  gemini: "Gemini",
  grok: "Grok",
  sonnet: "Sonnet",
  opus: "Opus",
  haiku: "Haiku",
  pro: "Pro",
  flash: "Flash",
  mini: "Mini",
  fast: "Fast",
  reasoning: "Reasoning",
};

/**
 * Format a model ID into a readable display name.
 * Converts "grok-4-1-fast-reasoning" to "Grok 4.1 Fast Reasoning"
 * Idempotent: already formatted names pass through unchanged.
 * Results are memoized for performance.
 */
export function formatModelName(modelId: string): string {
  if (!modelId) return "";

  // Check cache first
  const cached = modelNameCache.get(modelId);
  if (cached !== undefined) {
    return cached;
  }

  // If already formatted (contains spaces and starts with capital), cache and return as-is
  if (modelId.includes(" ") && /^[A-Z]/.test(modelId)) {
    modelNameCache.set(modelId, modelId);
    return modelId;
  }

  // Remove date suffixes like -2025-11-13 or -20250929
  let formatted = modelId.replace(/-\d{4}-\d{2}-\d{2}$/, "");
  formatted = formatted.replace(/-\d{8}$/, "");

  // Convert underscores to hyphens for consistent splitting
  formatted = formatted.replace(/_/g, "-");

  // Split by hyphens
  const parts = formatted.split(/-+/);
  const capitalized = parts.map((part) => {
    const lower = part.toLowerCase();
    // Check for version numbers like "4" or "4o" or "2.5"
    if (/^\d/.test(part)) {
      // Keep version numbers as-is
      return part.replace(/-/g, ".");
    }
    return (
      CAPITALIZATIONS[lower] ||
      (part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    );
  });

  // Join with spaces, but handle version numbers specially
  let result = "";
  for (let i = 0; i < capitalized.length; i++) {
    const part = capitalized[i];
    if (i > 0) {
      // Don't add space before version numbers that follow a model name
      const prevPart = capitalized[i - 1];
      if (/^\d/.test(part) && /^[A-Za-z]/.test(prevPart)) {
        result += " ";
      } else if (/^\d/.test(prevPart) && /^\d/.test(part)) {
        // Combine consecutive number parts with dot: "4" + "1" -> "4.1"
        result += ".";
      } else {
        result += " ";
      }
    }
    result += part;
  }

  const trimmedResult = result.trim();
  modelNameCache.set(modelId, trimmedResult);
  return trimmedResult;
}

/**
 * Look up display name for a model ID from available models.
 * Falls back to formatted model name if not found in the models registry.
 */
export function getModelDisplayName(
  modelId: string,
  availableModels: Record<string, ModelInfo[]>
): string {
  for (const models of Object.values(availableModels)) {
    const model = models.find((m) => m.id === modelId);
    if (model?.display_name) return model.display_name;
  }
  return formatModelName(modelId);
}
