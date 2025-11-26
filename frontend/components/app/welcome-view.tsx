import { Button } from '@/components/livekit/button';

function PhysicsWallahIcon() {
  return (
    <svg
      width="96"
      height="96"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-6 size-24 text-primary"
    >
      {/* Book and person icon representing education */}
      <path
        d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"
        fill="currentColor"
      />
      <circle cx="12" cy="17" r="1.5" fill="currentColor" />
      <path
        d="M12 14c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"
        fill="currentColor"
        opacity="0.7"
      />
    </svg>
  );
}

function PhysicsWallahLogo() {
  return (
    <div className="mb-8 text-center">
      <h1 className="text-6xl font-bold tracking-tight text-primary">Physics Wallah</h1>
      <p className="text-sm mt-2 tracking-widest uppercase text-muted-foreground">Your Education Partner</p>
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
        <PhysicsWallahLogo />
        
        <PhysicsWallahIcon />

        <h2 className="text-3xl font-bold text-foreground mb-3">
          Discover India's Best Exam Prep Courses
        </h2>
        
        <p className="text-muted-foreground max-w-md mb-8 text-sm">
          Talk to our AI representative to learn about <span className="font-semibold text-primary">JEE</span>, <span className="font-semibold text-primary">NEET</span>, and <span className="font-semibold text-primary">Board Exam</span> courses. Get instant answers about pricing, features, and batch schedules.
        </p>

        <Button 
          variant="primary" 
          size="lg" 
          onClick={onStartCall} 
          className="mt-4 px-12 py-6 text-lg font-bold hover:scale-105 transition-all"
        >
          💬 TALK TO US
        </Button>

        <div className="mt-8 pt-6 w-full border-t border-border">
          <p className="text-xs text-muted-foreground">
            Powered by <span className="font-semibold text-primary">Murf Falcon TTS</span> • AI Voice Agent for instant course support
          </p>
        </div>
      </section>
    </div>
  );
};
