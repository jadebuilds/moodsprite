import { readFileSync } from 'node:fs';
import { parse as parseYaml } from 'yaml';
import type { AgentConfig, AgentContext, SkillDefinition, MessageHandler, SignalMessage } from './types.js';
import { SignalClient } from './signal.js';
import { OllamaClient } from './llm.js';
import { JironServer } from './jiron/server.js';
import { JironClient } from './jiron/client.js';
import { PeerDiscovery } from './jiron/discovery.js';

function resolveEnv(value: string): string {
  return value.replace(/\$\{(\w+)\}/g, (_, key) => process.env[key] || '');
}

function resolveConfig(raw: Record<string, unknown>): AgentConfig {
  const resolve = (obj: unknown): unknown => {
    if (typeof obj === 'string') return resolveEnv(obj);
    if (Array.isArray(obj)) return obj.map(resolve);
    if (obj && typeof obj === 'object') {
      const out: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(obj)) {
        out[k] = resolve(v);
      }
      return out;
    }
    return obj;
  };
  return resolve(raw) as AgentConfig;
}

export class ZeroclawAgent {
  readonly config: AgentConfig;
  private skills: SkillDefinition[] = [];
  private messageHandler?: MessageHandler;

  private signal!: SignalClient;
  private llm!: OllamaClient;
  private jironServer!: JironServer;
  private jironClient!: JironClient;
  private discovery!: PeerDiscovery;

  constructor(configPath: string) {
    const raw = parseYaml(readFileSync(configPath, 'utf-8'));
    this.config = resolveConfig(raw);
  }

  skill(def: SkillDefinition): this {
    this.skills.push(def);
    return this;
  }

  onMessage(handler: MessageHandler): this {
    this.messageHandler = handler;
    return this;
  }

  async start(): Promise<void> {
    console.log(`[${this.config.name}] starting...`);

    // Init clients
    this.signal = new SignalClient(
      this.config.signal.phone,
      this.config.signal.apiUrl,
      this.config.signal.groupId,
    );
    this.llm = new OllamaClient(this.config.llm.url, this.config.llm.model);
    this.jironClient = new JironClient();
    this.discovery = new PeerDiscovery(this.jironClient, this.config.peers);

    // Init Jiron server
    this.jironServer = new JironServer(this.config, () => this.context());
    for (const s of this.skills) {
      this.jironServer.registerSkill(s);
    }
    await this.jironServer.start(this.config.jiron.port);

    // Wire Signal messages
    if (this.messageHandler) {
      const handler = this.messageHandler;
      this.signal.onMessage((msg: SignalMessage) => {
        handler(msg, this.context()).catch(err => {
          console.error(`[${this.config.name}] message handler error:`, err);
        });
      });
    }
    this.signal.startPolling();

    // Discover peers (non-blocking)
    this.discovery.discoverAll().then(peers => {
      console.log(`[${this.config.name}] discovered ${peers.length} peer(s)`);
    }).catch(err => {
      console.error(`[${this.config.name}] peer discovery failed:`, err);
    });
    this.discovery.startRefresh();

    console.log(`[${this.config.name}] ready`);

    // Keep alive
    await new Promise(() => {});
  }

  async stop(): Promise<void> {
    this.signal.stopPolling();
    this.discovery.stopRefresh();
    await this.jironServer.stop();
    console.log(`[${this.config.name}] stopped`);
  }

  context(): AgentContext {
    return {
      config: this.config,
      signal: this.signal,
      llm: this.llm,
      jiron: this.jironClient,
    };
  }
}
