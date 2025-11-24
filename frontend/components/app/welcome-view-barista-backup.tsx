import { Button } from '@/components/livekit/button';

function CoffeeCupIcon() {
  return (
    <svg
      width="96"
      height="96"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-6 size-24"
      style={{ color: '#8B6F47' }}
    >
      <path
        d="M2 19h18v2H2v-2zm2-7h12c0 2.76-2.24 5-5 5H7c-2.76 0-5-2.24-5-5h2zm0-2V4h12v6H4zm14 0V4h1c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2h-1zm-1-8H3c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1h14c.55 0 1-.45 1-1V3c0-.55-.45-1-1-1z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="0.5"
      />
    </svg>
  );
}

function MoonBucksLogo() {
  return (
    <div className="mb-8 text-center">
      <h1 className="text-6xl font-bold tracking-tight" style={{ color: '#D4A574' }}>MoonBucks</h1>
      <p className="text-sm mt-2 tracking-widest uppercase" style={{ color: '#B8956A' }}>Coffee & Voice AI</p>
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
        <MoonBucksLogo />
        
        <CoffeeCupIcon />

        <h2 className="text-3xl font-bold text-foreground mb-3">
          Welcome to MoonBucks
        </h2>

        <p className="text-muted-foreground max-w-md mb-2 text-lg leading-relaxed">
          Your AI barista is ready to take your order!
        </p>
        
        <p className="text-muted-foreground max-w-md mb-8 text-sm">
          Simply click the button below and tell me what you'd like to drink today.
        </p>

        <Button 
          variant="primary" 
          size="lg" 
          onClick={onStartCall} 
          className="mt-4 px-12 py-6 text-lg font-bold hover:scale-105 transition-all"
          style={{ 
            background: 'linear-gradient(135deg, #6F4E37 0%, #5D4037 100%)',
            color: '#FFF8E7',
            border: 'none'
          }}
        >
          {startButtonText}
        </Button>

        <div className="mt-8 pt-6 w-full" style={{ borderTop: '1px solid #E8DCC4' }}>
          <p className="text-xs" style={{ color: '#8B7355' }}>
            Powered by <span className="font-semibold" style={{ color: '#6F4E37' }}>Murf Falcon TTS</span> • Lightning-fast voice AI
          </p>
        </div>
      </section>
    </div>
  );
};
