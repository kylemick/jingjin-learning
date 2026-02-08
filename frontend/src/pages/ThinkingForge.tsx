import { useState } from 'react';
import { Brain } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import ScenarioSelector from '../components/ScenarioSelector';
import StreamingText from '../components/StreamingText';
import VoiceButton from '../components/VoiceButton';
import { useSSE } from '../hooks/useSSE';
import { useVoice } from '../hooks/useVoice';

const thinkingTools = [
  { key: 'argument', label: '論點-論據-結論', desc: '三段式結構思考' },
  { key: 'matrix', label: '矩陣分析', desc: '多維度對比分析' },
  { key: 'mindmap', label: '思維導圖', desc: '發散-收斂思考' },
  { key: 'timeline', label: '因果鏈', desc: '時間線因果分析' },
];

export default function ThinkingForge() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [scenario, setScenario] = useState('academic');
  const [activeTab, setActiveTab] = useState<'socratic' | 'simplify' | 'structured'>('socratic');
  const [topic, setTopic] = useState('');
  const [answer, setAnswer] = useState('');
  const [problem, setProblem] = useState('');
  const [tool, setTool] = useState('argument');
  const { text, isStreaming, startStream } = useSSE();
  const { isListening, startListening, stopListening, speak, stopSpeaking } = useVoice({
    onEnd: (t) => {
      if (activeTab === 'socratic') setAnswer((prev) => prev + t);
      else if (activeTab === 'simplify') setProblem((prev) => prev + t);
      else setTopic((prev) => prev + t);
    },
  });

  const handleSocratic = () => {
    if (!topic.trim() || !studentId) return;
    startStream(`/thinking-forge/${studentId}/socratic-dialogue?topic=${encodeURIComponent(topic)}&student_answer=${encodeURIComponent(answer)}&scenario=${scenario}`);
    setAnswer('');
  };

  const handleSimplify = () => {
    if (!problem.trim() || !studentId) return;
    startStream(`/thinking-forge/${studentId}/simplify?complex_problem=${encodeURIComponent(problem)}`);
  };

  const handleStructured = () => {
    if (!topic.trim() || !studentId) return;
    startStream(`/thinking-forge/${studentId}/structured-thinking?topic=${encodeURIComponent(topic)}&thinking_tool=${tool}`);
  };

  const tabs = [
    { key: 'socratic', label: '蘇格拉底問答' },
    { key: 'simplify', label: '斷捨離簡化' },
    { key: 'structured', label: '結構化思考' },
  ];

  return (
    <div>
      <PageHeader
        title="思維鍛造"
        subtitle="修煉思維，成為真正的利器"
        icon={<Brain size={24} />}
        quote="世界上沒有輕而易舉的答案，只有極少數的人能做到周密思考"
      />

      <ScenarioSelector value={scenario} onChange={setScenario} className="mb-5" />

      <div className="flex gap-1 mb-5 bg-slate-100 p-1 rounded-lg w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              activeTab === tab.key ? 'bg-white text-indigo-700 font-medium shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        {activeTab === 'socratic' && (
          <>
            <h3 className="font-semibold text-slate-700 mb-2">蘇格拉底式問答</h3>
            <p className="text-xs text-slate-500 mb-3">層層深入的思維對話，通過提問發現真理</p>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="你想探討什麼主題？"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm mb-2"
            />
            <div className="flex gap-2">
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="你的回答/想法（可選，留空則開始新對話）"
                rows={3}
                className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
              <VoiceButton isListening={isListening} onToggleListen={isListening ? stopListening : startListening} />
            </div>
            <button onClick={handleSocratic} className="mt-3 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
              開始對話
            </button>
          </>
        )}

        {activeTab === 'simplify' && (
          <>
            <h3 className="font-semibold text-slate-700 mb-2">斷捨離簡化</h3>
            <p className="text-xs text-slate-500 mb-3">簡化是清晰思考的前提，大腦需要斷捨離</p>
            <div className="flex gap-2 mb-3">
              <textarea
                value={problem}
                onChange={(e) => setProblem(e.target.value)}
                placeholder="描述你面對的複雜問題或情境..."
                rows={4}
                className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
              <VoiceButton isListening={isListening} onToggleListen={isListening ? stopListening : startListening} />
            </div>
            <button onClick={handleSimplify} className="px-4 py-2 bg-pink-500 text-white text-sm rounded-lg hover:bg-pink-600">
              開始簡化
            </button>
          </>
        )}

        {activeTab === 'structured' && (
          <>
            <h3 className="font-semibold text-slate-700 mb-2">結構化思考</h3>
            <p className="text-xs text-slate-500 mb-3">思考可以有自己的形狀，選擇一個思維工具</p>
            <div className="grid grid-cols-2 gap-2 mb-3">
              {thinkingTools.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setTool(t.key)}
                  className={`p-3 rounded-lg border text-left text-sm transition-colors ${
                    tool === t.key ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="font-medium text-slate-700">{t.label}</div>
                  <div className="text-xs text-slate-500">{t.desc}</div>
                </button>
              ))}
            </div>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="你想思考什麼主題？"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm mb-3"
            />
            <button onClick={handleStructured} className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
              開始結構化思考
            </button>
          </>
        )}
      </div>

      <StreamingText text={text} isStreaming={isStreaming} className="mb-5" />
      {text && !isStreaming && (
        <VoiceButton
          isListening={false}
          onToggleListen={() => {}}
          onSpeak={() => speak(text)}
          onStopSpeak={stopSpeaking}
        />
      )}
    </div>
  );
}
