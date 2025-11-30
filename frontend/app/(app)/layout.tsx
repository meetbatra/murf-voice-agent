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
      <header className="fixed top-0 left-0 z-50 w-full flex flex-row justify-between px-6 py-4 bg-background/95 backdrop-blur-md border-b border-green-500/20" style={{ boxShadow: '0 4px 6px -1px rgba(34, 197, 94, 0.1)' }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-linear-to-br from-green-600 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg shadow-green-500/30 border border-green-400/30">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Shopping bag icon */}
              <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
              <line x1="3" y1="6" x2="21" y2="6" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              <path d="M16 10a4 4 0 0 1-8 0" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="flex flex-col">
            <span className="text-foreground font-bold text-lg leading-none">ShopSmart</span>
            <span className="text-green-600 text-xs font-semibold">AI Shopping Assistant</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-green-500 text-lg">🛒</span>
          <span className="text-muted-foreground font-mono text-xs font-bold tracking-wider uppercase">
            Ava
          </span>
        </div>
      </header>

      {children}
    </>
  );
}
