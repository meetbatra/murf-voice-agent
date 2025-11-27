import { Button } from '@/components/livekit/button';

function SecureBankIcon() {
  return (
    <svg
      width="96"
      height="96"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-6 size-24 text-blue-600"
    >
      {/* Shield icon representing security and protection */}
      <path
        d="M12 2L4 6v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V6l-8-4z"
        fill="currentColor"
      />
      <path
        d="M12 2L4 6v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V6l-8-4zm0 3.18l6 2.7v4.62c0 4.35-2.78 8.4-6 9.5-3.22-1.1-6-5.15-6-9.5V7.88l6-2.7z"
        fill="white"
        opacity="0.3"
      />
      <path
        d="M10 13l-2-2-1.41 1.41L10 15.83l6-6-1.41-1.41L10 13z"
        fill="white"
      />
    </svg>
  );
}

function SecureBankLogo() {
  return (
    <div className="mb-8 text-center">
      <h1 className="text-6xl font-bold tracking-tight text-blue-600">SecureBank</h1>
      <p className="text-sm mt-2 tracking-widest uppercase text-muted-foreground">Fraud Prevention Department</p>
    </div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="min-h-screen flex items-center justify-center px-4">
      <section className="bg-card rounded-3xl p-12 max-w-2xl w-full shadow-2xl flex flex-col items-center text-center" style={{ boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
        <SecureBankLogo />
        
        <SecureBankIcon />

        <h2 className="text-3xl font-bold text-foreground mb-3">
          Important: Suspicious Activity Detected
        </h2>
        
        <p className="text-muted-foreground max-w-md mb-8 text-sm">
          Our <span className="font-semibold text-blue-600">Fraud Prevention</span> team has detected unusual activity on your account. Please verify your recent transactions by speaking with our <span className="font-semibold text-blue-600">AI Fraud Specialist</span>.
        </p>

        <Button 
          variant="primary" 
          size="lg" 
          onClick={onStartCall} 
          className="mt-4 px-12 py-6 text-lg font-bold hover:scale-105 transition-all bg-blue-600 hover:bg-blue-700"
        >
          🛡️ VERIFY NOW
        </Button>

        <div className="mt-8 pt-6 w-full border-t border-border">
          <p className="text-xs text-muted-foreground">
            Powered by <span className="font-semibold text-blue-600">Murf Falcon TTS</span> • Secure AI Voice Verification
          </p>
        </div>
      </section>
    </div>
  );
};
