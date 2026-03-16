export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatOptions {
  system?: string;
  history?: ChatMessage[];
  temperature?: number;
}

export class OllamaClient {
  constructor(
    private url: string,
    private model: string,
  ) {}

  async chat(prompt: string, options?: ChatOptions): Promise<string> {
    const messages: ChatMessage[] = [];

    if (options?.system) {
      messages.push({ role: 'system', content: options.system });
    }
    if (options?.history) {
      messages.push(...options.history);
    }
    messages.push({ role: 'user', content: prompt });

    const res = await fetch(`${this.url}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: this.model,
        messages,
        stream: false,
        ...(options?.temperature != null && { options: { temperature: options.temperature } }),
      }),
    });

    if (!res.ok) {
      throw new Error(`Ollama error ${res.status}: ${await res.text()}`);
    }

    const data = await res.json() as { message: { content: string } };
    return data.message.content;
  }

  async generate(prompt: string): Promise<string> {
    const res = await fetch(`${this.url}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: this.model, prompt, stream: false }),
    });

    if (!res.ok) {
      throw new Error(`Ollama error ${res.status}: ${await res.text()}`);
    }

    const data = await res.json() as { response: string };
    return data.response;
  }
}
