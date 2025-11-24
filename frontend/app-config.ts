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
  companyName: 'WellnessCompanion',
  pageTitle: 'Wellness Companion | AI Voice Check-In',
  pageDescription: 'Your daily health and wellness voice companion',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#4A90E2',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#6BA3E8',
  startButtonText: '✨ Start Check-In',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
