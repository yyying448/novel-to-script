import type { Provider, SSEEvent, ConvertParams } from '../types';

const BASE = '/api';

export async function fetchProviders(): Promise<Provider[]> {
  const r = await fetch(`${BASE}/providers`);
  const d = await r.json();
  return d.success ? d.providers : [];
}

export async function validateKey(key: string, provider: string, baseUrl?: string) {
  const r = await fetch(`${BASE}/validate-key`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: '', api_key: key, provider, base_url: baseUrl || null }),
  });
  return r.json();
}

export async function parseFile(file: File) {
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`${BASE}/parse-file`, { method: 'POST', body: fd });
  return r.json();
}

export async function previewChapters(params: Partial<ConvertParams>) {
  const r = await fetch(`${BASE}/preview-chapters`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}

export function convertNovel(
  params: ConvertParams,
  onEvent: (e: SSEEvent) => void,
  onDone: () => void,
  onError: (e: string) => void
) {
  fetch(`${BASE}/convert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  }).then(async (resp) => {
    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) { onDone(); break; }
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try { onEvent(JSON.parse(line.slice(6))); } catch {}
        }
      }
    }
  }).catch((e) => onError(e.message));
}

export async function reviseScript(
  params: Partial<ConvertParams> & { chapter_text: string; existing_yaml: string; feedback: string }
) {
  const r = await fetch(`${BASE}/revise`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}
