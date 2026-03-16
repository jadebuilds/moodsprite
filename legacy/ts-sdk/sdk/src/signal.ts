import type { SignalMessage } from './types.js';

export class SignalClient {
  private polling = false;
  private handlers: ((msg: SignalMessage) => void)[] = [];

  constructor(
    private phone: string,
    private apiUrl: string,
    private groupId: string,
  ) {}

  onMessage(handler: (msg: SignalMessage) => void) {
    this.handlers.push(handler);
  }

  async sendGroup(text: string): Promise<void> {
    await fetch(`${this.apiUrl}/v2/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        number: this.phone,
        recipients: [],
        base64_attachments: [],
        group_id: this.groupId,
      }),
    });
  }

  async sendDM(text: string, recipient: string): Promise<void> {
    await fetch(`${this.apiUrl}/v2/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        number: this.phone,
        recipients: [recipient],
      }),
    });
  }

  async reply(msg: SignalMessage, text: string): Promise<void> {
    if (msg.isGroupMessage) {
      await this.sendGroup(text);
    } else {
      await this.sendDM(text, msg.source);
    }
  }

  startPolling(intervalMs = 1000): void {
    this.polling = true;
    this.poll(intervalMs);
  }

  stopPolling(): void {
    this.polling = false;
  }

  private async poll(intervalMs: number): Promise<void> {
    while (this.polling) {
      try {
        const res = await fetch(`${this.apiUrl}/v1/receive/${encodeURIComponent(this.phone)}`);
        if (res.ok) {
          const envelopes = await res.json() as unknown[];
          for (const raw of envelopes) {
            const msg = this.parseMessage(raw);
            if (msg) {
              for (const handler of this.handlers) {
                handler(msg);
              }
            }
          }
        }
      } catch (err) {
        console.error('[signal] poll error:', (err as Error).message);
      }
      await new Promise(r => setTimeout(r, intervalMs));
    }
  }

  private parseMessage(raw: unknown): SignalMessage | null {
    const envelope = (raw as { envelope?: Record<string, unknown> }).envelope;
    if (!envelope?.dataMessage) return null;

    const data = envelope.dataMessage as Record<string, unknown>;
    const groupInfo = data.groupInfo as { groupId?: string } | undefined;

    return {
      source: envelope.source as string,
      text: (data.message as string) || '',
      timestamp: data.timestamp as number,
      groupId: groupInfo?.groupId,
      isGroupMessage: !!groupInfo,
    };
  }
}
