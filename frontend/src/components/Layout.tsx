import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  Clock, Compass, Zap, BookOpen, Brain, Target, BarChart3, Home, User, Database, MessageCircle
} from 'lucide-react';

const navItems = [
  { path: '/', label: '首頁', icon: Home },
  { path: '/journey', label: '精進旅程', icon: MessageCircle, highlight: true },
  { path: '/time-compass', label: '時間羅盤', icon: Clock },
  { path: '/choice-navigator', label: '選擇導航', icon: Compass },
  { path: '/action-workshop', label: '行動工坊', icon: Zap },
  { path: '/learning-dojo', label: '學習道場', icon: BookOpen },
  { path: '/thinking-forge', label: '思維鍛造', icon: Brain },
  { path: '/talent-growth', label: '才能精進', icon: Target },
  { path: '/review-hub', label: '成長復盤', icon: BarChart3 },
  { path: '/profile', label: '個人檔案', icon: User },
  { path: '/question-bank', label: '題庫管理', icon: Database },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0">
        <div className="p-5 border-b border-slate-200">
          <h1 className="text-xl font-bold text-indigo-600">精進學習系統</h1>
          <p className="text-xs text-slate-500 mt-1">成為一個很厲害的人</p>
        </div>
        <nav className="flex-1 overflow-y-auto py-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            const highlight = 'highlight' in item && item.highlight;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-5 py-2.5 text-sm transition-colors',
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 font-medium border-r-2 border-indigo-600'
                    : highlight
                      ? 'text-indigo-600 bg-indigo-50/50 hover:bg-indigo-50 font-medium'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                )}
              >
                <Icon size={18} />
                {item.label}
                {highlight && !isActive && (
                  <span className="ml-auto text-[10px] bg-indigo-600 text-white px-1.5 py-0.5 rounded-full">AI</span>
                )}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-slate-200 text-xs text-slate-400">
          基於《精進》· 采銅 著
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-slate-50">
        <div className="max-w-5xl mx-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
