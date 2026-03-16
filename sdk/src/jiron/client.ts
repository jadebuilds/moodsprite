import type { JironDocument } from './types.js';
import type { SkillResult } from '../types.js';

export class JironClient {
  private catalogCache = new Map<string, JironDocument>();

  async discover(peerUrl: string): Promise<JironDocument> {
    const cached = this.catalogCache.get(peerUrl);
    if (cached) return cached;

    const res = await fetch(peerUrl, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Jiron discovery failed for ${peerUrl}: ${res.status}`);
    }
    const doc = await res.json() as JironDocument;
    this.catalogCache.set(peerUrl, doc);
    return doc;
  }

  async getSkill(peerUrl: string, skillName: string): Promise<JironDocument> {
    const res = await fetch(`${peerUrl}/skills/${skillName}`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Skill ${skillName} not found at ${peerUrl}: ${res.status}`);
    }
    return await res.json() as JironDocument;
  }

  async invoke(peerUrl: string, skillName: string, input: Record<string, string>): Promise<SkillResult> {
    const res = await fetch(`${peerUrl}/skills/${skillName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Jiron-Action': 'create',
      },
      body: JSON.stringify(input),
    });
    const doc = await res.json() as JironDocument;
    return {
      success: doc.data?.success as boolean ?? res.ok,
      message: doc.data?.message as string ?? doc.title,
      data: doc.data,
    };
  }

  clearCache(peerUrl?: string): void {
    if (peerUrl) {
      this.catalogCache.delete(peerUrl);
    } else {
      this.catalogCache.clear();
    }
  }
}
