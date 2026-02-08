import { cn } from '../lib/utils';
import { ALL_PHASES } from '../hooks/useAgentChat';
import {
  Clock, Compass, Zap, BookOpen, Brain, Target, BarChart3,
} from 'lucide-react';

const phaseIcons: Record<string, React.ElementType> = {
  time_compass: Clock,
  choice_navigator: Compass,
  action_workshop: Zap,
  learning_dojo: BookOpen,
  thinking_forge: Brain,
  talent_growth: Target,
  review_hub: BarChart3,
};

interface PhaseProgressProps {
  currentPhase: string;
  phaseContext: Record<string, any>;
  className?: string;
}

export default function PhaseProgress({ currentPhase, phaseContext, className }: PhaseProgressProps) {
  const currentIdx = ALL_PHASES.findIndex(p => p.key === currentPhase);

  return (
    <div className={cn('bg-white rounded-xl border border-slate-200 px-4 py-3 shadow-sm', className)}>
      <div className="flex items-center gap-1 overflow-x-auto">
        {ALL_PHASES.map((phase, idx) => {
          const Icon = phaseIcons[phase.key] || Clock;
          const isCompleted = phase.key in (phaseContext || {});
          const isCurrent = idx === currentIdx;
          const isFuture = idx > currentIdx;

          return (
            <div key={phase.key} className="flex items-center">
              {idx > 0 && (
                <div className={cn(
                  'w-4 h-0.5 mx-0.5 flex-shrink-0',
                  isCompleted ? 'bg-emerald-400' : isCurrent ? 'bg-indigo-300' : 'bg-slate-200'
                )} />
              )}
              <div
                className={cn(
                  'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex-shrink-0',
                  isCompleted && 'bg-emerald-50 text-emerald-700',
                  isCurrent && 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300',
                  isFuture && 'bg-slate-50 text-slate-400',
                )}
                title={phase.goal}
              >
                <Icon size={14} />
                <span className="hidden sm:inline">{phase.name}</span>
                <span className="sm:hidden">{phase.order}</span>
                {isCompleted && <span className="text-emerald-500">✓</span>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
