export const BASE_URL = 'https://unrepulsed-diedre-nonfrenetic.ngrok-free.dev';

async function request(method, path, body = null, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data;
  try { data = await res.json(); } catch { data = {}; }
  return { ok: res.ok, status: res.status, data };
}

export default {
  login: (email, password) =>
    request('POST', '/api/login', { email, password }),

  register: (full_name, email, password) =>
    request('POST', '/api/register', { full_name, email, password }),

  verifyOtp: (email, code) =>
    request('POST', '/api/verify-otp', { email, code }),

  resendOtp: (email) =>
    request('POST', '/api/resend-otp', { email }),

  predict: (url, token) =>
    request('POST', '/api/predict', { url }, token),

  getHistory: (token) =>
    request('GET', '/api/history', null, token),

  getProfile: (token) =>
    request('GET', '/api/profile', null, token),

  updateProfile: (data, token) =>
    request('PUT', '/api/profile', data, token),

  uploadImage: async (uri, token) => {
    const filename = uri.split('/').pop();
    const ext = filename.split('.').pop().toLowerCase();
    const type = ext === 'png' ? 'image/png' : 'image/jpeg';
    const form = new FormData();
    form.append('image', { uri, name: filename, type });

    const res = await fetch(`${BASE_URL}/api/profile/image`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    let data;
    try { data = await res.json(); } catch { data = {}; }
    return { ok: res.ok, data };
  },
};
