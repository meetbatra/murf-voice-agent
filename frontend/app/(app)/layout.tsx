import { headers } from 'next/headers';
import { getAppConfig } from '@/lib/utils';

interface LayoutProps {
  children: React.ReactNode;
}

export default async function Layout({ children }: LayoutProps) {
  const hdrs = await headers();
  const { companyName } = await getAppConfig(hdrs);

  return (
    <>
      <header className="fixed top-0 left-0 z-50 w-full flex flex-row justify-between px-6 py-4 bg-background/95 backdrop-blur-md border-b border-purple-500/20" style={{ boxShadow: '0 4px 6px -1px rgba(168, 85, 247, 0.1)' }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-linear-to-br from-purple-600 to-violet-600 rounded-lg flex items-center justify-center shadow-lg shadow-purple-500/30 border border-purple-400/30">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Game controller icon */}
              <path d="M6 12a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2H6zm10 0a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2h-2z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
              <path d="M10 12V6a2 2 0 0 1 4 0v6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="flex flex-col">
            <span className="text-foreground font-bold text-lg leading-none">Improv Situations</span>
            <span className="text-purple-600 text-xs font-semibold">Weird Scenarios Game</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-purple-500 text-lg">🎮</span>
          <span className="text-muted-foreground font-mono text-xs font-bold tracking-wider uppercase">
            Host
          </span>
        </div>
      </header>

      {children}
    </>
  );
}
