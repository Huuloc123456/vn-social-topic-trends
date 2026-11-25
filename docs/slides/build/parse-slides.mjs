// Reads docs/NOI_DUNG_SLIDE.md into the slide spec consumed by build-slides.ps1.
// Usage: node docs/slides/build/parse-slides.mjs > docs/slides/build/slides.json
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const source = fileURLToPath(new URL('../../NOI_DUNG_SLIDE.md', import.meta.url));
const lines = readFileSync(source, 'utf8').replaceAll('\r\n', '\n').split('\n');

// Layout per slide, chosen so neighbouring slides do not repeat the same composition.
const LAYOUT = {
  '01': 'cover', '02': 'agenda', '03': 'text-img', '04': 'text-img', '05': 'table-top', '06': 'img-quad',
  '07': 'table-top', '08': 'img-text', '09': 'text-img', '10': 'img-text', '11': 'img-text', '12': 'text-img',
  '13': 'table-img', '14': 'text-img', '15': 'img-text', '16': 'text-img', '17': 'img-text', '18': 'text-img',
  '19': 'table-img', '20': 'two-img', '21': 'img-text', '22': 'text-img', '23': 'table-top', '24': 'img-text',
  '25': 'text-img', '26': 'img-text', '27': 'text-img', '28': 'end',
};

const slides = [];
let chapter = null, current = null, mode = null;
for (const line of lines) {
  const ch = /^## (Chương (\d)) — (.+)$/.exec(line);
  if (ch) { chapter = { number: Number(ch[2]), title: ch[3].trim() }; slides.push({ kind: 'section', chapter }); current = null; continue; }
  if (/^## /.test(line)) { if (!/^## Mở đầu/.test(line)) { current = null; chapter = null; } continue; }
  const head = /^### Slide (\d\d) — (.+)$/.exec(line);
  if (head) {
    current = { kind: 'slide', id: head[1], title: head[2].trim(), layout: LAYOUT[head[1]], chapter, items: [], ordered: false, table: [], images: [], notes: '' };
    slides.push(current); mode = null; continue;
  }
  if (!current) continue;
  if (line.startsWith('**Nội dung trên slide**')) { mode = 'content'; continue; }
  const hint = /^\*\*Gợi ý trình bày:\*\*\s*(.+)$/.exec(line);
  if (hint) { current.notes = hint[1].trim(); mode = null; continue; }
  if (line.startsWith('**Hình chèn:**')) { mode = null; continue; }
  const img = /^!\[([^\]]*)\]\(([^)]+)\)/.exec(line);
  if (img) { current.images.push({ alt: img[1], path: img[2].replaceAll('/', '\\') }); continue; }
  if (mode !== 'content') continue;
  const bullet = /^- (.+)$/.exec(line), numbered = /^\d+\. (.+)$/.exec(line);
  if (bullet || numbered) { current.items.push((bullet ?? numbered)[1].trim()); current.ordered = Boolean(numbered); continue; }
  if (/^\|/.test(line) && !/^\|\s*-/.test(line)) current.table.push(line.split('|').slice(1, -1).map(c => c.trim()));
}
if (slides.filter(s => s.kind === 'slide').length !== 28) throw new Error('expected 28 slides');
for (const s of slides) if (s.kind === 'slide' && !s.layout) throw new Error(`no layout for slide ${s.id}`);
// Fixed wording lives here (UTF-8), because Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI.
const strings = {
  course: 'INTERNET OF THINGS',
  product: 'KHOGUARD',
  tagline: 'Giám sát kho hàng và an toàn kho lạnh bằng IoT',
  advisor: 'GVHD: ………………………',
  members: 'Nhóm 17 · Đề tài 42 — Thành viên: ………………………',
  chapterLabel: 'Chương',
  thanks: 'CẢM ƠN THẦY CÔ VÀ CÁC BẠN ĐÃ LẮNG NGHE!',
};
process.stdout.write(JSON.stringify({ strings, slides }, null, 1));
