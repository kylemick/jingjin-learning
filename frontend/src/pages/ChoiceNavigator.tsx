import { useState, useEffect } from 'react';
import { Compass } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import ScenarioSelector from '../components/ScenarioSelector';
import StreamingText from '../components/StreamingText';
import VoiceButton from '../components/VoiceButton';
import { useSSE } from '../hooks/useSSE';
import { useVoice } from '../hooks/useVoice';
import { choiceNavApi } from '../services/api';

export default function ChoiceNavigator() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [goals, setGoals] = useState<any[]>([]);
  const [scenario, setScenario] = useState('academic');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [vision, setVision] = useState('');
  const { text, isStreaming, startStream } = useSSE();
  const { isListening, isTranscribing, isSpeaking, transcript, error, startListening, stopListening, speak, stopSpeaking } = useVoice({
    onEnd: (t) => setTitle((prev) => prev + t),
  });

  useEffect(() => {
    if (studentId) {
      choiceNavApi.listGoals(studentId).then(setGoals).catch(() => {});
    }
  }, [studentId]);

  const handleCreate = async () => {
    if (!title.trim() || !studentId) return;
    const goal = await choiceNavApi.createGoal(studentId, {
      scenario, title, description, five_year_vision: vision,
    });
    setGoals([goal, ...goals]);
    setTitle('');
    setDescription('');
    setVision('');
  };

  const handleExploreAssumptions = (goalId: number) => {
    startStream(`/choice-navigator/${studentId}/explore-assumptions?goal_id=${goalId}`);
  };

  return (
    <div>
      <PageHeader
        title="選擇導航"
        subtitle="尋找心中的巴拿馬 —— 如何做出比好更好的選擇"
        icon={<Compass size={24} />}
        quote="不管你做了哪個選擇，最終帶著你走向目的地的，可能並不是某一個選擇，而是那些你不會改變的東西"
      />

      <ScenarioSelector value={scenario} onChange={setScenario} className="mb-5" />

      {/* Create Goal */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        <h3 className="font-semibold text-slate-700 mb-3">設定目標</h3>
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="你的目標是什麼？"
              className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
            />
            <VoiceButton
              isListening={isListening}
              isTranscribing={isTranscribing}
              onToggleListen={isListening ? stopListening : startListening}
              transcript={transcript}
              error={error}
            />
          </div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="描述一下這個目標..."
            rows={2}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
          />
          <textarea
            value={vision}
            onChange={(e) => setVision(e.target.value)}
            placeholder="五年後的自己會是什麼樣子？（具象化你的遠期未來）"
            rows={2}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
          />
          <button onClick={handleCreate} className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
            建立目標
          </button>
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

      {/* Goals List */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h3 className="font-semibold text-slate-700 mb-3">我的目標</h3>
        {goals.length === 0 ? (
          <p className="text-sm text-slate-400">還沒有目標，從終極問題出發，設定你的第一個目標吧！</p>
        ) : (
          <div className="space-y-3">
            {goals.map((g) => (
              <div key={g.id} className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-slate-800">{g.title}</h4>
                    {g.description && <p className="text-sm text-slate-500 mt-1">{g.description}</p>}
                    {g.five_year_vision && (
                      <p className="text-sm text-indigo-600 mt-1">願景：{g.five_year_vision}</p>
                    )}
                  </div>
                  <button
                    onClick={() => handleExploreAssumptions(g.id)}
                    className="shrink-0 px-3 py-1.5 bg-purple-100 text-purple-700 text-xs rounded-lg hover:bg-purple-200"
                  >
                    識別隱含假設
                  </button>
                </div>
                {g.hidden_assumptions && (
                  <div className="mt-2 text-sm text-slate-600 bg-purple-50 p-3 rounded-lg">
                    {g.hidden_assumptions}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
