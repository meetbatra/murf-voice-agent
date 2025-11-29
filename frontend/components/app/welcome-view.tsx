import { Button } from '@/components/livekit/button';

function EpicQuestIcon() {
  return (
    <div className="relative">
      {/* Glowing background effect */}
      <div className="absolute inset-0 blur-2xl opacity-40 bg-linear-to-br from-purple-500 to-violet-600 rounded-full scale-150 animate-pulse"></div>
      
      <svg
        width="96"
        height="96"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="mb-6 size-24 text-purple-600 relative z-10 drop-shadow-2xl"
      >
        {/* D20 dice icon representing D&D gaming */}
        <path
          d="M12 2 L22 8 L22 16 L12 22 L2 16 L2 8 Z"
          fill="currentColor"
          opacity="0.3"
        />
        <path
          d="M12 2 L22 8 M22 8 L22 16 M22 16 L12 22 M12 22 L2 16 M2 16 L2 8 M2 8 L12 2 M12 2 L12 22 M2 8 L22 16 M22 8 L2 16"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        <circle cx="12" cy="12" r="2.5" fill="white" />
        <text x="12" y="14" fontSize="4" textAnchor="middle" fill="#9333ea" fontWeight="bold">20</text>
      </svg>
    </div>
  );
}

function EpicQuestLogo() {
  return (
    <div className="mb-8 text-center relative">
      {/* Decorative crossed swords */}
      <div className="absolute -top-4 left-1/2 -translate-x-1/2 text-purple-600/20 text-4xl">⚔️</div>
      
      <h1 className="text-6xl font-bold tracking-tight bg-linear-to-r from-purple-600 via-violet-500 to-purple-600 bg-clip-text text-transparent drop-shadow-lg">Epic Quest</h1>
      
      {/* Decorative line with gem */}
      <div className="flex items-center justify-center gap-2 mt-3">
        <div className="h-px w-12 bg-linear-to-r from-transparent to-purple-600/50"></div>
        <div className="w-2 h-2 rotate-45 bg-purple-600"></div>
        <div className="h-px w-12 bg-linear-to-l from-transparent to-purple-600/50"></div>
      </div>
      
      <p className="text-sm mt-3 tracking-widest uppercase text-muted-foreground font-semibold">AI Dungeon Master</p>
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
    <div ref={ref} className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden pt-20">
      {/* Floating particles effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-1 h-1 bg-purple-500 rounded-full animate-ping" style={{ animationDuration: '3s', animationDelay: '0s' }}></div>
        <div className="absolute top-1/3 right-1/4 w-1 h-1 bg-violet-500 rounded-full animate-ping" style={{ animationDuration: '4s', animationDelay: '1s' }}></div>
        <div className="absolute bottom-1/3 left-1/3 w-1 h-1 bg-purple-400 rounded-full animate-ping" style={{ animationDuration: '5s', animationDelay: '2s' }}></div>
      </div>
      
      <section className="bg-card/95 backdrop-blur-sm rounded-3xl p-12 max-w-2xl w-full shadow-2xl flex flex-col items-center text-center relative z-10 border border-purple-500/20" style={{ boxShadow: '0 25px 50px -12px rgba(147, 51, 234, 0.3), 0 0 0 1px rgba(147, 51, 234, 0.1)' }}>
        {/* Top corner decorations */}
        <div className="absolute top-4 left-4 text-purple-600/20 text-2xl">✦</div>
        <div className="absolute top-4 right-4 text-purple-600/20 text-2xl">✦</div>
        
        <EpicQuestLogo />
        
        <EpicQuestIcon />

        <h2 className="text-3xl font-bold text-foreground mb-3 relative">
          Your AI Dungeon Master Awaits
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-24 h-1 bg-linear-to-r from-transparent via-purple-600 to-transparent"></div>
        </h2>
        
        <p className="text-muted-foreground max-w-md mb-8 text-base leading-relaxed mt-6">
          Meet <span className="font-bold text-purple-600 bg-purple-600/10 px-2 py-0.5 rounded">Gandor</span>, your dramatic AI Game Master. Create characters, explore perilous dungeons, battle fearsome monsters, and forge your legend—all by voice!
        </p>

        <Button 
          variant="primary" 
          size="lg" 
          onClick={onStartCall} 
          className="mt-4 px-12 py-6 text-lg font-bold hover:scale-105 transition-all bg-linear-to-r from-purple-600 to-violet-600 hover:from-purple-700 hover:to-violet-700 shadow-lg shadow-purple-500/50 border border-purple-400/30"
        >
          ⚔️ START ADVENTURE
        </Button>

        <div className="mt-10 pt-6 w-full border-t border-purple-500/20">
          <p className="text-xs text-muted-foreground">
            Powered by <span className="font-semibold text-purple-600">Murf Falcon TTS</span> • <span className="text-purple-500">🎲</span> AI D&D Voice Game Master
          </p>
        </div>
        
        {/* Bottom corner decorations */}
        <div className="absolute bottom-4 left-4 text-purple-600/20 text-2xl">✦</div>
        <div className="absolute bottom-4 right-4 text-purple-600/20 text-2xl">✦</div>
      </section>
    </div>
  );
};
