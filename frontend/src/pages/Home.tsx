import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { reviewHubApi, profileApi } from '../services/api';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer,
  Tooltip,
} from 'recharts';
import {
  Clock, Compass, Zap, BookOpen, Brain, Target, BarChart3, UserPlus
} from 'lucide-react';

const moduleCards = [
  { path: '/time-compass', label: '時間羅盤', icon: Clock, color: 'bg-blue-50 text-blue-600', desc: '管理你的半衰期' },
  { path: '/choice-navigator', label: '選擇導航', icon: Compass, color: 'bg-purple-50 text-purple-600', desc: '找到心中的巴拿馬' },
  { path: '/action-workshop', label: '行動工坊', icon: Zap, color: 'bg-amber-50 text-amber-600', desc: '即刻行動，圖層分解' },
  { path: '/learning-dojo', label: '學習道場', icon: BookOpen, color: 'bg-emerald-50 text-emerald-600', desc: '以問題為中心學習' },
  { path: '/thinking-forge', label: '思維鍛造', icon: Brain, color: 'bg-pink-50 text-pink-600', desc: '修煉思維利器' },
  { path: '/talent-growth', label: '才能精進', icon: Target, color: 'bg-orange-50 text-orange-600', desc: '設計必要的難度' },
  { path: '/review-hub', label: '成長復盤', icon: BarChart3, color: 'bg-cyan-50 text-cyan-600', desc: '三行而後思' },
];

const radarLabels: Record<string, string> = {
  academic: '學科',
  expression: '表達',
  interview: '面試',
  time_management: '時間',
  thinking: '思維',
  effort_strategy: '努力',
  uniqueness: '獨特性',
};

export default function Home() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [studentId, setStudentId] = useState<number | null>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newGrade, setNewGrade] = useState('');

  useEffect(() => {
    profileApi.listStudents().then((list) => {
      setStudents(list);
      if (list.length > 0) {
        const id = list[0].id;
        setStudentId(id);
        localStorage.setItem('studentId', String(id));
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (studentId) {
      reviewHubApi.getDashboard(studentId).then(setDashboard).catch(() => {});
    }
  }, [studentId]);

  const radarData = dashboard?.radar_data
    ? Object.entries(dashboard.radar_data).map(([key, value]) => ({
        dimension: radarLabels[key] || key,
        score: value as number,
      }))
    : [];

  const handleCreateStudent = async () => {
    if (!newName.trim()) return;
    try {
      const s = await profileApi.createStudent({ name: newName, grade: newGrade });
      setStudents([...students, s]);
      setStudentId(s.id);
      localStorage.setItem('studentId', String(s.id));
      setShowCreate(false);
      setNewName('');
      setNewGrade('');
    } catch {}
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">
            {dashboard ? `${dashboard.student_name}，歡迎回來` : '歡迎來到精進學習系統'}
          </h1>
          <p className="text-slate-500 mt-1">盲目的努力，只是一種緩慢的疊加。精準的方法，才能帶來質的飛躍。</p>
        </div>
        <div className="flex items-center gap-2">
          {students.length > 0 && (
            <select
              value={studentId || ''}
              onChange={(e) => {
                const id = Number(e.target.value);
                setStudentId(id);
                localStorage.setItem('studentId', String(id));
              }}
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
            >
              {students.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          )}
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1 px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <UserPlus size={16} />
            新增學生
          </button>
        </div>
      </div>

      {/* Create student modal */}
      {showCreate && (
        <div className="mb-6 p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <h3 className="font-semibold mb-3">建立新的學生檔案</h3>
          <div className="flex gap-3">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="姓名"
              className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
            />
            <input
              value={newGrade}
              onChange={(e) => setNewGrade(e.target.value)}
              placeholder="年級（如：初二）"
              className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
            />
            <button onClick={handleCreateStudent} className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
              建立
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-slate-100 text-slate-600 text-sm rounded-lg hover:bg-slate-200">
              取消
            </button>
          </div>
        </div>
      )}

      {/* Radar Chart */}
      {radarData.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-6">
          <h2 className="text-lg font-semibold text-slate-700 mb-3">能力雷達圖</h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 13, fill: '#64748b' }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Module Cards */}
      <h2 className="text-lg font-semibold text-slate-700 mb-3">七大精進模組</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {moduleCards.map((card) => {
          const Icon = card.icon;
          const count = dashboard?.module_stats?.[card.path.replace('/', '').replace(/-/g, '_')] || 0;
          return (
            <Link
              key={card.path}
              to={card.path}
              className="group bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className={`p-2.5 rounded-lg ${card.color}`}>
                  <Icon size={22} />
                </div>
                {count > 0 && (
                  <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full">{count} 次練習</span>
                )}
              </div>
              <h3 className="mt-3 font-semibold text-slate-800 group-hover:text-indigo-600 transition-colors">
                {card.label}
              </h3>
              <p className="text-sm text-slate-500 mt-1">{card.desc}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
