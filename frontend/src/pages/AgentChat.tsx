import { useState, useEffect, useRef } from 'react';
import { Send, Plus, History, Mic, MicOff, Loader2, SkipForward, Volume2, VolumeX } from 'lucide-react';
import PhaseProgress from '../components/PhaseProgress';
import ChatBubble, { StreamingBubble } from '../components/ChatBubble';
import { useAgentChat, ALL_PHASES } from '../hooks/useAgentChat';
import { useVoice } from '../hooks/useVoice';
import { cn } from '../lib/utils';

interface ConvItem {
  id: number;
  title: string;
  current_phase: string;
  status: string;
  updated_at: string;
}

export default function AgentChat() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [convId, setConvId] = useState<number | null>(null);
  const [convList, setConvList] = useState<ConvItem[]>([]);
  const [input, setInput] = useState('');
  const [showSidebar, setShowSidebar] = useState(false);
  const [scenario, setScenario] = useState('academic');
  const bottomRef = useRef<HTMLDivElement>(null);

  const {
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
  } = useAgentChat();

  const {
    isListening,
    isTranscribing,
    isSpeaking,
    transcript,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  } = useVoice({
    onEnd: (t) => setInput(prev => prev + t),
  });

  // Load conversation list
  useEffect(() => {
    if (!studentId) return;
    fetch(`/api/agent/${studentId}/conversations`)
      .then(r => r.json())
      .then(setConvList)
      .catch(() => {});
  }, [studentId, convId]);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const handleNewConversation = async () => {
    if (!studentId) return;
    const res = await fetch(`/api/agent/${studentId}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新的精進旅程', scenario }),
    });
    const conv = await res.json();
    setConvId(conv.id);
    await loadConversation(studentId, conv.id);
    // Start: get AI's opening message
    await startConversation(studentId, conv.id);
    setShowSidebar(false);
  };

  const handleLoadConversation = async (id: number) => {
    setConvId(id);
    await loadConversation(studentId, id);
    setShowSidebar(false);
  };

  const handleSend = async () => {
    if (!input.trim() || !convId || isStreaming) return;
    const msg = input.trim();
    setInput('');
    await sendMessage(studentId, convId, msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSkipPhase = async () => {
    if (!convId) return;
    const res = await fetch(`/api/agent/${studentId}/conversations/${convId}/skip-phase`, {
      method: 'POST',
    });
    const data = await res.json();
    if (data.ok && data.new_phase) {
      // Reload conversation state
      await loadConversation(studentId, convId);
    }
  };

  const currentPhaseInfo = ALL_PHASES.find(p => p.key === currentPhase);
  const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant');

  // No student selected
  if (!studentId) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <h2 className="text-xl font-bold text-slate-700 mb-2">請先選擇或建立學生檔案</h2>
          <p className="text-slate-500">回到首頁建立學生後再開始精進旅程</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-slate-200 bg-white rounded-t-xl">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
            title="對話歷史"
          >
            <History size={18} />
          </button>
          <div>
            <h2 className="text-sm font-semibold text-slate-700">
              {convId ? `精進旅程 #${convId}` : '開始你的精進旅程'}
            </h2>
            {currentPhaseInfo && convId && (
              <p className="text-xs text-slate-400">
                {currentPhaseInfo.name} — {currentPhaseInfo.book_chapter}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {convId && convStatus === 'active' && (
            <button
              onClick={handleSkipPhase}
              className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
              title="跳過當前階段"
            >
              <SkipForward size={14} />
              跳過
            </button>
          )}
          <button
            onClick={handleNewConversation}
            className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
          >
            <Plus size={14} />
            新旅程
          </button>
        </div>
      </div>

      {/* Phase Progress */}
      {convId && (
        <div className="flex-shrink-0 px-4 py-2">
          <PhaseProgress currentPhase={currentPhase} phaseContext={phaseContext} />
        </div>
      )}

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {!convId ? (
          /* Landing: no conversation selected */
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mb-4">
              <span className="text-3xl">🎯</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-700 mb-2">精進旅程</h2>
            <p className="text-slate-500 max-w-md mb-6">
              基於《精進》的七步閉環，AI 教練將引導你一步步完成
              「認識時間 → 確定目標 → 分解行動 → 深度學習 → 鍛鍊思維 → 刻意練習 → 反思成長」
            </p>

            <div className="flex gap-2 mb-4">
              {(['academic', 'expression', 'interview'] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setScenario(s)}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    scenario === s
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  )}
                >
                  {s === 'academic' ? '學科提升' : s === 'expression' ? '表達提升' : '面試提升'}
                </button>
              ))}
            </div>

            <button
              onClick={handleNewConversation}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200"
            >
              開始精進旅程
            </button>

            {/* Conversation history */}
            {convList.length > 0 && (
              <div className="mt-8 w-full max-w-md">
                <h3 className="text-sm font-semibold text-slate-500 mb-2">歷史旅程</h3>
                <div className="space-y-2">
                  {convList.slice(0, 5).map((c) => {
                    const phaseName = ALL_PHASES.find(p => p.key === c.current_phase)?.name || c.current_phase;
                    return (
                      <button
                        key={c.id}
                        onClick={() => handleLoadConversation(c.id)}
                        className="w-full flex items-center justify-between px-4 py-3 bg-white rounded-lg border border-slate-200 hover:border-indigo-200 hover:shadow-sm transition-all text-left"
                      >
                        <div>
                          <div className="text-sm font-medium text-slate-700">{c.title}</div>
                          <div className="text-xs text-slate-400">當前：{phaseName}</div>
                        </div>
                        <span className={cn(
                          'text-xs px-2 py-1 rounded-full',
                          c.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-indigo-100 text-indigo-700'
                        )}>
                          {c.status === 'completed' ? '已完成' : '進行中'}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Messages */
          <div className="space-y-4">
            {messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg} />
            ))}
            {isStreaming && streamingText && (
              <StreamingBubble text={streamingText} />
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Sidebar overlay */}
      {showSidebar && (
        <div className="fixed inset-0 z-50 flex">
          <div className="w-80 bg-white shadow-xl border-r border-slate-200 p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-700">對話歷史</h3>
              <button onClick={() => setShowSidebar(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <button
              onClick={handleNewConversation}
              className="w-full mb-4 flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
            >
              <Plus size={16} />
              新的旅程
            </button>
            <div className="space-y-2">
              {convList.map((c) => (
                <button
                  key={c.id}
                  onClick={() => handleLoadConversation(c.id)}
                  className={cn(
                    'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                    convId === c.id ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-50 text-slate-600'
                  )}
                >
                  <div className="font-medium">{c.title}</div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {ALL_PHASES.find(p => p.key === c.current_phase)?.name}
                    {c.status === 'completed' && ' · 已完成'}
                  </div>
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 bg-black/20" onClick={() => setShowSidebar(false)} />
        </div>
      )}

      {/* Input Bar */}
      {convId && convStatus === 'active' && (
        <div className="flex-shrink-0 px-4 py-3 border-t border-slate-200 bg-white rounded-b-xl">
          {/* Voice + TTS */}
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={isListening ? stopListening : startListening}
              disabled={isTranscribing || isStreaming}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                isTranscribing
                  ? 'bg-amber-100 text-amber-700'
                  : isListening
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              )}
            >
              {isTranscribing ? <Loader2 size={14} className="animate-spin" /> : isListening ? <MicOff size={14} /> : <Mic size={14} />}
              {isTranscribing ? '辨識中...' : isListening ? '停止' : '語音'}
            </button>
            {lastAssistantMsg && (
              <button
                onClick={isSpeaking ? stopSpeaking : () => speak(lastAssistantMsg.content)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  isSpeaking ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                )}
              >
                {isSpeaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                {isSpeaking ? '停止' : '朗讀'}
              </button>
            )}
            {transcript && isTranscribing && (
              <span className="text-xs text-indigo-500 truncate max-w-48">{transcript}</span>
            )}
          </div>

          {/* Text input */}
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="輸入你的想法..."
              rows={1}
              className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300"
              disabled={isStreaming}
            />
            <button
              onClick={isStreaming ? stopStreaming : handleSend}
              disabled={!isStreaming && !input.trim()}
              className={cn(
                'px-4 py-2.5 rounded-xl text-white font-medium transition-colors flex items-center gap-1',
                isStreaming
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300'
              )}
            >
              {isStreaming ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                </>
              ) : (
                <Send size={16} />
              )}
            </button>
          </div>
        </div>
      )}

      {/* Journey completed */}
      {convId && convStatus === 'completed' && (
        <div className="flex-shrink-0 px-4 py-4 border-t border-slate-200 bg-emerald-50 text-center rounded-b-xl">
          <p className="text-emerald-700 font-medium">🎉 恭喜完成精進旅程！</p>
          <button
            onClick={handleNewConversation}
            className="mt-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
          >
            開始新的旅程
          </button>
        </div>
      )}
    </div>
  );
}
