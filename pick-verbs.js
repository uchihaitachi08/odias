// pick-verbs.js
import { normalizeCompact } from './normalize.js';

const statusEl = document.getElementById('vg-status');
const cardsEl  = document.getElementById('vg-cards');
const nextBtn  = document.getElementById('vg-next');
const scoreEl  = document.getElementById('vg-score');

let DICT = [];
let VERB_SET = new Set();
let VERB_POOL = [];     // indices of dict entries that are verbs
let NONVERB_POOL = [];  // indices of dict entries that are not verbs

let rounds = 0, correctClicks = 0, totalVerbTargets = 0;
let current = null; // { items:[{idx,isVerb,el}], targetCount, decidedCount, foundCount }
const seen = new Set();

const randInt = (n) => Math.floor(Math.random() * n);
const shuffle = (a) => { for (let i=a.length-1;i>0;i--){ const j=randInt(i+1); [a[i],a[j]]=[a[j],a[i]]; } };
const sampleDistinct = (arr, k) => {
  if (k >= arr.length) return arr.slice(0, k);
  const result = [];
  const used = new Set();
  while (result.length < k && used.size < arr.length) {
    const i = randInt(arr.length);
    if (!used.has(i)) { used.add(i); result.push(arr[i]); }
  }
  return result;
};

function extractWord(v){ return typeof v === 'string' ? v : (v && v.word) ? v.word : ''; }
function key(w){ return normalizeCompact(String(w || '')); }

async function loadData() {
  // IMPORTANT: serve over HTTP (e.g. python -m http.server) — file:// will block fetch.
  const [dict, verbsRaw] = await Promise.all([
    fetch('./dictionary.json').then(r => r.json()),
    fetch('./verbs.json').then(r => r.json())
  ]);

  DICT = Array.isArray(dict) ? dict : [];

  VERB_SET = new Set();
  for (const v of (verbsRaw || [])) {
    const w = extractWord(v);
    if (w) VERB_SET.add(key(w));
  }

  VERB_POOL.length = 0;
  NONVERB_POOL.length = 0;
  DICT.forEach((e, i) => {
    const k = key(e.word);
    if (!k) return;
    if (VERB_SET.has(k)) VERB_POOL.push(i);
    else NONVERB_POOL.push(i);
  });

  if (!VERB_POOL.length) {
    throw new Error('No verbs found. Check verbs.json path/format and normalization.');
  }
}

function newRound() {
  nextBtn.style.display = 'none';
  cardsEl.innerHTML = '';
  current = null;

  // choose 1–3 verb targets (cap by availability)
  let targetCount = Math.min(1 + randInt(3), 3, VERB_POOL.length);

  // prefer unseen
  const verbCands = VERB_POOL.filter(i => !seen.has(key(DICT[i].word)));
  const nonCands  = NONVERB_POOL.filter(i => !seen.has(key(DICT[i].word)));

  const vPool = verbCands.length >= targetCount ? verbCands : VERB_POOL;
  const nPool = nonCands.length >= (4 - targetCount) ? nonCands : NONVERB_POOL;

  const verbIdxs = sampleDistinct(vPool, targetCount);
  const nonIdxs  = sampleDistinct(nPool, 4 - targetCount);

  const items = [
    ...verbIdxs.map(i => ({ idx: i, isVerb: true })),
    ...nonIdxs.map(i => ({ idx: i, isVerb: false }))
  ];
  shuffle(items);

  for (const it of items) seen.add(key(DICT[it.idx].word));
  if (seen.size > 200) seen.clear();

  current = { items, targetCount, decidedCount: 0, foundCount: 0 };
  totalVerbTargets += targetCount;
  rounds += 1;

  statusEl.textContent = `Find the verbs (${targetCount} this round)`;
  renderRound(items);
}

function renderRound(items) {
  const frag = document.createDocumentFragment();
  items.forEach(it => {
    const e = DICT[it.idx];
    const btn = document.createElement('button');
    btn.style.cssText = `
      border:1px solid var(--border);border-radius:12px;padding:14px;cursor:pointer;
      text-align:left;background:#fff;min-height:72px;font-size:16px;
    `;
    btn.innerHTML = `<div style="font-size:1.4rem;font-weight:700">${e.word || ''}</div>
                     ${e.transliteration ? `<div style="color:#777;margin-top:.15rem">${e.transliteration}</div>` : ''}`;
    btn.addEventListener('click', () => handleClick(btn, it));
    frag.appendChild(btn);
    it.el = btn;
  });
  cardsEl.appendChild(frag);
}

function handleClick(btn, item) {
  if (btn.dataset.locked === '1') return;

  if (item.isVerb) {
    // green
    btn.style.background = '#e9f8ee';
    btn.style.borderColor = '#2db46b';
    btn.style.boxShadow = 'inset 0 0 0 1px #2db46b';
    correctClicks += 1;
    current.foundCount += 1;
  } else {
    // red
    btn.style.background = '#fdecec';
    btn.style.borderColor = '#d23b3b';
    btn.style.boxShadow = 'inset 0 0 0 1px #d23b3b';
  }
  btn.dataset.locked = '1';
  current.decidedCount += 1;

  if (current.foundCount === current.targetCount || current.decidedCount === 4) {
    revealRemainder();
    endRound();
  }
}

function revealRemainder() {
  for (const it of current.items) {
    const el = it.el;
    if (el.dataset.locked === '1') continue;
    if (it.isVerb) {
      el.style.background = '#f3fff7';
      el.style.borderColor = '#69c892';
      el.style.boxShadow = 'inset 0 0 0 1px #69c892';
    } else {
      el.style.opacity = '0.7';
    }
    el.dataset.locked = '1';
  }
}

function endRound() {
  nextBtn.style.display = 'inline-block';
  scoreEl.textContent = `Score: ${correctClicks} correct picks in ${rounds} rounds (targets so far: ${totalVerbTargets}).`;
}

nextBtn?.addEventListener('click', newRound);

// boot
(async () => {
  try {
    await loadData();
    statusEl.textContent = 'Loaded. Click the verbs!';
    newRound();
  } catch (e) {
    console.error(e);
    statusEl.textContent = e.message || 'Failed to load data.';
  }
})();

