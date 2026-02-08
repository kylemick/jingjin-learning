import { cn } from '../lib/utils';

interface StreamingTextProps {
  text: string;
  isStreaming: boolean;
  className?: string;
}

export default function StreamingText({ text, isStreaming, className }: StreamingTextProps) {
  if (!text && !isStreaming) return null;

  return (
    <div className={cn('bg-white rounded-xl border border-slate-200 p-5 shadow-sm', className)}>
      <div className={cn(
        'prose prose-slate prose-sm max-w-none whitespace-pre-wrap',
        isStreaming && 'streaming-cursor'
      )}>
        {text || (isStreaming ? '正在思考中...' : '')}
      </div>
    </div>
  );
}
