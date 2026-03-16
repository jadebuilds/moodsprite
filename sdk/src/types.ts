export interface AgentConfig {
  name: string;
  owner: string;
  signal: SignalConfig;
  llm: LLMConfig;
  jiron: JironConfig;
  peers: string[];
  personality: string;
}

export interface SignalConfig {
  phone: string;
  apiUrl: string;
  groupId: string;
}

export interface LLMConfig {
  url: string;
  model: string;
}

export interface JironConfig {
  port: number;
  hostname: string;
}

export interface FieldDef {
  name: string;
  type: 'text' | 'textarea' | 'select';
  label: string;
  required?: boolean;
  options?: string[];
}

export interface SkillResult {
  success: boolean;
  message: string;
  data?: Record<string, unknown>;
}

export interface SkillDefinition {
  name: string;
  title: string;
  description: string;
  fields: FieldDef[];
  handler: (input: Record<string, string>, ctx: AgentContext) => Promise<SkillResult>;
}

export interface SignalMessage {
  source: string;
  text: string;
  timestamp: number;
  groupId?: string;
  isGroupMessage: boolean;
}

export interface AgentContext {
  config: AgentConfig;
  signal: import('./signal.js').SignalClient;
  llm: import('./llm.js').OllamaClient;
  jiron: import('./jiron/client.js').JironClient;
}

export type MessageHandler = (msg: SignalMessage, ctx: AgentContext) => Promise<void>;
