import { useState, useEffect } from 'react';
import { User, Plus, X } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import { profileApi } from '../services/api';

export default function Profile() {
  const studentId = Number(localStorage.getItem('studentId') || '0');
  const [student, setStudent] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    name: '', grade: '', school: '', target_direction: '', personality: '', learning_style: '',
  });
  const [newInterest, setNewInterest] = useState('');
  const [newInterestDepth, setNewInterestDepth] = useState('3');
  const [feedbacks, setFeedbacks] = useState<any[]>([]);

  useEffect(() => {
    if (studentId) {
      profileApi.getStudent(studentId).then((s) => {
        setStudent(s);
        setForm({
          name: s.name || '',
          grade: s.grade || '',
          school: s.school || '',
          target_direction: s.target_direction || '',
          personality: s.personality || '',
          learning_style: s.learning_style || '',
        });
      }).catch(() => {});
      profileApi.getFeedbackSummaries(studentId).then(setFeedbacks).catch(() => {});
    }
  }, [studentId]);

  const handleSave = async () => {
    if (!studentId) return;
    const updated = await profileApi.updateStudent(studentId, form);
    setStudent(updated);
    setEditing(false);
  };

  const handleAddInterest = async () => {
    if (!newInterest.trim() || !studentId) return;
    await profileApi.addInterest(studentId, {
      topic: newInterest,
      depth: Number(newInterestDepth),
    });
    const s = await profileApi.getStudent(studentId);
    setStudent(s);
    setNewInterest('');
  };

  const handleRemoveInterest = async (interestId: number) => {
    if (!studentId) return;
    await profileApi.removeInterest(studentId, interestId);
    const s = await profileApi.getStudent(studentId);
    setStudent(s);
  };

  if (!student) {
    return (
      <div className="text-center py-20 text-slate-400">
        請先在首頁建立學生檔案
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="個人檔案"
        subtitle="持續精進的核心引擎 —— 你的專屬學習畫像"
        icon={<User size={24} />}
      />

      {/* Basic Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-slate-700">基礎信息</h3>
          <button
            onClick={() => editing ? handleSave() : setEditing(true)}
            className="px-3 py-1.5 bg-indigo-100 text-indigo-700 text-sm rounded-lg hover:bg-indigo-200"
          >
            {editing ? '保存' : '編輯'}
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { key: 'name', label: '姓名' },
            { key: 'grade', label: '年級' },
            { key: 'school', label: '學校' },
            { key: 'target_direction', label: '目標方向' },
            { key: 'personality', label: '性格特點' },
            { key: 'learning_style', label: '學習風格' },
          ].map((field) => (
            <div key={field.key}>
              <label className="text-xs text-slate-500 mb-1 block">{field.label}</label>
              {editing ? (
                <input
                  value={(form as any)[field.key]}
                  onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              ) : (
                <p className="text-sm text-slate-700 px-3 py-2 bg-slate-50 rounded-lg">
                  {(student as any)[field.key] || '未填寫'}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Interests */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
        <h3 className="font-semibold text-slate-700 mb-3">興趣圖譜</h3>
        <div className="flex flex-wrap gap-2 mb-3">
          {(student.interests || []).map((i: any) => (
            <span key={i.id} className="flex items-center gap-1 px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-full text-sm">
              {i.topic}
              <span className="text-xs opacity-60">(深度{i.depth})</span>
              <button onClick={() => handleRemoveInterest(i.id)} className="hover:text-red-500">
                <X size={14} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            value={newInterest}
            onChange={(e) => setNewInterest(e.target.value)}
            placeholder="添加新興趣"
            className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
          />
          <select value={newInterestDepth} onChange={(e) => setNewInterestDepth(e.target.value)}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm">
            {[1,2,3,4,5].map(n => <option key={n} value={n}>深度 {n}</option>)}
          </select>
          <button onClick={handleAddInterest} className="flex items-center gap-1 px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
            <Plus size={16} /> 添加
          </button>
        </div>
      </div>

      {/* Ability Profile */}
      {student.ability_profile && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-5">
          <h3 className="font-semibold text-slate-700 mb-3">能力畫像（AI 動態評估）</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: '語文', key: 'chinese_score' },
              { label: '數學', key: 'math_score' },
              { label: '英語', key: 'english_score' },
              { label: '物理', key: 'physics_score' },
              { label: '邏輯性', key: 'logic_score' },
              { label: '語言組織', key: 'language_score' },
              { label: '說服力', key: 'persuasion_score' },
              { label: '創造性', key: 'creativity_score' },
              { label: '自信度', key: 'confidence_score' },
              { label: '應變力', key: 'responsiveness_score' },
              { label: '回答深度', key: 'depth_score' },
              { label: '獨特性', key: 'uniqueness_score' },
            ].map((item) => (
              <div key={item.key} className="text-center p-3 bg-slate-50 rounded-lg">
                <div className="text-xs text-slate-500 mb-1">{item.label}</div>
                <div className="text-lg font-semibold text-indigo-600">
                  {student.ability_profile[item.key]}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feedback Summaries */}
      {feedbacks.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <h3 className="font-semibold text-slate-700 mb-3">AI 反饋摘要</h3>
          <div className="space-y-3">
            {feedbacks.map((fb) => (
              <div key={fb.id} className="p-4 bg-slate-50 rounded-lg">
                <div className="text-xs font-medium text-indigo-600 mb-2">{fb.scenario}</div>
                {fb.strengths && <p className="text-sm text-emerald-700 mb-1">優勢：{fb.strengths}</p>}
                {fb.weaknesses && <p className="text-sm text-orange-700 mb-1">短板：{fb.weaknesses}</p>}
                {fb.progress_trend && <p className="text-sm text-blue-700 mb-1">趨勢：{fb.progress_trend}</p>}
                {fb.ai_suggestions && <p className="text-sm text-slate-600">建議：{fb.ai_suggestions}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
