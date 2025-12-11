/**
 * Shared spinner hook for terminal-based spinners.
 * Consolidates duplicate spinner logic from Discussion.tsx and MethodAdvisor.tsx.
 */

import { useEffect, useRef } from "react";

/** Spinner animation frames */
export const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

/** Animation interval in milliseconds */
export const SPINNER_INTERVAL_MS = 80;

/** ANSI color codes */
const ANSI_COLORS = {
  yellow: "\x1b[33m",
  green: "\x1b[32m",
  reset: "\x1b[0m",
} as const;

export interface UseTerminalSpinnerOptions {
  /** Text to display next to the spinner */
  text: string;
  /** Spinner color */
  color: "yellow" | "green";
  /** Whether the spinner is active */
  active: boolean;
  /** Number of lines to move up from cursor (default: 1) */
  linesUp?: number;
}

/**
 * Terminal spinner hook that writes directly to stdout with cursor positioning.
 * Used for smooth spinner animations without React re-renders.
 */
export function useTerminalSpinner({
  text,
  color,
  active,
  linesUp = 1,
}: UseTerminalSpinnerOptions): void {
  const spinnerTextRef = useRef("");

  useEffect(() => {
    if (!active) {
      spinnerTextRef.current = "";
      return;
    }

    let frameIndex = 0;
    const colorCode = ANSI_COLORS[color];

    // Hide cursor
    process.stdout.write("\x1b[?25l");

    const writeSpinner = (spinnerText: string): void => {
      process.stdout.write("\x1b[s"); // Save cursor
      process.stdout.write(`\x1b[${linesUp}A`); // Move up
      process.stdout.write(`\r\x1b[K${colorCode}${spinnerText}${ANSI_COLORS.reset}`); // Clear and write
      process.stdout.write("\x1b[u"); // Restore cursor
    };

    // Initial render with small delay
    const startDelay = setTimeout(() => {
      spinnerTextRef.current = ` ${SPINNER_FRAMES[0]} ${text}`;
      writeSpinner(spinnerTextRef.current);
    }, 10);

    // Animation loop
    const timer = setInterval(() => {
      frameIndex = (frameIndex + 1) % SPINNER_FRAMES.length;
      spinnerTextRef.current = ` ${SPINNER_FRAMES[frameIndex]} ${text}`;
      writeSpinner(spinnerTextRef.current);
    }, SPINNER_INTERVAL_MS);

    // Cleanup
    return () => {
      clearTimeout(startDelay);
      clearInterval(timer);
      process.stdout.write("\x1b[s");
      process.stdout.write(`\x1b[${linesUp}A`);
      process.stdout.write("\r\x1b[K");
      process.stdout.write("\x1b[u");
      process.stdout.write("\x1b[?25h"); // Show cursor
      spinnerTextRef.current = "";
    };
  }, [text, color, active, linesUp]);
}

/**
 * Simple in-place spinner hook for inline animations (like MethodAdvisor).
 * Returns the current spinner frame as a string.
 */
export function useInlineSpinner(active: boolean): string {
  const frameRef = useRef(0);
  const textRef = useRef(SPINNER_FRAMES[0]);

  useEffect(() => {
    if (!active) {
      frameRef.current = 0;
      textRef.current = SPINNER_FRAMES[0];
      return;
    }

    const timer = setInterval(() => {
      frameRef.current = (frameRef.current + 1) % SPINNER_FRAMES.length;
      textRef.current = SPINNER_FRAMES[frameRef.current];
    }, SPINNER_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [active]);

  return textRef.current;
}
