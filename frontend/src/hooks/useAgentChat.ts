import { useState, useCallback, useRef } from 'react';

const ACTION_RE = /<!--ACTION:.*?-->/gs;
const PHASE_RE = /<!--PHASE_COMPLETE:.*?-->/gs;

export interface ChatMsg {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  phase_at_time?: string;
  action_metadata?: any;
  created_at?: string;
}

export interface PhaseInfo {
  key: string;
  order: number;
  name: string;
  book_chapter: string;
  goal: string;
}

export const ALL_PHASES: PhaseInfo[] = [
  { key: 'time_compass', order: 1, name: '時間羅盤', book_chapter: '時間之尺', goal: '審視時間使用' },
  { key: 'choice_navigator', order: 2, name: '選擇導航', book_chapter: '尋找心中的巴拿馬', goal: '確定方向' },
  { key: 'action_workshop', order: 3, name: '行動工坊', book_chapter: '即刻行動', goal: '分解任務' },
  { key: 'learning_dojo', order: 4, name: '學習道場', book_chapter: '高段位學習者', goal: '深度學習' },
  { key: 'thinking_forge', order: 5, name: '思維鍛造', book_chapter: '修煉思維利器', goal: '鍛鍊思維' },
  { key: 'talent_growth', order: 6, name: '才能精進', book_chapter: '努力的才能', goal: '刻意練習' },
  { key: 'review_hub', order: 7, name: '成長復盤', book_chapter: '獨特的成功', goal: '反思提升' },
];

function cleanMarkers(text: string): string {
  return text.replace(ACTION_RE, '').replace(PHASE_RE, '').trim();
}

export function useAgentChat() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [currentPhase, setCurrentPhase] = useState('time_compass');
  const [phaseContext, setPhaseContext] = useState<Record<string, any>>({});
  const [convStatus, setConvStatus] = useState('active');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const abortRef = useRef<AbortController | null>(null);

  const processSSE = useCallback(async (
    url: string,
    options: RequestInit,
    onComplete?: () => void,
  ) => {
    setIsStreaming(true);
    setStreamingText('');

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(url, { ...options, signal: controller.signal });
      if (!res.ok || !res.body) throw new Error(`SSE Error: ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6).trim();
          if (data === '[DONE]') continue;

          try {
            const parsed = JSON.parse(data);

            // state_update event from backend
            if (parsed.type === 'state_update') {
              setCurrentPhase(parsed.current_phase || 'time_compass');
              setPhaseContext(parsed.phase_context || {});
              setConvStatus(parsed.status || 'active');
              continue;
            }

            if (parsed.content) {
              accumulated += parsed.content;
              setStreamingText(cleanMarkers(accumulated));
            }
          } catch {
            // ignore
          }
        }
      }

      // Finalize: add assistant message to list
      if (accumulated) {
        const cleaned = cleanMarkers(accumulated);
        setMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant',
          content: cleaned,
          phase_at_time: currentPhase,
        }]);
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Agent chat error:', err);
        setMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant',
          content: '抱歉，發生了錯誤，請稍後再試。',
        }]);
      }
    } finally {
      setIsStreaming(false);
      setStreamingText('');
      abortRef.current = null;
      onComplete?.();
    }
  }, [currentPhase]);

  const startConversation = useCallback(async (studentId: number, convId: number) => {
    await processSSE(
      `/api/agent/${studentId}/conversations/${convId}/start`,
      { method: 'POST' },
    );
  }, [processSSE]);

  const sendMessage = useCallback(async (studentId: number, convId: number, message: string) => {
    // Add user message immediately
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content: message,
      phase_at_time: currentPhase,
    }]);

    await processSSE(
      `/api/agent/${studentId}/conversations/${convId}/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      },
    );
  }, [processSSE, currentPhase]);

  const loadConversation = useCallback(async (studentId: number, convId: number) => {
    const res = await fetch(`/api/agent/${studentId}/conversations/${convId}`);
    if (!res.ok) return;
    const data = await res.json();
    setCurrentPhase(data.current_phase || 'time_compass');
    setPhaseContext(data.phase_context || {});
    setConvStatus(data.status || 'active');
    // Clean markers from historical messages
    const msgs: ChatMsg[] = (data.messages || [])
      .filter((m: any) => m.role !== 'system')
      .map((m: any) => ({
        ...m,
        content: cleanMarkers(m.content),
      }));
    setMessages(msgs);
  }, []);

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return {
    messages,
    currentPhase,
    phaseContext,
    convStatus,
    isStreaming,
    streamingText,
    startConversation,
    sendMessage,
    loadConversation,
    stopStreaming,
  };
}
