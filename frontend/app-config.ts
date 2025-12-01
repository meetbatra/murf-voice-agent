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
  companyName: 'ImprovArena',
  pageTitle: 'Improv Situations | Weird Scenarios Game',
  pageDescription: 'Face bizarre scenarios and show off your creative improvisation skills',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#a855f7',  // Purple for comedy theme
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#c084fc',  // Lighter purple for dark mode
  startButtonText: '🎮 START GAME',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
