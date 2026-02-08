const BASE_URL = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ===================== 個人檔案 =====================
export const profileApi = {
  listStudents: () => request<any[]>('/profile/students'),
  getStudent: (id: number) => request<any>(`/profile/students/${id}`),
  createStudent: (data: any) =>
    request<any>('/profile/students', { method: 'POST', body: JSON.stringify(data) }),
  updateStudent: (id: number, data: any) =>
    request<any>(`/profile/students/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  addInterest: (studentId: number, data: any) =>
    request<any>(`/profile/students/${studentId}/interests`, { method: 'POST', body: JSON.stringify(data) }),
  removeInterest: (studentId: number, interestId: number) =>
    request<any>(`/profile/students/${studentId}/interests/${interestId}`, { method: 'DELETE' }),
  getAbility: (studentId: number) => request<any>(`/profile/students/${studentId}/ability`),
  getFeedbackSummaries: (studentId: number) => request<any[]>(`/profile/students/${studentId}/feedback-summaries`),
};

// ===================== 題庫 =====================
export const questionApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<any[]>(`/questions/${qs}`);
  },
  get: (id: number) => request<any>(`/questions/${id}`),
  create: (data: any) =>
    request<any>('/questions/', { method: 'POST', body: JSON.stringify(data) }),
  aiGenerate: (scenario: string, difficulty?: string, subject?: string) => {
    const params = new URLSearchParams({ scenario });
    if (difficulty) params.set('difficulty', difficulty);
    if (subject) params.set('subject', subject);
    return request<any>(`/questions/ai-generate?${params}`, { method: 'POST' });
  },
};

// ===================== 時間羅盤 =====================
export const timeCompassApi = {
  listEntries: (studentId: number) => request<any[]>(`/time-compass/${studentId}/entries`),
  addEntry: (studentId: number, data: any) =>
    request<any>(`/time-compass/${studentId}/entries`, { method: 'POST', body: JSON.stringify(data) }),
  getStats: (studentId: number) => request<any>(`/time-compass/${studentId}/stats`),
};

// ===================== 選擇導航 =====================
export const choiceNavApi = {
  listGoals: (studentId: number) => request<any[]>(`/choice-navigator/${studentId}/goals`),
  createGoal: (studentId: number, data: any) =>
    request<any>(`/choice-navigator/${studentId}/goals`, { method: 'POST', body: JSON.stringify(data) }),
};

// ===================== 行動工坊 =====================
export const actionWorkshopApi = {
  listPlans: (studentId: number) => request<any[]>(`/action-workshop/${studentId}/plans`),
  createPlan: (studentId: number, data: any) =>
    request<any>(`/action-workshop/${studentId}/plans`, { method: 'POST', body: JSON.stringify(data) }),
  completePlan: (studentId: number, planId: number) =>
    request<any>(`/action-workshop/${studentId}/plans/${planId}/complete`, { method: 'PUT' }),
  recommendQuestions: (studentId: number, scenario: string) =>
    request<any[]>(`/action-workshop/${studentId}/recommend-questions?scenario=${scenario}`),
};

// ===================== 成長復盤 =====================
export const reviewHubApi = {
  listRecords: (studentId: number, params?: Record<string, string>) => {
    const qs = params ? '&' + new URLSearchParams(params).toString() : '';
    return request<any[]>(`/review-hub/${studentId}/records?${qs}`);
  },
  addReflection: (studentId: number, data: any) =>
    request<any>(`/review-hub/${studentId}/reflect`, { method: 'POST', body: JSON.stringify(data) }),
  getDashboard: (studentId: number) => request<any>(`/review-hub/${studentId}/dashboard`),
};

// ===================== SSE 流式請求 =====================
export async function fetchSSE(
  url: string,
  options: RequestInit,
  onChunk: (text: string) => void,
  onDone?: () => void,
): Promise<void> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok || !res.body) {
    throw new Error(`SSE Error: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim();
        if (data === '[DONE]') {
          onDone?.();
          return;
        }
        try {
          const parsed = JSON.parse(data);
          if (parsed.content) {
            onChunk(parsed.content);
          }
        } catch {
          // ignore parse errors
        }
      }
    }
  }
  onDone?.();
}
