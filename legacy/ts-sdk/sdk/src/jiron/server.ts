import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import type { SkillDefinition, AgentConfig, AgentContext } from '../types.js';
import { buildRootDocument, buildSkillDocument, buildResultDocument, renderDocument } from './document.js';

export class JironServer {
  private skills = new Map<string, SkillDefinition>();
  private server: ReturnType<typeof createServer>;
  private getContext: () => AgentContext;

  constructor(config: AgentConfig, getContext: () => AgentContext) {
    this.getContext = getContext;
    this.server = createServer((req, res) => this.handleRequest(req, res, config));
  }

  registerSkill(skill: SkillDefinition): void {
    this.skills.set(skill.name, skill);
  }

  start(port: number): Promise<void> {
    return new Promise(resolve => {
      this.server.listen(port, () => {
        console.log(`[jiron] listening on :${port}`);
        resolve();
      });
    });
  }

  stop(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.server.close(err => err ? reject(err) : resolve());
    });
  }

  private async handleRequest(req: IncomingMessage, res: ServerResponse, config: AgentConfig): Promise<void> {
    const url = new URL(req.url || '/', `http://localhost`);
    const accept = req.headers.accept || '';

    try {
      if (url.pathname === '/' && req.method === 'GET') {
        const doc = buildRootDocument(config, [...this.skills.values()]);
        const { body, contentType } = renderDocument(doc, accept);
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(body);
        return;
      }

      const skillMatch = url.pathname.match(/^\/skills\/([a-z0-9-]+)$/);
      if (skillMatch) {
        const skill = this.skills.get(skillMatch[1]);
        if (!skill) {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Skill not found' }));
          return;
        }

        if (req.method === 'GET') {
          const doc = buildSkillDocument(skill);
          const { body, contentType } = renderDocument(doc, accept);
          res.writeHead(200, { 'Content-Type': contentType });
          res.end(body);
          return;
        }

        if (req.method === 'POST') {
          const input = await parseBody(req);
          const result = await skill.handler(input, this.getContext());
          const doc = buildResultDocument(`${skill.title} — Result`, {
            success: result.success,
            message: result.message,
            ...result.data,
          });
          const { body, contentType } = renderDocument(doc, accept);
          res.writeHead(result.success ? 200 : 422, { 'Content-Type': contentType });
          res.end(body);
          return;
        }
      }

      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
    } catch (err) {
      console.error('[jiron] request error:', err);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Internal server error' }));
    }
  }
}

function parseBody(req: IncomingMessage): Promise<Record<string, string>> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on('data', c => chunks.push(c));
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString();
      const contentType = req.headers['content-type'] || '';

      if (contentType.includes('application/json')) {
        try {
          resolve(JSON.parse(raw));
        } catch {
          reject(new Error('Invalid JSON'));
        }
        return;
      }

      // application/x-www-form-urlencoded
      const params = new URLSearchParams(raw);
      const result: Record<string, string> = {};
      for (const [k, v] of params) {
        result[k] = v;
      }
      resolve(result);
    });
    req.on('error', reject);
  });
}
