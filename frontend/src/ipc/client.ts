/**
 * IPC Client for communicating with Quorum Python backend.
 */

import { spawn, ChildProcess } from "node:child_process";
import { createInterface, Interface } from "node:readline";
import { EventEmitter } from "node:events";
import { v4 as uuidv4 } from "uuid";

import type {
  JsonRpcRequest,
  JsonRpcResponse,
  JsonRpcNotification,
  InitializeResult,
  ListModelsResult,
  ValidateModelResult,
  UserSettings,
  RunDiscussionParams,
  RunDiscussionResult,
  RoleAssignments,
  GetRoleAssignmentsResult,
  SwapRoleAssignmentsResult,
  AnalyzeQuestionResult,
  GetConfigResult,
  EventMap,
  EventType,
} from "./protocol.js";

type EventListener<T extends EventType> = (params: EventMap[T]) => void;

interface PendingRequest {
  resolve: (result: unknown) => void;
  reject: (error: Error) => void;
}

export class BackendClient extends EventEmitter {
  private process: ChildProcess | null = null;
  private readline: Interface | null = null;
  private pendingRequests: Map<string, PendingRequest> = new Map();
  private isReady = false;
  private readyPromise: Promise<void> | null = null;
  private readyResolve: (() => void) | null = null;
  private pythonCommand: string;
  private pythonArgs: string[];

  constructor() {
    super();

    // Python tells us where it is via QUORUM_PYTHON env var (set by main.py)
    // This works for both dev mode and pip install
    this.pythonCommand = process.env.QUORUM_PYTHON || "python";
    this.pythonArgs = ["-m", "quorum", "--ipc"];
  }

  /**
   * Start the backend process.
   */
  async start(): Promise<void> {
    if (this.process) {
      throw new Error("Backend already started");
    }

    this.readyPromise = new Promise((resolve) => {
      this.readyResolve = resolve;
    });

    this.process = spawn(this.pythonCommand, this.pythonArgs, {
      stdio: ["pipe", "pipe", "pipe"],
    });

    this.process.on("error", (err) => {
      this.emit("error", err);
    });

    this.process.on("exit", (code) => {
      this.isReady = false;
      this.emit("exit", code);
    });

    // Read stdout line by line
    if (this.process.stdout) {
      this.readline = createInterface({
        input: this.process.stdout,
        crlfDelay: Infinity,
      });

      this.readline.on("line", (line) => {
        this.handleLine(line);
      });
    }

    // Capture stderr for debugging
    if (this.process.stderr) {
      const stderrReader = createInterface({
        input: this.process.stderr,
        crlfDelay: Infinity,
      });

      stderrReader.on("line", (line) => {
        this.emit("stderr", line);
      });
    }

    // Wait for ready event
    await this.readyPromise;
  }

  /**
   * Stop the backend process.
   */
  stop(): void {
    if (this.readline) {
      this.readline.close();
      this.readline = null;
    }

    if (this.process) {
      this.process.kill();
      this.process = null;
    }

    this.isReady = false;

    // Reject all pending requests
    for (const [id, pending] of this.pendingRequests) {
      pending.reject(new Error("Backend stopped"));
    }
    this.pendingRequests.clear();
  }

  /**
   * Handle a line of output from the backend.
   */
  private handleLine(line: string): void {
    if (!line.trim()) return;

    let message: JsonRpcResponse | JsonRpcNotification;
    try {
      message = JSON.parse(line);
    } catch (e) {
      this.emit("parse_error", line);
      return;
    }

    // Check if it's a response (has id) or notification
    if ("id" in message && message.id !== undefined) {
      const response = message as JsonRpcResponse;
      const pending = this.pendingRequests.get(String(response.id));

      if (pending) {
        this.pendingRequests.delete(String(response.id));

        if (response.error) {
          pending.reject(new Error(response.error.message));
        } else {
          pending.resolve(response.result);
        }
      }
    } else {
      // It's a notification/event
      const notification = message as JsonRpcNotification;
      const method = notification.method as EventType;

      // Handle ready event specially
      if (method === "ready" && this.readyResolve) {
        this.isReady = true;
        this.readyResolve();
        this.readyResolve = null;
      }

      // Emit the event
      this.emit(method, notification.params);
    }
  }

  /**
   * Send a request and wait for response.
   */
  private async request<T>(method: string, params: object = {}): Promise<T> {
    if (!this.process || !this.process.stdin) {
      throw new Error("Backend not started");
    }

    if (!this.isReady && method !== "initialize") {
      await this.readyPromise;
    }

    const id = uuidv4();
    const request: JsonRpcRequest = {
      jsonrpc: "2.0",
      id,
      method,
      params,
    };

    return new Promise<T>((resolve, reject) => {
      this.pendingRequests.set(id, {
        resolve: resolve as (result: unknown) => void,
        reject,
      });

      const line = JSON.stringify(request) + "\n";
      this.process!.stdin!.write(line);
    });
  }

  // =========================================================================
  // Public API Methods
  // =========================================================================

  async initialize(): Promise<InitializeResult> {
    return this.request<InitializeResult>("initialize");
  }

  async listModels(): Promise<ListModelsResult> {
    return this.request<ListModelsResult>("list_models");
  }

  async validateModel(modelId: string): Promise<ValidateModelResult> {
    return this.request<ValidateModelResult>("validate_model", { model_id: modelId });
  }

  async getConfig(): Promise<GetConfigResult> {
    return this.request<GetConfigResult>("get_config");
  }

  async getUserSettings(): Promise<UserSettings> {
    return this.request<UserSettings>("get_user_settings");
  }

  async saveUserSettings(settings: Partial<UserSettings>): Promise<void> {
    await this.request("save_user_settings", settings);
  }

  async getInputHistory(): Promise<string[]> {
    const result = await this.request<{ history: string[] }>("get_input_history");
    return result.history;
  }

  async addToInputHistory(input: string): Promise<void> {
    await this.request("add_to_input_history", { input });
  }

  async runDiscussion(params: RunDiscussionParams): Promise<RunDiscussionResult> {
    return this.request<RunDiscussionResult>("run_discussion", params);
  }

  async cancelDiscussion(): Promise<void> {
    await this.request("cancel_discussion");
  }

  async resumeDiscussion(): Promise<void> {
    await this.request("resume_discussion");
  }

  async getRoleAssignments(method: string, modelIds: string[]): Promise<RoleAssignments | null> {
    const result = await this.request<GetRoleAssignmentsResult>("get_role_assignments", {
      method,
      model_ids: modelIds,
    });
    return result.assignments;
  }

  async swapRoleAssignments(assignments: RoleAssignments): Promise<RoleAssignments> {
    const result = await this.request<SwapRoleAssignmentsResult>("swap_role_assignments", {
      assignments,
    });
    return result.assignments;
  }

  async analyzeQuestion(question: string): Promise<AnalyzeQuestionResult> {
    return this.request<AnalyzeQuestionResult>("analyze_question", { question });
  }

  // =========================================================================
  // Typed Event Listeners
  // =========================================================================

  onEvent<T extends EventType>(event: T, listener: EventListener<T>): this {
    return this.on(event, listener);
  }

  offEvent<T extends EventType>(event: T, listener: EventListener<T>): this {
    return this.off(event, listener);
  }
}
