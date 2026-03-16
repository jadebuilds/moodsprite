import { ZeroclawAgent } from '../../sdk/src/index.js';

const agent = new ZeroclawAgent(new URL('./agent.yml', import.meta.url).pathname);

agent
  .onMessage(async (msg, ctx) => {
    if (!msg.text.trim()) return;

    if (msg.isGroupMessage) {
      const mentioned = msg.text.toLowerCase().includes('@aya')
        || msg.text.toLowerCase().includes('aya');
      if (!mentioned) return;
    }

    const reply = await ctx.llm.chat(msg.text, { system: ctx.config.personality });
    await ctx.signal.reply(msg, reply);
  })
  .start();
