import { JironClient } from './client.js';
import type { JironDocument } from './types.js';

export interface PeerInfo {
  url: string;
  catalog: JironDocument;
  lastSeen: number;
}

export class PeerDiscovery {
  private peers = new Map<string, PeerInfo>();
  private refreshInterval: ReturnType<typeof setInterval> | null = null;

  constructor(
    private client: JironClient,
    private peerUrls: string[],
  ) {}

  async discoverAll(): Promise<PeerInfo[]> {
    const results: PeerInfo[] = [];
    for (const url of this.peerUrls) {
      try {
        const catalog = await this.client.discover(url);
        const info: PeerInfo = { url, catalog, lastSeen: Date.now() };
        this.peers.set(url, info);
        results.push(info);
      } catch (err) {
        console.error(`[discovery] failed to discover ${url}:`, (err as Error).message);
      }
    }
    return results;
  }

  startRefresh(intervalMs = 60_000): void {
    this.refreshInterval = setInterval(() => {
      this.client.clearCache();
      this.discoverAll().catch(err => {
        console.error('[discovery] refresh error:', err);
      });
    }, intervalMs);
  }

  stopRefresh(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  getPeer(url: string): PeerInfo | undefined {
    return this.peers.get(url);
  }

  getAllPeers(): PeerInfo[] {
    return [...this.peers.values()];
  }

  findSkill(skillName: string): { peer: PeerInfo; href: string } | undefined {
    for (const peer of this.peers.values()) {
      const link = peer.catalog.links.find(l => l.href === `/skills/${skillName}`);
      if (link) return { peer, href: `${peer.url}${link.href}` };
    }
    return undefined;
  }
}
