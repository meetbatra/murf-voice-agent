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
      <header className="fixed top-0 left-0 z-50 w-full flex flex-row justify-between px-6 py-4 bg-background/95 backdrop-blur-md border-b border-purple-500/20" style={{ boxShadow: '0 4px 6px -1px rgba(147, 51, 234, 0.1)' }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-linear-to-br from-purple-600 to-violet-600 rounded-lg flex items-center justify-center shadow-lg shadow-purple-500/30 border border-purple-400/30">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Sword icon for fantasy theme */}
              <path d="M12 2 L12 16 M8 14 L16 14 L14 18 L10 18 Z M12 2 L9 4 L15 4 Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            </svg>
          </div>
          <div className="flex flex-col">
            <span className="text-foreground font-bold text-lg leading-none">Epic Quest</span>
            <span className="text-purple-600 text-xs font-semibold">by Gandor</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-purple-500 text-lg">🎲</span>
          <span className="text-muted-foreground font-mono text-xs font-bold tracking-wider uppercase">
            D&D Game Master
          </span>
        </div>
      </header>

      {children}
    </>
  );
}
