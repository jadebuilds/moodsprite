import type { SkillDefinition } from '@zeroclaw/sdk';

export const referFriend: SkillDefinition = {
  name: 'refer-friend',
  title: 'Refer a Friend',
  description: 'Refer someone to get their own Zeroclaw agent. Requires admin approval before provisioning.',
  fields: [
    { name: 'friendName', type: 'text', label: 'Friend\'s Name', required: true },
    { name: 'friendPhone', type: 'text', label: 'Friend\'s Phone Number', required: true },
    { name: 'agentName', type: 'text', label: 'Desired Agent Name', required: true },
    { name: 'referredBy', type: 'text', label: 'Referred By', required: true },
    { name: 'notes', type: 'textarea', label: 'Notes' },
  ],
  handler: async (input, ctx) => {
    const { friendName, friendPhone, agentName, referredBy, notes } = input;

    // Announce in Signal group and await manual approval
    await ctx.signal.sendGroup(
      `[Referral] ${referredBy} is referring ${friendName} (${friendPhone}).\n` +
      `Desired agent name: ${agentName}\n` +
      `${notes ? `Notes: ${notes}\n` : ''}` +
      `\n@jade — reply "approve" to provision.`,
    );

    return {
      success: true,
      message: `Referral submitted for ${friendName}. Awaiting admin approval.`,
      data: { friendName, agentName, status: 'pending_approval' },
    };
  },
};
