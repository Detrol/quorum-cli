#!/usr/bin/env node
/**
 * Minimal Node.js client for Quorum IPC.
 *
 * Demonstrates how to connect to Quorum's JSON-RPC backend and run a discussion.
 *
 * Usage:
 *     node examples/node_ipc_client.js
 */

const { spawn } = require('child_process');
const path = require('path');
const readline = require('readline');

class QuorumClient {
  constructor() {
    this.process = null;
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.lineReader = null;
  }

  /**
   * Start the Quorum backend process.
   */
  async connect() {
    const projectRoot = path.join(__dirname, '..');

    return new Promise((resolve, reject) => {
      // Start the backend with --ipc flag
      this.process = spawn('python', ['-m', 'quorum', '--ipc'], {
        cwd: projectRoot,
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      // Set up line-by-line reading
      this.lineReader = readline.createInterface({
        input: this.process.stdout,
      });

      // Handle stderr
      this.process.stderr.on('data', (data) => {
        console.error(`[stderr] ${data}`);
      });

      // Handle process exit
      this.process.on('exit', (code) => {
        console.log(`Backend exited with code ${code}`);
      });

      // Wait for ready event
      console.log('Waiting for backend to be ready...');

      const onLine = (line) => {
        try {
          const data = JSON.parse(line);

          if (data.method === 'ready') {
            console.log(`Backend ready! Protocol version: ${data.params?.protocol_version}`);
            this.lineReader.off('line', onLine);
            this._startEventLoop();
            resolve();
          }
        } catch (e) {
          reject(new Error(`Failed to parse: ${line}`));
        }
      };

      this.lineReader.on('line', onLine);

      // Timeout after 30 seconds
      setTimeout(() => reject(new Error('Timeout waiting for ready')), 30000);
    });
  }

  /**
   * Start the event loop to handle responses and events.
   */
  _startEventLoop() {
    this.lineReader.on('line', (line) => {
      try {
        const data = JSON.parse(line);

        // Check if it's a response to a pending request
        if (data.id !== undefined && this.pendingRequests.has(data.id)) {
          const { resolve, reject } = this.pendingRequests.get(data.id);
          this.pendingRequests.delete(data.id);

          if (data.error) {
            reject(new Error(data.error.message));
          } else {
            resolve(data.result);
          }
        } else {
          // It's an event
          this._handleEvent(data);
        }
      } catch (e) {
        console.error(`Failed to parse: ${line}`);
      }
    });
  }

  /**
   * Handle incoming events.
   */
  _handleEvent(event) {
    const { method, params = {} } = event;

    switch (method) {
      case 'phase_start':
        console.log(`\n=== ${params.message} ===`);
        break;

      case 'thinking':
        console.log(`  [${params.model}] thinking...`);
        break;

      case 'independent_answer':
        console.log(`\n[${params.source}]`);
        console.log(`  ${(params.content || '').slice(0, 200)}...`);
        break;

      case 'critique':
        console.log(`\n[${params.source}] Critique:`);
        console.log(`  Agreements: ${(params.agreements || '').slice(0, 100)}...`);
        break;

      case 'chat_message':
        const role = params.role ? `(${params.role}) ` : '';
        console.log(`\n[${params.source}] ${role}`);
        console.log(`  ${(params.content || '').slice(0, 200)}...`);
        break;

      case 'final_position':
        console.log(`\n[${params.source}] Final Position (${params.confidence}):`);
        console.log(`  ${(params.position || '').slice(0, 200)}...`);
        break;

      case 'synthesis':
        console.log(`\n=== SYNTHESIS (${params.consensus}) ===`);
        console.log(`Synthesizer: ${params.synthesizer_model}`);
        console.log(`\n${(params.synthesis || '').slice(0, 500)}...`);
        break;

      case 'discussion_complete':
        console.log(`\nDiscussion complete! (${params.messages_count} messages)`);
        break;

      case 'phase_complete':
        console.log(`\n[Phase ${params.completed_phase} complete]`);
        // In a real client, wait for user input and send resume_discussion
        break;

      case 'discussion_error':
        console.log(`\nERROR: ${params.error}`);
        break;

      default:
        // Ignore unknown events
        break;
    }
  }

  /**
   * Send a JSON-RPC request and wait for response.
   */
  async request(method, params = {}) {
    this.requestId++;
    const requestId = this.requestId;

    const request = {
      jsonrpc: '2.0',
      id: requestId,
      method,
      params,
    };

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(requestId, { resolve, reject });

      const line = JSON.stringify(request) + '\n';
      this.process.stdin.write(line);
    });
  }

  /**
   * Close the connection.
   */
  close() {
    if (this.process) {
      this.process.stdin.end();
    }
  }
}

/**
 * Example: List models and run a simple discussion.
 */
async function main() {
  const client = new QuorumClient();

  try {
    // Connect to backend
    await client.connect();

    // Initialize
    const initResult = await client.request('initialize', { protocol_version: '1.0.0' });
    console.log(`Initialized: ${initResult.name} v${initResult.version}`);
    console.log(`Providers: ${initResult.providers.join(', ')}`);

    // List available models
    const modelsResult = await client.request('list_models');
    console.log('\nAvailable models:');
    for (const [provider, models] of Object.entries(modelsResult.models)) {
      console.log(`  ${provider}:`);
      for (const model of models) {
        const validated = modelsResult.validated?.includes(model.id) ? '(validated)' : '';
        console.log(`    - ${model.id} ${validated}`);
      }
    }

    // Get user settings
    const settings = await client.request('get_user_settings');
    const selected = settings.selected_models || [];

    if (selected.length < 2) {
      console.log('\nNot enough models selected. Please run Quorum UI first to select models.');
      return;
    }

    console.log(`\nSelected models: ${selected.join(', ')}`);

    // Run a discussion
    console.log('\n' + '='.repeat(60));
    console.log('Starting discussion...');
    console.log('='.repeat(60));

    const result = await client.request('run_discussion', {
      question: 'What is 2+2?',
      model_ids: selected.slice(0, 2), // Use first 2 selected models
      options: {
        method: 'standard',
        max_turns: 2,
      },
    });

    console.log(`\nDiscussion result: ${JSON.stringify(result)}`);

  } catch (e) {
    console.error(`Error: ${e.message}`);
    throw e;

  } finally {
    client.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
