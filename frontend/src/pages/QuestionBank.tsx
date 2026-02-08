import { useState, useEffect } from 'react';
import { Database, Plus, Sparkles } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import ScenarioSelector from '../components/ScenarioSelector';
import { questionApi } from '../services/api';

const difficultyLabels: Record<string, string> = {
  basic: '基礎',
  intermediate: '進階',
  challenge: '挑戰',
};

const difficultyColors: Record<string, string> = {
  basic: 'bg-green-100 text-green-700',
  intermediate: 'bg-amber-100 text-amber-700',
  challenge: 'bg-red-100 text-red-700',
};

export default function QuestionBank() {
  const [questions, setQuestions] = useState<any[]>([]);
  const [scenario, setScenario] = useState('academic');
  const [difficulty, setDifficulty] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState('');
  const [form, setForm] = useState({
    title: '', reference_answer: '', difficulty: 'basic', question_type: '', subject: '',
  });

  useEffect(() => {
    loadQuestions();
  }, [scenario, difficulty]);

  const loadQuestions = () => {
    const params: Record<string, string> = { scenario };
    if (difficulty) params.difficulty = difficulty;
    questionApi.list(params).then(setQuestions).catch(() => {});
  };

  const handleCreate = async () => {
    if (!form.title.trim()) return;
    await questionApi.create({
      ...form,
      scenario,
      subject: form.subject || undefined,
    });
    setShowCreate(false);
    setForm({ title: '', reference_answer: '', difficulty: 'basic', question_type: '', subject: '' });
    loadQuestions();
  };

  const handleAIGenerate = async () => {
    setGenerating(true);
    setGenResult('');
    try {
      const result = await questionApi.aiGenerate(scenario, difficulty || 'basic');
      setGenResult(result.generated);
    } catch {
      setGenResult('生成失敗，請稍後再試');
    }
    setGenerating(false);
  };

  return (
    <div>
      <PageHeader
        title="題庫管理"
        subtitle="結構化練習素材，支持按難度和標籤篩選"
        icon={<Database size={24} />}
      />

      <div className="flex items-center justify-between mb-5">
        <ScenarioSelector value={scenario} onChange={setScenario} />
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1 px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
          >
            <Plus size={16} /> 新增題目
          </button>
          <button
            onClick={handleAIGenerate}
            disabled={generating}
            className="flex items-center gap-1 px-3 py-2 bg-amber-500 text-white text-sm rounded-lg hover:bg-amber-600 disabled:opacity-50"
          >
            <Sparkles size={16} /> {generating ? '生成中...' : 'AI 生成'}
          </button>
        </div>
      </div>

      {/* Difficulty Filter */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setDifficulty('')}
          className={`px-3 py-1.5 text-xs rounded-full ${!difficulty ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
        >
          全部
        </button>
        {Object.entries(difficultyLabels).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setDifficulty(key)}
            className={`px-3 py-1.5 text-xs rounded-full ${difficulty === key ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
          <h3 className="font-semibold text-slate-700 mb-3">新增題目</h3>
          <div className="space-y-3">
            <textarea
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="題幹"
              rows={3}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            />
            <textarea
              value={form.reference_answer}
              onChange={(e) => setForm({ ...form, reference_answer: e.target.value })}
              placeholder="參考答案"
              rows={2}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            />
            <div className="flex gap-3">
              <select value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
                className="px-3 py-2 border border-slate-200 rounded-lg text-sm">
                {Object.entries(difficultyLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <input
                value={form.question_type}
                onChange={(e) => setForm({ ...form, question_type: e.target.value })}
                placeholder="題目類型"
                className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div className="flex gap-2">
              <button onClick={handleCreate} className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">保存</button>
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-slate-100 text-slate-600 text-sm rounded-lg">取消</button>
            </div>
          </div>
        </div>
      )}

      {/* AI Generated Result */}
      {genResult && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 mb-5">
          <h3 className="text-sm font-medium text-amber-800 mb-2">AI 生成結果</h3>
          <pre className="text-sm text-slate-700 whitespace-pre-wrap">{genResult}</pre>
        </div>
      )}

      {/* Questions List */}
      <div className="space-y-3">
        {questions.length === 0 ? (
          <div className="text-center py-10 text-slate-400">暫無題目，點擊新增或 AI 生成</div>
        ) : (
          questions.map((q) => (
            <div key={q.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${difficultyColors[q.difficulty] || 'bg-slate-100'}`}>
                    {difficultyLabels[q.difficulty] || q.difficulty}
                  </span>
                  {q.question_type && (
                    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full">{q.question_type}</span>
                  )}
                </div>
                <span className="text-xs text-slate-400">#{q.id}</span>
              </div>
              <p className="text-sm text-slate-800 mb-2">{q.title}</p>
              {q.reference_answer && (
                <details className="text-sm">
                  <summary className="text-indigo-600 cursor-pointer hover:text-indigo-700">查看參考答案</summary>
                  <p className="mt-2 text-slate-600 bg-slate-50 p-3 rounded-lg">{q.reference_answer}</p>
                </details>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
