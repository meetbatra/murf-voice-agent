'use client';

import { motion } from 'motion/react';

interface WellnessSession {
  date: string;
  timestamp: string;
  mood_score: number;
  energy_level: string;
  stressors: string | null;
  objectives: string[];
  summary: string;
}

interface WellnessData {
  sessions: WellnessSession[];
}

interface WellnessSummaryProps {
  data: WellnessData;
  onClose: () => void;
}

export function WellnessSummary({ data, onClose }: WellnessSummaryProps) {
  const latestSession = data.sessions[data.sessions.length - 1];
  const date = new Date(latestSession.timestamp);
  
  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 bottom-0 w-[400px] p-8 overflow-y-auto bg-card border-l-4 border-primary shadow-2xl"
      style={{ 
        zIndex: 9999,
      }}
    >
      {/* Header */}
      <div className="text-center mb-6 pb-4 border-b-2 border-dashed border-muted">
        <h2 className="text-3xl font-bold mb-2 text-primary">
          Today's Check-In
        </h2>
        <p className="text-xs uppercase tracking-widest text-muted-foreground">
          Wellness Companion
        </p>
        <p className="text-xs mt-2 text-muted-foreground">
          {date.toLocaleDateString()} • {date.toLocaleTimeString()}
        </p>
      </div>

      {/* Mood & Energy */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-3">
          <span className="font-semibold text-foreground">Mood Score</span>
          <span className="text-2xl font-bold text-primary">
            {latestSession.mood_score}/10
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="font-semibold text-foreground">Energy Level</span>
          <span className="capitalize text-muted-foreground">
            {latestSession.energy_level}
          </span>
        </div>
      </div>

      {/* Stressors */}
      {latestSession.stressors && (
        <div className="mb-6 p-4 rounded-lg bg-accent/20 border border-accent">
          <h3 className="font-semibold mb-2 text-accent-foreground">On Your Mind</h3>
          <p className="text-sm text-foreground">{latestSession.stressors}</p>
        </div>
      )}

      {/* Objectives */}
      <div className="mb-6">
        <h3 className="font-semibold mb-3 text-foreground">Today's Objectives</h3>
        <ul className="space-y-2">
          {latestSession.objectives.map((obj, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-primary">✓</span>
              <span className="text-sm text-foreground">{obj}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Summary */}
      <div className="mb-6 p-4 rounded-lg bg-secondary">
        <h3 className="font-semibold mb-2 text-secondary-foreground">Summary</h3>
        <p className="text-sm italic text-secondary-foreground">{latestSession.summary}</p>
      </div>

      {/* Footer */}
      <div className="text-center text-xs mb-6 text-muted-foreground">
        <p className="mb-2">You're doing great! ✨</p>
        <p>Powered by <span className="font-semibold text-primary">Murf Falcon TTS</span></p>
      </div>

      {/* Close Button */}
      <button
        onClick={onClose}
        className="mt-auto py-3 px-6 bg-primary text-primary-foreground border-none rounded-lg text-base font-semibold cursor-pointer w-full hover:opacity-90 transition-opacity"
      >
        Close Summary
      </button>
    </motion.div>
  );
}
