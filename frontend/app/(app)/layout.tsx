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
      <header className="fixed top-0 left-0 z-50 w-full flex flex-row justify-between p-6 bg-background/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7 4h14v2l-2 9h-10l-2-9v-2zm0 0c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2M7 15h10M9 18a1 1 0 100 2 1 1 0 000-2zm8 0a1 1 0 100 2 1 1 0 000-2z" stroke="white" strokeWidth="2" fill="none"/>
            </svg>
          </div>
          <span className="text-foreground font-bold text-xl">FreshMart</span>
        </div>
        
        <span className="text-muted-foreground font-mono text-xs font-bold tracking-wider uppercase">
          Grocery Shopping
        </span>
      </header>

      {children}
    </>
  );
}
