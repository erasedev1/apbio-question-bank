'use strict';

const BANK = window.BANK;
const $ = (id) => document.getElementById(id);
const key = (ch, sec) => ch + '|' + (sec === null ? 'review' : sec);

/* questions bucketed by chapter|section so counting a selection is a lookup */
const buckets = new Map();
for (const q of BANK.questions) {
  const k = key(q.c, q.s);
  if (!buckets.has(k)) buckets.set(k, []);
  buckets.get(k).push(q);
}

const selected = new Set();   // of chapter|section keys

/* ---------------- setup screen ---------------- */

function buildChapters() {
  const ol = $('chapters');
  const frag = document.createDocumentFragment();

  for (const ch of BANK.chapters) {
    const total = ch.secs.reduce((n, s) => n + s.n, 0);
    const li = document.createElement('li');
    li.dataset.search = (ch.n + ' ' + ch.t).toLowerCase();

    const row = document.createElement('div');
    row.className = 'row';
    row.innerHTML =
      '<label><input type="checkbox" data-ch="' + ch.n + '">' +
      '<span class="no">' + ch.n + '</span>' +
      '<span class="ti"></span>' +
      '<span class="ct">' + total + '</span></label>' +
      '<button type="button" class="tg" aria-expanded="false">topics</button>';
    row.querySelector('.ti').textContent = ch.t;

    const ul = document.createElement('ul');
    ul.className = 'topics';
    ul.hidden = true;
    for (const s of ch.secs) {
      const k = key(ch.n, s.s === 'review' ? null : s.s);
      const label = document.createElement('label');
      label.innerHTML = '<input type="checkbox" data-key="' + k + '">' +
        '<span>' + (s.s === 'review' ? 'review' : s.s) + '</span>' +
        '<span class="ct">' + s.n + '</span>';
      ul.appendChild(document.createElement('li')).appendChild(label);
    }

    row.querySelector('.tg').addEventListener('click', (e) => {
      ul.hidden = !ul.hidden;
      e.currentTarget.setAttribute('aria-expanded', String(!ul.hidden));
    });

    li.append(row, ul);
    frag.appendChild(li);
  }
  ol.appendChild(frag);

  ol.addEventListener('change', (e) => {
    const cb = e.target;
    if (cb.dataset.ch) {
      const li = cb.closest('li');
      li.querySelectorAll('[data-key]').forEach((t) => {
        t.checked = cb.checked;
        cb.checked ? selected.add(t.dataset.key) : selected.delete(t.dataset.key);
      });
    } else if (cb.dataset.key) {
      cb.checked ? selected.add(cb.dataset.key) : selected.delete(cb.dataset.key);
      syncChapterBox(cb.closest('.chapters > li'));
    }
    refresh();
  });
}

function syncChapterBox(li) {
  const topics = [...li.querySelectorAll('[data-key]')];
  const on = topics.filter((t) => t.checked).length;
  const box = li.querySelector('[data-ch]');
  box.checked = on === topics.length;
  box.indeterminate = on > 0 && on < topics.length;
}

function available() {
  let n = 0;
  for (const k of selected) n += buckets.get(k).length;
  return n;
}

function refresh() {
  const n = available();
  $('availnum').textContent = n;
  const count = $('count');
  count.max = Math.max(1, n);
  if (n && +count.value > n) count.value = n;
  if (n && (!+count.value || +count.value < 1)) count.value = Math.min(20, n);
  $('go').disabled = n === 0;
}

function setAll(on) {
  document.querySelectorAll('#chapters input[type=checkbox]').forEach((cb) => {
    cb.checked = on;
    cb.indeterminate = false;
    if (cb.dataset.key) on ? selected.add(cb.dataset.key) : selected.delete(cb.dataset.key);
  });
  refresh();
}

$('all').addEventListener('click', () => setAll(true));
$('none').addEventListener('click', () => setAll(false));
$('count').addEventListener('input', refresh);
$('filter').addEventListener('input', (e) => {
  const term = e.target.value.trim().toLowerCase();
  document.querySelectorAll('#chapters > li').forEach((li) => {
    li.hidden = term !== '' && !li.dataset.search.includes(term);
  });
});

/* ---------------- run ---------------- */

let run = null;

function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function show(view) {
  for (const v of ['setup', 'test', 'results']) $(v).hidden = v !== view;
  window.scrollTo(0, 0);
}

$('go').addEventListener('click', () => {
  const pool = [];
  for (const k of selected) pool.push(...buckets.get(k));
  const n = Math.min(Math.max(1, +$('count').value || 1), pool.length);
  run = {
    qs: shuffle(pool.slice()).slice(0, n),
    at: 0,
    answers: new Array(n).fill(null),
    exam: document.querySelector('input[name=mode]:checked').value === 'exam',
  };
  show('test');
  render();
});

function img([file, w, h], cls) {
  const el = document.createElement('img');
  el.src = 'images/' + file;
  el.width = w; el.height = h;
  el.loading = 'lazy';
  el.alt = cls === 'choice' ? 'Answer choice' : 'Question figure';
  return el;
}

function render() {
  const q = run.qs[run.at];
  const picked = run.answers[run.at];

  $('pbar').style.width = ((run.at) / run.qs.length * 100) + '%';
  $('pos').textContent = 'Question ' + (run.at + 1) + ' of ' + run.qs.length;
  $('tag').textContent = 'Chapter ' + q.c + (q.s ? ' · Section ' + q.s : ' · Chapter review');

  const figs = $('figs');
  figs.replaceChildren();
  for (const f of (q.f || q.g || [])) figs.appendChild(img(f));

  $('stem').textContent = q.q;

  const box = $('choices');
  box.replaceChildren();
  for (const k of Object.keys(q.o)) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'choice';
    b.dataset.k = k;

    const kk = document.createElement('span');
    kk.className = 'k';
    kk.textContent = k;
    const v = document.createElement('span');
    v.className = 'v';
    if (q.m && q.m[k]) v.appendChild(img(q.m[k], 'choice'));
    else v.textContent = q.o[k];
    b.append(kk, v);

    if (picked) applyMark(b, k, picked, q.a);
    b.addEventListener('click', () => choose(k));
    box.appendChild(b);
  }

  const answered = picked !== null;
  $('next').disabled = !answered;
  $('next').textContent = run.at === run.qs.length - 1 ? 'Finish' : 'Next';
  showVerdict(picked, q.a);
}

/* practice mode paints right/wrong; exam mode only marks the selection */
function applyMark(btn, k, picked, correct) {
  if (run.exam) { if (k === picked) btn.classList.add('sel'); return; }
  btn.disabled = true;
  if (k === correct) btn.classList.add('ok');
  else if (k === picked) btn.classList.add('bad');
}

function showVerdict(picked, correct) {
  const el = $('verdict');
  if (!picked || run.exam) { el.textContent = ''; el.className = 'verdict'; return; }
  const right = picked === correct;
  el.textContent = right ? 'Correct' : 'Incorrect — answer is ' + correct;
  el.className = 'verdict ' + (right ? 'ok' : 'bad');
}

function choose(k) {
  // in practice mode the first answer stands; in exam mode you may change it
  if (!run.exam && run.answers[run.at] !== null) return;
  run.answers[run.at] = k;
  render();
}

$('next').addEventListener('click', () => {
  if (run.at === run.qs.length - 1) return finish();
  run.at++;
  render();
  window.scrollTo(0, 0);
});

$('quit').addEventListener('click', () => {
  if (run.answers.some((a) => a !== null)) finish();
  else show('setup');
});

document.addEventListener('keydown', (e) => {
  if ($('test').hidden || e.metaKey || e.ctrlKey || e.altKey) return;
  const q = run.qs[run.at];
  const keys = Object.keys(q.o);
  const up = e.key.toUpperCase();
  if (keys.includes(up)) { choose(up); e.preventDefault(); return; }
  const n = parseInt(e.key, 10);
  if (n >= 1 && n <= keys.length) { choose(keys[n - 1]); e.preventDefault(); return; }
  if ((e.key === 'Enter' || e.key === 'ArrowRight') && !$('next').disabled) {
    $('next').click(); e.preventDefault();
  }
});

/* ---------------- results ---------------- */

function finish() {
  const done = run.answers.filter((a) => a !== null).length;
  const right = run.qs.filter((q, i) => run.answers[i] === q.a).length;
  const pct = done ? Math.round(right / done * 100) : 0;

  $('score').textContent = right + ' / ' + done + '  (' + pct + '%)';
  $('scoresub').textContent = (run.exam ? 'Exam' : 'Practice') + ' · ' +
    (done < run.qs.length ? done + ' of ' + run.qs.length + ' answered' : run.qs.length + ' questions');

  const ol = $('review');
  ol.replaceChildren();
  run.qs.forEach((q, i) => {
    const picked = run.answers[i];
    if (picked === null) return;
    const ok = picked === q.a;
    const li = document.createElement('li');
    li.className = ok ? 'ok' : 'bad';

    const p = document.createElement('p');
    p.className = 'rq';
    p.textContent = q.q;

    const a = document.createElement('p');
    a.className = 'ra';
    const yours = document.createElement('span');
    yours.innerHTML = '<b>You</b> ';
    const ys = document.createElement('span');
    ys.className = 'y' + (ok ? '' : ' bad');
    ys.textContent = picked + (q.m ? '' : '. ' + q.o[picked]);
    yours.appendChild(ys);
    a.appendChild(yours);

    if (!ok) {
      const corr = document.createElement('span');
      corr.innerHTML = '<b>Answer</b> ';
      const cs = document.createElement('span');
      cs.className = 'c';
      cs.textContent = q.a + (q.m ? '' : '. ' + q.o[q.a]);
      corr.appendChild(cs);
      a.appendChild(corr);
    }

    const meta = document.createElement('p');
    meta.className = 'rm';
    meta.textContent = 'Chapter ' + q.c + (q.s ? ' · Section ' + q.s : ' · Chapter review') +
      ' · ' + q.b + ' · PDF p.' + q.p;

    li.append(p, a, meta);
    ol.appendChild(li);
  });

  show('results');
}

$('again').addEventListener('click', () => { run = null; show('setup'); });

/* ---------------- boot ---------------- */

$('bankline').textContent =
  BANK.questions.length.toLocaleString() + ' questions · ' + BANK.chapters.length +
  ' chapters · Campbell Biology 11e';
buildChapters();
refresh();
