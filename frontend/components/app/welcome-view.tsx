import { Button } from '@/components/livekit/button';
import { useState } from 'react';

function GameIcon() {
  return (
    <div className="relative">
      {/* Glowing background effect */}
      <div className="absolute inset-0 blur-2xl opacity-40 bg-linear-to-br from-purple-500 to-violet-600 rounded-full scale-150 animate-pulse"></div>
      
      <svg
        width="80"
        height="80"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="mb-4 size-20 text-purple-600 relative z-10 drop-shadow-2xl"
      >
        {/* Thinking face */}
        <circle
          cx="12"
          cy="12"
          r="9"
          fill="currentColor"
          opacity="0.3"
        />
        {/* Eyes */}
        <circle cx="9" cy="10" r="1.5" fill="currentColor" />
        <circle cx="15" cy="10" r="1.5" fill="currentColor" />
        {/* Thinking expression */}
        <path
          d="M8 15c0.5-0.5 1.5-0.5 2-0.5s1.5 0 2 0.5"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          fill="none"
        />
        {/* Sparkles */}
        <circle cx="5" cy="6" r="0.5" fill="white" opacity="0.8" />
        <circle cx="19" cy="7" r="0.5" fill="white" opacity="0.8" />
      </svg>
    </div>
  );
}

function ImprovSituationsLogo() {
  return (
    <div className="mb-6 text-center relative">
      {/* Decorative game icon */}
      <div className="absolute -top-4 left-1/2 -translate-x-1/2 text-purple-600/20 text-4xl">🎮</div>
      
      <h1 className="text-5xl font-bold tracking-tight bg-linear-to-r from-purple-600 via-violet-500 to-purple-600 bg-clip-text text-transparent drop-shadow-lg">Improv Situations</h1>
      
      {/* Decorative line with star */}
      <div className="flex items-center justify-center gap-2 mt-3">
        <div className="h-px w-12 bg-linear-to-r from-transparent to-purple-600/50"></div>
        <div className="text-purple-600 text-xs">★</div>
        <div className="h-px w-12 bg-linear-to-l from-transparent to-purple-600/50"></div>
      </div>
      
      <p className="text-sm mt-3 tracking-widest uppercase text-muted-foreground font-semibold">Theatrical Improv Battle</p>
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
  const [playerName, setPlayerName] = useState('');

  const handleStart = () => {
    if (playerName.trim()) {
      // Store player name for the session
      sessionStorage.setItem('improv_player_name', playerName.trim());
      onStartCall();
    }
  };

  return (
    <div ref={ref} className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden pt-20">
      {/* Floating particles effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-1 h-1 bg-purple-500 rounded-full animate-ping" style={{ animationDuration: '3s', animationDelay: '0s' }}></div>
        <div className="absolute top-1/3 right-1/4 w-1 h-1 bg-violet-500 rounded-full animate-ping" style={{ animationDuration: '4s', animationDelay: '1s' }}></div>
        <div className="absolute bottom-1/3 left-1/3 w-1 h-1 bg-purple-400 rounded-full animate-ping" style={{ animationDuration: '5s', animationDelay: '2s' }}></div>
      </div>
      
      <section className="bg-card/95 backdrop-blur-sm rounded-3xl p-10 max-w-lg w-full shadow-2xl flex flex-col items-center text-center relative z-10 border border-purple-500/20" style={{ boxShadow: '0 25px 50px -12px rgba(168, 85, 247, 0.3), 0 0 0 1px rgba(168, 85, 247, 0.1)' }}>
        {/* Top corner decorations */}
        <div className="absolute top-4 left-4 text-purple-600/20 text-2xl">✦</div>
        <div className="absolute top-4 right-4 text-purple-600/20 text-2xl">✦</div>
        
        <ImprovSituationsLogo />
        
        <GameIcon />

        <h2 className="text-2xl font-bold text-foreground mb-2 relative">
          Handle the Weird
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-24 h-1 bg-linear-to-r from-transparent via-purple-600 to-transparent"></div>
        </h2>
        
        <p className="text-muted-foreground max-w-md mb-6 text-sm leading-relaxed mt-4">
          Face bizarre, unexpected situations and show us your creative solutions. Five rounds of <span className="font-bold text-purple-600 bg-purple-600/10 px-2 py-0.5 rounded">weird scenarios</span>. Can you think outside the box?
        </p>

        {/* Name Input */}
        <div className="w-full max-w-md mb-6">
          <label htmlFor="player-name" className="block text-sm font-semibold text-muted-foreground mb-2 text-left">
            Contestant Name
          </label>
          <input
            id="player-name"
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleStart()}
            placeholder="Enter your name..."
            className="w-full px-4 py-3 rounded-lg bg-background/50 border-2 border-purple-500/30 focus:border-purple-500 focus:outline-none text-foreground placeholder:text-muted-foreground/50 transition-all"
          />
        </div>

        <Button 
          variant="primary" 
          size="lg" 
          onClick={handleStart}
          disabled={!playerName.trim()}
          className="mt-2 px-10 py-5 text-base font-bold hover:scale-105 transition-all bg-linear-to-r from-purple-600 to-violet-600 hover:from-purple-700 hover:to-violet-700 shadow-lg shadow-purple-500/50 border border-purple-400/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          🎮 START IMPROV BATTLE
        </Button>

        <div className="mt-6 pt-4 w-full border-t border-purple-500/20">
          <p className="text-xs text-muted-foreground">
            Powered by <span className="font-semibold text-purple-600">Murf Falcon TTS</span> • <span className="text-purple-500">🎮</span> AI Improv Game
          </p>
        </div>
        
        {/* Bottom corner decorations */}
        <div className="absolute bottom-4 left-4 text-purple-600/20 text-2xl">✦</div>
        <div className="absolute bottom-4 right-4 text-purple-600/20 text-2xl">✦</div>
      </section>
    </div>
  );
};
