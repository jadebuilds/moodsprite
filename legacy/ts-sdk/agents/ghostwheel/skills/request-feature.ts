import type { SkillDefinition } from '@zeroclaw/sdk';

export const requestFeature: SkillDefinition = {
  name: 'request-feature',
  title: 'Request a Feature',
  description: 'Submit a feature request. Ghostwheel will assess feasibility and tag Jade for input.',
  fields: [
    { name: 'title', type: 'text', label: 'Feature Title', required: true },
    { name: 'description', type: 'textarea', label: 'Description', required: true },
    { name: 'requestedBy', type: 'text', label: 'Requested By' },
  ],
  handler: async (input, ctx) => {
    const { title, description, requestedBy } = input;

    // Announce in Signal group
    await ctx.signal.sendGroup(
      `[Feature Request] ${title}\nFrom: ${requestedBy || 'anonymous'}\n${description}`,
    );

    // LLM feasibility assessment
    const assessment = await ctx.llm.chat(
      `Assess the feasibility of this feature request. Consider complexity, value, and any concerns:\n\nTitle: ${title}\nDescription: ${description}`,
      { system: ctx.config.personality },
    );

    await ctx.signal.sendGroup(`[Ghostwheel Assessment] ${assessment}\n\n@jade — your input requested.`);

    return {
      success: true,
      message: `Feature request submitted: ${title}`,
      data: { assessment },
    };
  },
};
