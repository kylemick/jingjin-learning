import { useState, useEffect } from 'react';
import { Target } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import ScenarioSelector from '../components/ScenarioSelector';
import StreamingText from '../components/StreamingText';
import VoiceButton from '../components/VoiceButton';
import { useSSE } from '../hooks/useSSE';
import { useVoice } from '../hooks/useVoice';
import { profileApi } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

export default function TalentGrowth() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [scenario, setScenario] = useState('academic');
  const [currentTopic, setCurrentTopic] = useState('');
  const [ability, setAbility] = useState<any>(null);
  const { text, isStreaming, startStream } = useSSE();
  const { speak, stopSpeaking } = useVoice();

  useEffect(() => {
    if (studentId) {
      profileApi.getAbility(studentId).then(setAbility).catch(() => {});
    }
  }, [studentId]);

  const handleStrengthAnalysis = () => {
    if (!studentId) return;
    startStream(`/talent-growth/${studentId}/strength-analysis`);
  };

  const handleDesignChallenge = () => {
    if (!studentId) return;
    const topicParam = currentTopic ? `&current_topic=${encodeURIComponent(currentTopic)}` : '';
    startStream(`/talent-growth/${studentId}/design-challenge?scenario=${scenario}${topicParam}`);
  };

  const abilityChartData = ability ? [
    { name: '語文', score: ability.chinese_score },
    { name: '數學', score: ability.math_score },
    { name: '英語', score: ability.english_score },
    { name: '物理', score: ability.physics_score },
    { name: '邏輯', score: ability.logic_score },
    { name: '語言', score: ability.language_score },
    { name: '自信', score: ability.confidence_score },
    { name: '應變', score: ability.responsiveness_score },
    { name: '創造', score: ability.creativity_score },
  ] : [];

  return (
    <div>
      <PageHeader
        title="才能精進"
        subtitle="努力，是一種需要學習的才能"
        icon={<Target size={24} />}
        quote="意志力是不可靠的，賜予你力量的是激情的驅動，而不是意志力的鞭策"
      />

      <ScenarioSelector value={scenario} onChange={setScenario} className="mb-5" />

      {/* Ability Chart */}
      {abilityChartData.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
          <h3 className="font-semibold text-slate-700 mb-3">能力畫像</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={abilityChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="score" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <h3 className="font-semibold text-slate-700 mb-2">長板優勢識別</h3>
          <p className="text-xs text-slate-500 mb-3">沒有突出的長板就是危險，找到並發展你的核心優勢</p>
          <button onClick={handleStrengthAnalysis} className="px-4 py-2 bg-emerald-500 text-white text-sm rounded-lg hover:bg-emerald-600">
            分析我的優勢
          </button>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <h3 className="font-semibold text-slate-700 mb-2">必要難度挑戰</h3>
          <p className="text-xs text-slate-500 mb-3">挑戰是設計出來的 —— 略高於舒適區的挑戰最有效</p>
          <input
            value={currentTopic}
            onChange={(e) => setCurrentTopic(e.target.value)}
            placeholder="當前學習主題（可選）"
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm mb-2"
          />
          <button onClick={handleDesignChallenge} className="px-4 py-2 bg-orange-500 text-white text-sm rounded-lg hover:bg-orange-600">
            設計挑戰
          </button>
        </div>
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
