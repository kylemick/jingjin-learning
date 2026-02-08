import { cn } from '../lib/utils';
import { User, Bot } from 'lucide-react';
import type { ChatMsg } from '../hooks/useAgentChat';

interface ChatBubbleProps {
  message: ChatMsg;
}

export default function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div className={cn(
        'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
        isUser ? 'bg-indigo-100 text-indigo-600' : 'bg-emerald-100 text-emerald-600'
      )}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Bubble */}
      <div className={cn(
        'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
        isUser
          ? 'bg-indigo-600 text-white rounded-tr-md'
          : 'bg-white border border-slate-200 text-slate-700 rounded-tl-md shadow-sm'
      )}>
        {message.content.split('\n').map((line, i) => {
          // Render markdown-like bold
          const parts = line.split(/(\*\*.*?\*\*)/g);
          return (
            <p key={i} className={i > 0 ? 'mt-2' : ''}>
              {parts.map((part, j) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                  return <strong key={j}>{part.slice(2, -2)}</strong>;
                }
                return <span key={j}>{part}</span>;
              })}
            </p>
          );
        })}
      </div>
    </div>
  );
}


interface StreamingBubbleProps {
  text: string;
}

export function StreamingBubble({ text }: StreamingBubbleProps) {
  return (
    <div className="flex gap-3 flex-row">
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-emerald-100 text-emerald-600">
        <Bot size={16} />
      </div>
      <div className="max-w-[75%] rounded-2xl rounded-tl-md px-4 py-3 text-sm leading-relaxed bg-white border border-slate-200 text-slate-700 shadow-sm">
        {text.split('\n').map((line, i) => (
          <p key={i} className={i > 0 ? 'mt-2' : ''}>{line}</p>
        ))}
        <span className="inline-block w-1.5 h-4 bg-indigo-500 rounded-sm ml-0.5 animate-pulse" />
      </div>
    </div>
  );
}
