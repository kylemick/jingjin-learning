import { useState, useEffect } from 'react';
import { BarChart3 } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import ScenarioSelector from '../components/ScenarioSelector';
import StreamingText from '../components/StreamingText';
import VoiceButton from '../components/VoiceButton';
import { useSSE } from '../hooks/useSSE';
import { useVoice } from '../hooks/useVoice';
import { reviewHubApi } from '../services/api';

export default function ReviewHub() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [scenario, setScenario] = useState('academic');
  const [records, setRecords] = useState<any[]>([]);
  const [feedbackContent, setFeedbackContent] = useState('');
  const [reflectionText, setReflectionText] = useState('');
  const [selectedRecord, setSelectedRecord] = useState<number | null>(null);
  const { text, isStreaming, startStream } = useSSE();
  const { isListening, startListening, stopListening, speak, stopSpeaking } = useVoice({
    onEnd: (t) => setFeedbackContent((prev) => prev + t),
  });

  useEffect(() => {
    if (studentId) {
      reviewHubApi.listRecords(studentId).then(setRecords).catch(() => {});
    }
  }, [studentId]);

  const handleDeepFeedback = () => {
    if (!feedbackContent.trim() || !studentId) return;
    startStream(`/review-hub/${studentId}/deep-feedback?scenario=${scenario}&content=${encodeURIComponent(feedbackContent)}`);
  };

  const handleReflect = async () => {
    if (!selectedRecord || !reflectionText.trim() || !studentId) return;
    await reviewHubApi.addReflection(studentId, {
      record_id: selectedRecord,
      reflection: reflectionText,
    });
    setReflectionText('');
    setSelectedRecord(null);
    // Refresh records
    reviewHubApi.listRecords(studentId).then(setRecords).catch(() => {});
  };

  const handleUpdateProfile = async () => {
    if (!studentId) return;
    try {
      await fetch(`/api/review-hub/${studentId}/update-profile-from-feedback?scenario=${scenario}`, {
        method: 'POST',
      });
      alert('個人檔案已更新！');
    } catch {}
  };

  return (
    <div>
      <PageHeader
        title="成長復盤"
        subtitle="創造成功，而不是複製成功"
        icon={<BarChart3 size={24} />}
        quote="做一個主動探索的學習者。獨特性，就是你的核心競爭力"
      />

      <ScenarioSelector value={scenario} onChange={setScenario} className="mb-5" />

      {/* Deep Feedback */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        <h3 className="font-semibold text-slate-700 mb-2">AI 深度反饋</h3>
        <p className="text-xs text-slate-500 mb-3">提交你的作品/練習，獲取深度、具體、有建設性的反饋</p>
        <div className="flex gap-2 mb-3">
          <textarea
            value={feedbackContent}
            onChange={(e) => setFeedbackContent(e.target.value)}
            placeholder="在此貼入你的作品/練習/回答..."
            rows={4}
            className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
          />
        </div>
        <div className="flex gap-2">
          <button onClick={handleDeepFeedback} className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
            獲取深度反饋
          </button>
          <VoiceButton isListening={isListening} onToggleListen={isListening ? stopListening : startListening} />
          <button onClick={handleUpdateProfile} className="px-4 py-2 bg-emerald-500 text-white text-sm rounded-lg hover:bg-emerald-600">
            更新個人檔案
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
          className="mb-5"
        />
      )}

      {/* Learning Records */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        <h3 className="font-semibold text-slate-700 mb-3">學習記錄 · 三行而後思</h3>
        {records.length === 0 ? (
          <p className="text-sm text-slate-400">還沒有學習記錄。去行動工坊完成一些練習吧！</p>
        ) : (
          <div className="space-y-3">
            {records.map((r) => (
              <div key={r.id} className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full">
                      {r.module}
                    </span>
                    {r.scenario && (
                      <span className="text-xs bg-slate-200 text-slate-600 px-2 py-1 rounded-full">{r.scenario}</span>
                    )}
                  </div>
                  <span className="text-xs text-slate-400">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}
                  </span>
                </div>
                {r.content && <p className="text-sm text-slate-600 mb-2">{r.content.substring(0, 200)}</p>}
                {r.ai_feedback && (
                  <div className="text-sm text-slate-700 bg-blue-50 p-3 rounded-lg mb-2">
                    <span className="text-xs font-medium text-blue-600">AI 反饋：</span>
                    <p className="mt-1">{r.ai_feedback.substring(0, 300)}</p>
                  </div>
                )}
                {r.reflection ? (
                  <div className="text-sm text-emerald-700 bg-emerald-50 p-3 rounded-lg">
                    <span className="text-xs font-medium">我的反思：</span>
                    <p className="mt-1">{r.reflection}</p>
                  </div>
                ) : (
                  <div>
                    {selectedRecord === r.id ? (
                      <div className="flex gap-2">
                        <textarea
                          value={reflectionText}
                          onChange={(e) => setReflectionText(e.target.value)}
                          placeholder="寫下你的反思..."
                          rows={2}
                          className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
                        />
                        <button onClick={handleReflect} className="px-3 py-1 bg-emerald-500 text-white text-xs rounded-lg">
                          提交
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setSelectedRecord(r.id)}
                        className="text-xs text-emerald-600 hover:text-emerald-700"
                      >
                        + 添加反思（三行而後思）
                      </button>
                    )}
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
