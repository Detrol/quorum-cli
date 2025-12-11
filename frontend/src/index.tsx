#!/usr/bin/env node
/**
 * Quorum Frontend - Terminal UI for multi-agent consensus.
 */

import React from "react";
import { render } from "ink";
import { writeFileSync } from "node:fs";
import { App } from "./App.js";

// Signal bash spinner to stop (if running via shell launcher)
const signalFile = process.env.QUORUM_SIGNAL_FILE;
if (signalFile) {
  writeFileSync(signalFile, "ready");
}

// Clear screen
process.stdout.write('\x1Bc');

const { unmount, waitUntilExit } = render(<App />);

// Handle graceful shutdown
process.on("SIGINT", () => {
  // Restore cursor visibility
  process.stdout.write('\x1b[?25h');
  unmount();
  process.exit(0);
});

process.on("SIGTERM", () => {
  // Restore cursor visibility
  process.stdout.write('\x1b[?25h');
  unmount();
  process.exit(0);
});

// Wait for app to exit
waitUntilExit().then(() => {
  // Restore cursor visibility
  process.stdout.write('\x1b[?25h');
  process.exit(0);
});
