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
  companyName: 'ShopSmart',
  pageTitle: 'ShopSmart | AI Shopping Assistant',
  pageDescription: 'Shop smarter with voice-powered AI shopping assistant',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#16a34a',  // Green for e-commerce/shopping theme
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#22c55e',  // Lighter green for dark mode
  startButtonText: '🛒 START SHOPPING',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
