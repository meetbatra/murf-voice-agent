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
  companyName: 'MoonBucks',
  pageTitle: 'MoonBucks | AI Voice Barista',
  pageDescription: 'Order your favorite coffee with our AI-powered voice barista',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#00704A',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#1B8758',
  startButtonText: '☕ Start Order',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
