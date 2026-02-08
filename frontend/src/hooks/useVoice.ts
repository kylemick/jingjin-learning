import { useState, useCallback, useRef } from 'react';

interface UseVoiceOptions {
  onResult?: (text: string) => void;
  onEnd?: (fullText: string) => void;
}

export function useVoice(options?: UseVoiceOptions) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const fullTranscriptRef = useRef('');

  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setIsListening(true);
      setTranscript('');
      fullTranscriptRef.current = '';

      // Connect to backend WebSocket
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/api/voice/stt`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'result') {
          fullTranscriptRef.current += data.text;
          setTranscript(fullTranscriptRef.current);
          options?.onResult?.(data.text);
        } else if (data.type === 'end') {
          options?.onEnd?.(fullTranscriptRef.current);
        }
      };

      ws.onopen = () => {
        // Start recording and sending audio
        const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            event.data.arrayBuffer().then(buffer => {
              ws.send(new Uint8Array(buffer));
            });
          }
        };

        mediaRecorder.start(100); // Send audio chunks every 100ms
      };

      ws.onerror = () => {
        setIsListening(false);
        stream.getTracks().forEach(t => t.stop());
      };

      ws.onclose = () => {
        setIsListening(false);
        stream.getTracks().forEach(t => t.stop());
      };
    } catch (err) {
      console.error('Microphone access denied:', err);
      setIsListening(false);
    }
  }, [options]);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'stop' }));
      wsRef.current.close();
    }
    setIsListening(false);
  }, []);

  const speak = useCallback((text: string, lang: string = 'zh-TW') => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }, []);

  const stopSpeaking = useCallback(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }, []);

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  };
}
