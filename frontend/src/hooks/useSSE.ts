import { useState, useCallback, useRef } from 'react';
import { fetchSSE } from '../services/api';

interface UseSSEOptions {
  onDone?: (fullText: string) => void;
}

export function useSSE(options?: UseSSEOptions) {
  const [text, setText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const fullTextRef = useRef('');

  const startStream = useCallback(async (url: string, body?: any) => {
    setText('');
    fullTextRef.current = '';
    setIsStreaming(true);

    try {
      await fetchSSE(
        url,
        { method: 'POST', body: body ? JSON.stringify(body) : undefined },
        (chunk) => {
          fullTextRef.current += chunk;
          setText(fullTextRef.current);
        },
        () => {
          setIsStreaming(false);
          options?.onDone?.(fullTextRef.current);
        },
      );
    } catch (err) {
      setIsStreaming(false);
      setText('請求失敗，請稍後再試。');
    }
  }, [options]);

  const reset = useCallback(() => {
    setText('');
    fullTextRef.current = '';
    setIsStreaming(false);
  }, []);

  return { text, isStreaming, startStream, reset };
}
