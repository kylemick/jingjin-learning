import { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import StreamingText from '../components/StreamingText';
import VoiceButton from '../components/VoiceButton';
import { useSSE } from '../hooks/useSSE';
import { useVoice } from '../hooks/useVoice';
import { timeCompassApi } from '../services/api';

export default function TimeCompass() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [entries, setEntries] = useState<any[]>([]);
  const [activity, setActivity] = useState('');
  const [duration, setDuration] = useState('30');
  const [halfLife, setHalfLife] = useState('long');
  const [benefit, setBenefit] = useState('3');
  const { text, isStreaming, startStream } = useSSE();
  const { isListening, isTranscribing, isSpeaking, transcript, error, startListening, stopListening, speak, stopSpeaking } = useVoice({
    onEnd: (t) => setActivity((prev) => prev + t),
  });

  useEffect(() => {
    if (studentId) {
      timeCompassApi.listEntries(studentId).then(setEntries).catch(() => {});
    }
  }, [studentId]);

  const handleAdd = async () => {
    if (!activity.trim() || !studentId) return;
    const entry = await timeCompassApi.addEntry(studentId, {
      activity,
      duration_minutes: Number(duration),
      half_life: halfLife,
      benefit_value: Number(benefit),
    });
    setEntries([entry, ...entries]);
    setActivity('');
  };

  const handleAnalyze = () => {
    if (!studentId) return;
    startStream(`/time-compass/${studentId}/ai-analyze`);
  };

  return (
    <div>
      <PageHeader
        title="時間羅盤"
        subtitle="時間之尺 —— 我們應該怎樣對待時間"
        icon={<Clock size={24} />}
        quote="把時間花在值得做的事情上——收益值高、半衰期長的事情"
      />

      {/* Add Entry */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        <h3 className="font-semibold text-slate-700 mb-3">記錄時間投入</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          <div>
            <label className="text-xs text-slate-500 mb-1 block">活動內容</label>
            <div className="flex gap-2">
              <input
                value={activity}
                onChange={(e) => setActivity(e.target.value)}
                placeholder="例如：複習數學三角函數"
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
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">時長(分鐘)</label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">半衰期</label>
              <select value={halfLife} onChange={(e) => setHalfLife(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm">
                <option value="long">長</option>
                <option value="short">短</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">收益值</label>
              <select value={benefit} onChange={(e) => setBenefit(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm">
                {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={handleAdd} className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
            記錄
          </button>
          <button onClick={handleAnalyze} className="px-4 py-2 bg-amber-500 text-white text-sm rounded-lg hover:bg-amber-600">
            AI 分析我的時間使用
          </button>
        </div>
      </div>

      {/* AI Analysis */}
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

      {/* Entries List */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h3 className="font-semibold text-slate-700 mb-3">時間記錄</h3>
        {entries.length === 0 ? (
          <p className="text-sm text-slate-400">還沒有時間記錄，開始記錄你的時間投入吧！</p>
        ) : (
          <div className="space-y-2">
            {entries.map((e) => (
              <div key={e.id} className="flex items-center justify-between px-4 py-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    e.half_life === 'long' ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'
                  }`}>
                    {e.half_life === 'long' ? '長半衰期' : '短半衰期'}
                  </span>
                  <span className="text-sm text-slate-700">{e.activity}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span>{e.duration_minutes} 分鐘</span>
                  <span>收益 {e.benefit_value}/5</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
