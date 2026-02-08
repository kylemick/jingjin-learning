import { Mic, MicOff, Volume2, VolumeX, Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

interface VoiceButtonProps {
  isListening: boolean;
  isTranscribing?: boolean;
  isSpeaking?: boolean;
  onToggleListen: () => void;
  onSpeak?: () => void;
  onStopSpeak?: () => void;
  transcript?: string;
  error?: string;
  className?: string;
}

export default function VoiceButton({
  isListening,
  isTranscribing,
  isSpeaking,
  onToggleListen,
  onSpeak,
  onStopSpeak,
  transcript,
  error,
  className,
}: VoiceButtonProps) {
  const busy = isListening || isTranscribing;

  return (
    <div className={cn('flex items-center gap-2 flex-wrap', className)}>
      {/* 錄音 / 停止按鈕 */}
      <button
        onClick={onToggleListen}
        disabled={isTranscribing}
        className={cn(
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
          isTranscribing
            ? 'bg-amber-100 text-amber-700 cursor-wait'
            : isListening
              ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse'
              : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
        )}
      >
        {isTranscribing ? (
          <Loader2 size={16} className="animate-spin" />
        ) : isListening ? (
          <MicOff size={16} />
        ) : (
          <Mic size={16} />
        )}
        {isTranscribing ? '辨識中...' : isListening ? '停止錄音' : '語音輸入'}
      </button>

      {/* 朗讀按鈕 */}
      {onSpeak && (
        <button
          onClick={isSpeaking ? onStopSpeak : onSpeak}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            isSpeaking
              ? 'bg-red-100 text-red-700 hover:bg-red-200'
              : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
          )}
        >
          {isSpeaking ? <VolumeX size={16} /> : <Volume2 size={16} />}
          {isSpeaking ? '停止朗讀' : '朗讀'}
        </button>
      )}

      {/* 即時狀態顯示 */}
      {busy && transcript && (
        <span className="text-sm text-indigo-600 bg-indigo-50 px-3 py-1 rounded-lg max-w-xs truncate">
          {transcript}
        </span>
      )}

      {/* 錯誤提示 */}
      {error && (
        <span className="text-xs text-red-500 bg-red-50 px-3 py-1 rounded-lg">
          {error}
        </span>
      )}
    </div>
  );
}
