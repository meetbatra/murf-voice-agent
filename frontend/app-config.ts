export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  // for LiveKit Cloud Sandbox
  sandboxId?: string;
  agentName?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Epic Quest',
  pageTitle: 'Epic Quest | AI Dungeon Master',
  pageDescription: 'Embark on voice-powered D&D adventures with your AI Game Master',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#9333ea',  // Purple for fantasy/magic theme
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#a855f7',  // Lighter purple for dark mode
  startButtonText: '⚔️ START ADVENTURE',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
