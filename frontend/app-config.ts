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
  companyName: 'SecureBank',
  pageTitle: 'SecureBank Fraud Alert | Transaction Verification',
  pageDescription: 'Secure fraud prevention and transaction verification service',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#2563eb',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#3b82f6',
  startButtonText: '🛡️ VERIFY NOW',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
