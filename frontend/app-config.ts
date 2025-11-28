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
  companyName: 'FreshMart',
  pageTitle: 'FreshMart Grocery Ordering | Voice Shopping Assistant',
  pageDescription: 'Shop for groceries with your voice-powered shopping assistant',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#16a34a',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#22c55e',
  startButtonText: '🛒 START SHOPPING',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
