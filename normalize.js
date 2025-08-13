// normalize.js

// --- helpers to decode weird pastes ---
function decodeHtmlEntities(s) {
  if (!/[&][#\w]+;/.test(s)) return s;
  const ta = document.createElement('textarea');
  ta.innerHTML = s;
  return ta.value;
}

function decodeUnicodeEscapes(s) {
  // turns \u0B28\u0B2C\u0B2E\u0B40 into real Odia chars
  if (!/\\u[0-9a-fA-F]{4}/.test(s)) return s;
  try {
    // escape embedded quotes, then JSON-parse
    return JSON.parse('"' + s.replace(/"/g, '\\"') + '"');
  } catch {
    return s;
  }
}

// --- base normalizer: keep characters, remove junk, NFC ---
export function normalizeInput(input) {
  let s = String(input ?? '');

  // decode entities and \uXXXX
  s = decodeHtmlEntities(s);
  s = decodeUnicodeEscapes(s);

  // strip zero-widths / word joiners / BOM
  s = s.replace(/[\u200B\u200C\u200D\u2060\uFEFF]/g, '');

  // trim outer whitespace
  s = s.trim();

  // normalize to NFC for stable codepoints
  if (s.normalize) s = s.normalize('NFC');

  return s;
}

// Detect if string contains Odia script chars (U+0B00–U+0B7F)
export function isOdiaWord(s) {
  s = normalizeInput(s);
  return /[\u0B00-\u0B7F]/.test(s);
}

// Exact-ish key: collapse ANY Unicode spaces to a single ASCII space
// Useful for matching multi-word entries where spacing may vary (one vs many spaces)
export function normalizeExact(s) {
  s = normalizeInput(s);
  // \p{Z} = all Unicode separators; needs /u
  return s.replace(/\p{Z}+/gu, ' ').trim().normalize('NFC');
}

// Space-agnostic key: remove ALL Unicode spaces for tolerant lookups
// This lets "ହେରିଆମାରିବା" match JSON word "ହେରିଆ ମାରିବା"
export function normalizeCompact(s) {
  s = normalizeInput(s);
  return s.replace(/\p{Z}+/gu, '').normalize('NFC');
}

/*
Usage example in your app:

// Build two indexes
const indexExact = new Map();
const indexCompact = new Map();

for (const e of dict) {
  if (!e.word) continue;
  const k1 = normalizeExact(e.word);
  const k2 = normalizeCompact(e.word);
  if (!indexExact.has(k1)) indexExact.set(k1, []);
  indexExact.get(k1).push(e);
  if (!indexCompact.has(k2)) indexCompact.set(k2, []);
  indexCompact.get(k2).push(e);
}

// On search:
const qRaw = input.value;
const k1 = normalizeExact(qRaw);
let entries = indexExact.get(k1);
if (!entries || entries.length === 0) {
  const k2 = normalizeCompact(qRaw);
  entries = indexCompact.get(k2) || [];
}
*/

