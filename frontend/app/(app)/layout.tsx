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
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-lg">M</span>
          </div>
          <span className="text-foreground font-bold text-xl">{companyName}</span>
        </div>
        
        <span className="text-muted-foreground font-mono text-xs font-bold tracking-wider uppercase">
          AI Barista Challenge
        </span>
      </header>

      {children}
    </>
  );
}
