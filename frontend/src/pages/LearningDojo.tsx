import { useState } from 'react';
import { BookOpen } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import ScenarioSelector from '../components/ScenarioSelector';
import StreamingText from '../components/StreamingText';
import VoiceButton from '../components/VoiceButton';
import { useSSE } from '../hooks/useSSE';
import { useVoice } from '../hooks/useVoice';

export default function LearningDojo() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [scenario, setScenario] = useState('academic');
  const [activeTab, setActiveTab] = useState<'question' | 'decode' | 'fusion'>('question');
  const [topic, setTopic] = useState('');
  const [content, setContent] = useState('');
  const [knowledgeA, setKnowledgeA] = useState('');
  const [knowledgeB, setKnowledgeB] = useState('');
  const { text, isStreaming, startStream } = useSSE();
  const { isListening, startListening, stopListening, speak, stopSpeaking } = useVoice({
    onEnd: (t) => {
      if (activeTab === 'question') setTopic((prev) => prev + t);
      else if (activeTab === 'decode') setContent((prev) => prev + t);
    },
  });

  const tabs = [
    { key: 'question', label: '以問題為中心' },
    { key: 'decode', label: '知識解碼' },
    { key: 'fusion', label: '知識融合' },
  ];

  const handleSubmit = () => {
    if (!studentId) return;
    if (activeTab === 'question' && topic.trim()) {
      startStream(`/learning-dojo/${studentId}/question-centered-learning?topic=${encodeURIComponent(topic)}&scenario=${scenario}`);
    } else if (activeTab === 'decode' && content.trim()) {
      startStream(`/learning-dojo/${studentId}/decode-knowledge?content=${encodeURIComponent(content)}&scenario=${scenario}`);
    } else if (activeTab === 'fusion' && knowledgeA.trim() && knowledgeB.trim()) {
      startStream(`/learning-dojo/${studentId}/knowledge-fusion?knowledge_a=${encodeURIComponent(knowledgeA)}&knowledge_b=${encodeURIComponent(knowledgeB)}`);
    }
  };

  return (
    <div>
      <PageHeader
        title="學習道場"
        subtitle="直面現實的學習 —— 如何成為高段位學習者"
        icon={<BookOpen size={24} />}
        quote="技能，才是學習的終點。你掌握了多少知識，取決於你能調用多少，而非記住多少"
      />

      <ScenarioSelector value={scenario} onChange={setScenario} className="mb-5" />

      {/* Tabs */}
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

      {/* Input Area */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        {activeTab === 'question' && (
          <>
            <h3 className="font-semibold text-slate-700 mb-2">以問題為中心的學習</h3>
            <p className="text-xs text-slate-500 mb-3">好的學習者，首先要向自己提問</p>
            <div className="flex gap-2">
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="你想學習什麼主題？（如：勾股定理、光的折射）"
                className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
              <VoiceButton isListening={isListening} onToggleListen={isListening ? stopListening : startListening} />
            </div>
          </>
        )}

        {activeTab === 'decode' && (
          <>
            <h3 className="font-semibold text-slate-700 mb-2">知識解碼</h3>
            <p className="text-xs text-slate-500 mb-3">不做信息搬運工 —— 從信息到知識到技能的三層遞進</p>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="把你學到的內容貼在這裡，AI 幫你深度解碼..."
              rows={4}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm mb-2"
            />
            <VoiceButton isListening={isListening} onToggleListen={isListening ? stopListening : startListening} />
          </>
        )}

        {activeTab === 'fusion' && (
          <>
            <h3 className="font-semibold text-slate-700 mb-2">知識融合</h3>
            <p className="text-xs text-slate-500 mb-3">讓不同的知識產生化學反應</p>
            <input
              value={knowledgeA}
              onChange={(e) => setKnowledgeA(e.target.value)}
              placeholder="知識 A（如：牛頓第二定律）"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm mb-2"
            />
            <input
              value={knowledgeB}
              onChange={(e) => setKnowledgeB(e.target.value)}
              placeholder="知識 B（如：供需平衡）"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            />
          </>
        )}

        <button onClick={handleSubmit} className="mt-3 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
          開始學習
        </button>
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
