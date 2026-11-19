const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export async function request(path, options = {}) {
  const token = localStorage.getItem('note_by_sp_token');
  let response;
  try {
    response = await fetch(API + path, {
      ...options,
      headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: 'Bearer ' + token } : {}), ...options.headers },
    });
  } catch { throw new Error('เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาตรวจสอบ Docker และ API'); }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/auth/')) {
      localStorage.removeItem('note_by_sp_token');
      window.dispatchEvent(new Event('note-by-sp-unauthorized'));
    }
    throw new Error(typeof data.detail === 'string' ? data.detail : 'เกิดข้อผิดพลาด');
  }
  return data;
}
export const api = {
  register: (body) => request('/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  login: (body) => request('/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  me: () => request('/auth/me'),
  dashboard: () => request('/dashboard'),
  subjects: () => request('/subjects'),
  addSubject: (body) => request('/subjects', { method: 'POST', body: JSON.stringify(body) }),
  deleteSubject: (id) => request('/subjects/' + id, { method: 'DELETE' }),
  notes: () => request('/notes'),
  createNote: (body) => request('/notes', { method: 'POST', body: JSON.stringify(body) }),
  updateNote: (id, body) => request('/notes/' + id, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteNote: (id) => request('/notes/' + id, { method: 'DELETE' }),
};
