import { cn } from '../lib/utils';
import { GraduationCap, MessageSquare, Users } from 'lucide-react';

const scenarios = [
  { value: 'academic', label: '學科提升', icon: GraduationCap, color: 'indigo' },
  { value: 'expression', label: '表達提升', icon: MessageSquare, color: 'amber' },
  { value: 'interview', label: '面試提升', icon: Users, color: 'emerald' },
];

interface ScenarioSelectorProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export default function ScenarioSelector({ value, onChange, className }: ScenarioSelectorProps) {
  return (
    <div className={cn('flex gap-3', className)}>
      {scenarios.map((s) => {
        const Icon = s.icon;
        const isActive = value === s.value;
        return (
          <button
            key={s.value}
            onClick={() => onChange(s.value)}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border',
              isActive
                ? s.color === 'indigo' ? 'bg-indigo-50 text-indigo-700 border-indigo-300'
                : s.color === 'amber' ? 'bg-amber-50 text-amber-700 border-amber-300'
                : 'bg-emerald-50 text-emerald-700 border-emerald-300'
                : 'bg-white text-slate-500 border-slate-200 hover:border-slate-300'
            )}
          >
            <Icon size={16} />
            {s.label}
          </button>
        );
      })}
    </div>
  );
}
