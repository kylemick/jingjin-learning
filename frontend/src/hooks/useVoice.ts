import { useState, useCallback, useRef, useEffect } from 'react';

interface UseVoiceOptions {
  onResult?: (text: string) => void;
  onEnd?: (fullText: string) => void;
}

export function useVoice(options?: UseVoiceOptions) {
  const [isListening, setIsListening] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const optionsRef = useRef(options);

  // 用 ref 跟蹤 options，避免 useCallback 依賴導致無限重渲染
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const startListening = useCallback(async () => {
    setError('');
    setTranscript('');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // 選擇瀏覽器支持的音頻格式
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/mp4';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // 釋放麥克風
        stream.getTracks().forEach(t => t.stop());
        streamRef.current = null;

        if (chunksRef.current.length === 0) {
          setIsTranscribing(false);
          return;
        }

        // 組裝音頻 Blob
        const blob = new Blob(chunksRef.current, { type: mimeType });
        chunksRef.current = [];

        // 上傳到後端轉寫
        setIsTranscribing(true);
        setTranscript('辨識中...');

        try {
          const formData = new FormData();
          const ext = mimeType.includes('webm') ? 'webm' : 'mp4';
          formData.append('audio', blob, `recording.${ext}`);

          const response = await fetch('/api/voice/transcribe', {
            method: 'POST',
            body: formData,
          });

          const data = await response.json();

          if (response.ok && data.text) {
            setTranscript(data.text);
            optionsRef.current?.onResult?.(data.text);
            optionsRef.current?.onEnd?.(data.text);
          } else {
            const errMsg = data.error || data.message || '語音識別失敗';
            setError(errMsg);
            setTranscript('');
          }
        } catch (err) {
          console.error('語音上傳失敗:', err);
          setError('語音上傳失敗，請檢查後端服務');
          setTranscript('');
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start(250); // 每 250ms 收集一次數據
      setIsListening(true);
    } catch (err) {
      console.error('麥克風權限被拒絕:', err);
      setError('麥克風權限被拒絕');
    }
  }, []);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setIsListening(false);
  }, []);

  const speak = useCallback((text: string, lang: string = 'zh-CN') => {
    if (!('speechSynthesis' in window)) {
      console.warn('此瀏覽器不支持語音合成');
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // 嘗試選擇中文語音
    const voices = window.speechSynthesis.getVoices();
    const zhVoice = voices.find(v => v.lang.startsWith('zh'));
    if (zhVoice) {
      utterance.voice = zhVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    // Chrome bug: 語音列表可能尚未加載
    if (voices.length === 0) {
      window.speechSynthesis.onvoiceschanged = () => {
        const v = window.speechSynthesis.getVoices();
        const zh = v.find(voice => voice.lang.startsWith('zh'));
        if (zh) utterance.voice = zh;
        window.speechSynthesis.speak(utterance);
      };
    } else {
      window.speechSynthesis.speak(utterance);
    }
  }, []);

  const stopSpeaking = useCallback(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, []);

  return {
    isListening,
    isTranscribing,
    isSpeaking,
    transcript,
    error,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  };
}
