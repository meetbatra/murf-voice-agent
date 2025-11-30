import { Button } from '@/components/livekit/button';

function ShoppingBagIcon() {
  return (
    <div className="relative">
      {/* Glowing background effect */}
      <div className="absolute inset-0 blur-2xl opacity-40 bg-linear-to-br from-green-500 to-emerald-600 rounded-full scale-150 animate-pulse"></div>
      
      <svg
        width="96"
        height="96"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="mb-6 size-24 text-green-600 relative z-10 drop-shadow-2xl"
      >
        {/* Shopping bag icon */}
        <path
          d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"
          fill="currentColor"
          opacity="0.3"
        />
        <path
          d="M3 6h18M6 2l-3 4M18 2l3 4M16 10a4 4 0 0 1-8 0"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="12" cy="14" r="1.5" fill="white" />
      </svg>
    </div>
  );
}

function ShopSmartLogo() {
  return (
    <div className="mb-8 text-center relative">
      {/* Decorative shopping icon */}
      <div className="absolute -top-4 left-1/2 -translate-x-1/2 text-green-600/20 text-4xl">🛍️</div>
      
      <h1 className="text-6xl font-bold tracking-tight bg-linear-to-r from-green-600 via-emerald-500 to-green-600 bg-clip-text text-transparent drop-shadow-lg">ShopSmart</h1>
      
      {/* Decorative line with diamond */}
      <div className="flex items-center justify-center gap-2 mt-3">
        <div className="h-px w-12 bg-linear-to-r from-transparent to-green-600/50"></div>
        <div className="w-2 h-2 rotate-45 bg-green-600"></div>
        <div className="h-px w-12 bg-linear-to-l from-transparent to-green-600/50"></div>
      </div>
      
      <p className="text-sm mt-3 tracking-widest uppercase text-muted-foreground font-semibold">AI Shopping Assistant</p>
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
        <div className="absolute top-1/4 left-1/4 w-1 h-1 bg-green-500 rounded-full animate-ping" style={{ animationDuration: '3s', animationDelay: '0s' }}></div>
        <div className="absolute top-1/3 right-1/4 w-1 h-1 bg-emerald-500 rounded-full animate-ping" style={{ animationDuration: '4s', animationDelay: '1s' }}></div>
        <div className="absolute bottom-1/3 left-1/3 w-1 h-1 bg-green-400 rounded-full animate-ping" style={{ animationDuration: '5s', animationDelay: '2s' }}></div>
      </div>
      
      <section className="bg-card/95 backdrop-blur-sm rounded-3xl p-12 max-w-2xl w-full shadow-2xl flex flex-col items-center text-center relative z-10 border border-green-500/20" style={{ boxShadow: '0 25px 50px -12px rgba(34, 197, 94, 0.3), 0 0 0 1px rgba(34, 197, 94, 0.1)' }}>
        {/* Top corner decorations */}
        <div className="absolute top-4 left-4 text-green-600/20 text-2xl">✦</div>
        <div className="absolute top-4 right-4 text-green-600/20 text-2xl">✦</div>
        
        <ShopSmartLogo />
        
        <ShoppingBagIcon />

        <h2 className="text-3xl font-bold text-foreground mb-3 relative">
          Your AI Shopping Assistant Awaits
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-24 h-1 bg-linear-to-r from-transparent via-green-600 to-transparent"></div>
        </h2>
        
        <p className="text-muted-foreground max-w-md mb-8 text-base leading-relaxed mt-6">
          Meet <span className="font-bold text-green-600 bg-green-600/10 px-2 py-0.5 rounded">Ava</span>, your friendly AI Shopping Assistant. Browse products, add to cart, place orders, and complete your shopping—all by voice!
        </p>

        <Button 
          variant="primary" 
          size="lg" 
          onClick={onStartCall} 
          className="mt-4 px-12 py-6 text-lg font-bold hover:scale-105 transition-all bg-linear-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 shadow-lg shadow-green-500/50 border border-green-400/30"
        >
          🛒 START SHOPPING
        </Button>

        <div className="mt-10 pt-6 w-full border-t border-green-500/20">
          <p className="text-xs text-muted-foreground">
            Powered by <span className="font-semibold text-green-600">Murf Falcon TTS</span> • <span className="text-green-500">🛍️</span> AI Voice Shopping Assistant
          </p>
        </div>
        
        {/* Bottom corner decorations */}
        <div className="absolute bottom-4 left-4 text-green-600/20 text-2xl">✦</div>
        <div className="absolute bottom-4 right-4 text-green-600/20 text-2xl">✦</div>
      </section>
    </div>
  );
};
