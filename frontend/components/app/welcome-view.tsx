import { Button } from '@/components/livekit/button';

function TutorIcon() {
  return (
    <svg
      width="96"
      height="96"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-6 size-24 text-primary"
    >
      {/* Graduation cap */}
      <path
        d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"
        fill="currentColor"
      />
    </svg>
  );
}

function TutorLogo() {
  return (
    <div className="mb-8 text-center">
      <h1 className="text-6xl font-bold tracking-tight text-primary">Teach-the-Tutor</h1>
      <p className="text-sm mt-2 tracking-widest uppercase text-muted-foreground">Active Recall Learning Coach</p>
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
        <TutorLogo />
        
        <TutorIcon />

        <h2 className="text-3xl font-bold text-foreground mb-3">
          Master Programming Through Active Recall
        </h2>
        
        <p className="text-muted-foreground max-w-md mb-8 text-sm">
          Choose <span className="font-semibold text-primary">Learn Mode</span> to understand concepts, <span className="font-semibold text-primary">Quiz Mode</span> to test yourself, or <span className="font-semibold text-primary">Teach Back Mode</span> to explain what you've learned.
        </p>

        <Button 
          variant="primary" 
          size="lg" 
          onClick={onStartCall} 
          className="mt-4 px-12 py-6 text-lg font-bold hover:scale-105 transition-all"
        >
          ✨ START LEARNING
        </Button>

        <div className="mt-8 pt-6 w-full border-t border-border">
          <p className="text-xs text-muted-foreground">
            Powered by <span className="font-semibold text-primary">Murf Falcon TTS</span> • Multi-voice AI tutor with Matthew, Alicia & Ken
          </p>
        </div>
      </section>
    </div>
  );
};
