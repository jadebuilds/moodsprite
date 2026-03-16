import type { SkillDefinition } from '@zeroclaw/sdk';

export const reportBug: SkillDefinition = {
  name: 'report-bug',
  title: 'Report a Bug',
  description: 'Report a bug for triage and analysis. Ghostwheel will analyze the report, attempt a diagnosis, and escalate to Jade if needed.',
  fields: [
    { name: 'summary', type: 'text', label: 'Summary', required: true },
    { name: 'details', type: 'textarea', label: 'Details' },
    { name: 'severity', type: 'select', label: 'Severity', options: ['low', 'medium', 'high'] },
    { name: 'context', type: 'textarea', label: 'Additional Context' },
  ],
  handler: async (input, ctx) => {
    const { summary, details, severity, context } = input;
    const severityLabel = severity || 'medium';

    // Announce in Signal group
    await ctx.signal.sendGroup(
      `[Bug Report] ${severityLabel.toUpperCase()}: ${summary}\n${details || '(no details)'}`,
    );

    // LLM analysis
    const analysis = await ctx.llm.chat(
      `Analyze this bug report and provide a brief diagnosis:\n\nSummary: ${summary}\nSeverity: ${severityLabel}\nDetails: ${details || 'none'}\nContext: ${context || 'none'}`,
      { system: ctx.config.personality },
    );

    // Post analysis
    await ctx.signal.sendGroup(`[Ghostwheel Analysis] ${analysis}`);

    return {
      success: true,
      message: `Bug reported and analyzed. Severity: ${severityLabel}`,
      data: { analysis },
    };
  },
};
