import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { cn } from '../lib/utils';

interface VoiceButtonProps {
  isListening: boolean;
  onToggleListen: () => void;
  onSpeak?: () => void;
  onStopSpeak?: () => void;
  className?: string;
}

export default function VoiceButton({
  isListening,
  onToggleListen,
  onSpeak,
  onStopSpeak,
  className,
}: VoiceButtonProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <button
        onClick={onToggleListen}
        className={cn(
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
          isListening
            ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse'
            : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
        )}
      >
        {isListening ? <MicOff size={16} /> : <Mic size={16} />}
        {isListening ? '停止錄音' : '語音輸入'}
      </button>
      {onSpeak && (
        <button
          onClick={onSpeak}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-emerald-100 text-emerald-700 hover:bg-emerald-200 transition-colors"
        >
          <Volume2 size={16} />
          朗讀
        </button>
      )}
      {onStopSpeak && (
        <button
          onClick={onStopSpeak}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
        >
          <VolumeX size={16} />
        </button>
      )}
    </div>
  );
}
