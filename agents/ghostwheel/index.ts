import { ZeroclawAgent } from '../../sdk/src/index.js';
import { reportBug } from './skills/report-bug.js';
import { requestFeature } from './skills/request-feature.js';
import { referFriend } from './skills/refer-friend.js';

const agent = new ZeroclawAgent(new URL('./agent.yml', import.meta.url).pathname);

agent
  .skill(reportBug)
  .skill(requestFeature)
  .skill(referFriend)
  .onMessage(async (msg, ctx) => {
    // Skip empty messages
    if (!msg.text.trim()) return;

    // Only respond to @-mentions in group, or all DMs
    if (msg.isGroupMessage) {
      const mentioned = msg.text.toLowerCase().includes('@ghostwheel')
        || msg.text.toLowerCase().includes('ghostwheel');
      if (!mentioned) return;
    }

    const reply = await ctx.llm.chat(msg.text, { system: ctx.config.personality });
    await ctx.signal.reply(msg, reply);
  })
  .start();
