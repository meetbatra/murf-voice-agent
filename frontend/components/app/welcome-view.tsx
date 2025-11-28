import { Button } from '@/components/livekit/button';

function FreshMartIcon() {
  return (
    <svg
      width="96"
      height="96"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-6 size-24 text-green-600"
    >
      {/* Shopping bag icon representing grocery shopping */}
      <path
        d="M7 4h10c1.1 0 2 .9 2 2v14c0 1.1-.9 2-2 2H7c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"
        fill="currentColor"
      />
      <path
        d="M9 2c0 1.1.9 2 2 2h2c1.1 0 2-.9 2-2M7 8h10"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="12" cy="14" r="3" fill="white" opacity="0.5" />
    </svg>
  );
}

function FreshMartLogo() {
  return (
    <div className="mb-8 text-center">
      <h1 className="text-6xl font-bold tracking-tight text-green-600">FreshMart</h1>
      <p className="text-sm mt-2 tracking-widest uppercase text-muted-foreground">Grocery Shopping Assistant</p>
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
        <FreshMartLogo />
        
        <FreshMartIcon />

        <h2 className="text-3xl font-bold text-foreground mb-3">
          Welcome to Voice-Powered Shopping
        </h2>
        
        <p className="text-muted-foreground max-w-md mb-8 text-sm">
          Meet <span className="font-semibold text-green-600">Alicia</span>, your friendly shopping assistant. Simply tell her what you need, add items to your cart, and place your order—all by voice!
        </p>

        <Button 
          variant="primary" 
          size="lg" 
          onClick={onStartCall} 
          className="mt-4 px-12 py-6 text-lg font-bold hover:scale-105 transition-all bg-green-600 hover:bg-green-700"
        >
          🛒 START SHOPPING
        </Button>

        <div className="mt-8 pt-6 w-full border-t border-border">
          <p className="text-xs text-muted-foreground">
            Powered by <span className="font-semibold text-green-600">Murf Falcon TTS</span> • AI Voice Shopping Assistant
          </p>
        </div>
      </section>
    </div>
  );
};
