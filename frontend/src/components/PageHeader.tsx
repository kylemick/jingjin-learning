interface PageHeaderProps {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  quote?: string;
}

export default function PageHeader({ title, subtitle, icon, quote }: PageHeaderProps) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 mb-1">
        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
          {icon}
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>
      </div>
      {quote && (
        <div className="mt-3 px-4 py-2 bg-amber-50 border-l-4 border-amber-400 text-sm text-amber-800 italic rounded-r-lg">
          "{quote}" —— 《精進》
        </div>
      )}
    </div>
  );
}
