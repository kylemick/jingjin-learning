import { useState } from 'react';
import { Zap } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import ScenarioSelector from '../components/ScenarioSelector';
import StreamingText from '../components/StreamingText';
import VoiceButton from '../components/VoiceButton';
import { useSSE } from '../hooks/useSSE';
import { useVoice } from '../hooks/useVoice';

export default function ActionWorkshop() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [scenario, setScenario] = useState('academic');
  const [taskDesc, setTaskDesc] = useState('');
  const [practiceContent, setPracticeContent] = useState('');
  const [mode, setMode] = useState<'decompose' | 'practice'>('decompose');
  const { text, isStreaming, startStream } = useSSE();
  const { isListening, isTranscribing, isSpeaking, error, startListening, stopListening, speak, stopSpeaking } = useVoice({
    onEnd: (t) => {
      if (mode === 'decompose') setTaskDesc((prev) => prev + t);
      else setPracticeContent((prev) => prev + t);
    },
  });

  const handleDecompose = () => {
    if (!taskDesc.trim() || !studentId) return;
    setMode('decompose');
    startStream(`/action-workshop/${studentId}/decompose-task?task_description=${encodeURIComponent(taskDesc)}`);
  };

  const handleSubmitPractice = () => {
    if (!practiceContent.trim() || !studentId) return;
    setMode('practice');
    startStream(`/action-workshop/${studentId}/submit-practice`, {
      module: 'action_workshop',
      scenario,
      content: practiceContent,
    });
  };

  return (
    <div>
      <PageHeader
        title="行動工坊"
        subtitle="即刻行動 —— 改變一切的核心力量"
        icon={<Zap size={24} />}
        quote="當一件事你不知道怎麼做的時候，就直接開始做吧。只要開始了第一步，就會有第二步、第三步"
      />

      <ScenarioSelector value={scenario} onChange={setScenario} className="mb-5" />

      {/* Task Decomposition */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        <h3 className="font-semibold text-slate-700 mb-3">圖層工作法 - 任務分解</h3>
        <p className="text-xs text-slate-500 mb-3">
          像 Photoshop 分圖層一樣：先處理核心思考區間，再處理細節支撐
        </p>
        <div className="flex gap-2 mb-3">
          <input
            value={taskDesc}
            onChange={(e) => setTaskDesc(e.target.value)}
            placeholder="描述你要完成的任務..."
            className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
          />
          <VoiceButton
            isListening={isListening && mode === 'decompose'}
            isTranscribing={isTranscribing}
            onToggleListen={() => {
              setMode('decompose');
              isListening ? stopListening() : startListening();
            }}
            error={error}
          />
        </div>
        <button onClick={handleDecompose} className="px-4 py-2 bg-amber-500 text-white text-sm rounded-lg hover:bg-amber-600">
          AI 分解任務
        </button>
      </div>

      {/* Practice Submission */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        <h3 className="font-semibold text-slate-700 mb-3">提交練習</h3>
        <p className="text-xs text-slate-500 mb-3">完成練習後提交，獲取 AI 即時反饋</p>
        <div className="flex gap-2 mb-3">
          <textarea
            value={practiceContent}
            onChange={(e) => setPracticeContent(e.target.value)}
            placeholder="在此輸入你的回答/練習內容..."
            rows={4}
            className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
          />
        </div>
        <div className="flex gap-2">
          <button onClick={handleSubmitPractice} className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
            提交並獲取反饋
          </button>
          <VoiceButton
            isListening={isListening && mode === 'practice'}
            isTranscribing={isTranscribing}
            onToggleListen={() => {
              setMode('practice');
              isListening ? stopListening() : startListening();
            }}
            error={error}
          />
        </div>
      </div>

      {/* AI Response */}
      <StreamingText text={text} isStreaming={isStreaming} className="mb-5" />
      {text && !isStreaming && (
        <VoiceButton
          isListening={false}
          onToggleListen={() => {}}
          onSpeak={() => speak(text)}
          onStopSpeak={stopSpeaking}
          isSpeaking={isSpeaking}
          className="mb-5"
        />
      )}
    </div>
  );
}
