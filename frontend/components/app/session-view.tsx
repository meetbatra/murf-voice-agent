'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import type { AppConfig } from '@/app-config';
import { ChatTranscript } from '@/components/app/chat-transcript';
import { PreConnectMessage } from '@/components/app/preconnect-message';
import { TileLayout } from '@/components/app/tile-layout';
import {
  AgentControlBar,
  type ControlBarControls,
} from '@/components/livekit/agent-control-bar/agent-control-bar';
import { useChatMessages } from '@/hooks/useChatMessages';
import { useConnectionTimeout } from '@/hooks/useConnectionTimout';
import { useDebugMode } from '@/hooks/useDebug';
import { cn } from '@/lib/utils';
import { ScrollArea } from '../livekit/scroll-area/scroll-area';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';
const BOTTOM_VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden' as const,
  animate: 'visible' as const,
  exit: 'hidden' as const,
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: [0.4, 0.0, 0.2, 1],
  },
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({ top = false, bottom = false, className }: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className
      )}
    />
  );
}
interface SessionViewProps {
  appConfig: AppConfig;
}

export const SessionView = ({
  appConfig,
  ...props
}: React.ComponentProps<'section'> & SessionViewProps) => {
  useConnectionTimeout(200_000);
  useDebugMode({ enabled: IN_DEVELOPMENT });

  const messages = useChatMessages();
  const [chatOpen, setChatOpen] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const sidebarScrollRef = useRef<HTMLDivElement>(null);

  const controls: ControlBarControls = {
    leave: true,
    microphone: true,
    chat: appConfig.supportsChatInput,
    camera: appConfig.supportsVideoInput,
    screenShare: appConfig.supportsVideoInput,
  };

  useEffect(() => {
    // Auto-scroll to bottom whenever messages change and chat is open
    if (scrollAreaRef.current && chatOpen) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
    // Auto-scroll sidebar transcript
    if (sidebarScrollRef.current) {
      sidebarScrollRef.current.scrollTop = sidebarScrollRef.current.scrollHeight;
    }
  }, [messages, chatOpen]);

  return (
    <>
    <section className="bg-background relative z-10 h-screen w-full overflow-hidden flex" {...props}>
      {/* Main Content Wrapper */}
      <div className="h-full flex-1">
        {/* Chat Transcript */}
        <div
          className={cn(
            'fixed inset-0 grid grid-cols-1 grid-rows-1',
            !chatOpen && 'pointer-events-none'
          )}
        >
        <Fade top className="absolute inset-x-4 top-0 h-40" />
        <ScrollArea ref={scrollAreaRef} className="px-4 pt-40 pb-[150px] md:px-6 md:pb-[180px]">
          <ChatTranscript
            hidden={!chatOpen}
            messages={messages}
            className="mx-auto max-w-2xl space-y-3 transition-opacity duration-300 ease-out"
          />
        </ScrollArea>
      </div>

      {/* Tile Layout */}
      <TileLayout chatOpen={chatOpen} />

      {/* Bottom */}
      <motion.div
        variants={{
          visible: {
            opacity: 1,
            translateY: '0%',
          },
          hidden: {
            opacity: 0,
            translateY: '100%',
          },
        }}
        initial="hidden"
        animate="visible"
        exit="hidden"
        transition={{
          duration: 0.3,
          delay: 0.5,
        }}
        className="fixed inset-x-3 bottom-0 md:inset-x-12"
        style={{ zIndex: 50 }}
      >
        {appConfig.isPreConnectBufferEnabled && (
          <PreConnectMessage messages={messages} className="pb-4" />
        )}
        <div className="bg-background relative mx-auto max-w-2xl pb-3 md:pb-12">
          <Fade bottom className="absolute inset-x-0 top-0 h-4 -translate-y-full" />
          <AgentControlBar controls={controls} onChatOpenChange={setChatOpen} />
        </div>
      </motion.div>
      </div>

      {/* Right Sidebar Transcript - Always Visible */}
      <motion.aside
        initial={{ opacity: 0, x: 100 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.8 }}
        className="hidden lg:flex flex-col w-80 xl:w-96 h-screen border-l border-green-500/30 bg-card/50 backdrop-blur-sm"
      >
        {/* Header */}
        <div className="p-4 border-b border-green-500/20 bg-linear-to-b from-green-950/30 to-transparent">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <h3 className="text-sm font-bold text-green-600 uppercase tracking-wider">Live Transcript</h3>
          </div>
          <p className="text-xs text-muted-foreground mt-1">Real-time conversation</p>
        </div>

        {/* Messages */}
        <ScrollArea ref={sidebarScrollRef} className="flex-1 p-4">
          <div className="space-y-3">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="w-12 h-12 rounded-full bg-green-600/20 flex items-center justify-center mb-3">
                  <span className="text-2xl">🛒</span>
                </div>
                <p className="text-sm text-muted-foreground">No messages yet</p>
                <p className="text-xs text-muted-foreground/70 mt-1">Start shopping!</p>
              </div>
            ) : (
              messages.map(({ id, timestamp, from, message }) => {
                const isUser = from?.isLocal;
                return (
                  <div
                    key={id}
                    className={cn(
                      'p-3 rounded-lg text-sm',
                      isUser
                        ? 'bg-green-600/20 border border-green-500/30 ml-4'
                        : 'bg-card border border-green-500/20 mr-4'
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={cn(
                          'text-xs font-semibold',
                          isUser ? 'text-green-400' : 'text-green-600'
                        )}
                      >
                        {isUser ? 'You' : 'Ava'}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-foreground/90 leading-relaxed">{message}</p>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="p-3 border-t border-green-500/20 bg-linear-to-t from-green-950/30 to-transparent">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{messages.length} messages</span>
            <span className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
              Live
            </span>
          </div>
        </div>
      </motion.aside>
    </section>
    </>
  );
};
