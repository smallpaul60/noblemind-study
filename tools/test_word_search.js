/*
 * Rail for the exhaustive Scripture word search in Noble_Mind_Study_Tool_v2.html.
 *
 * Run:  node tools/test_word_search.js
 *
 * It extracts the SHIPPED functions straight out of the HTML and runs them
 * against the real Bible JSON in the repo, so it cannot drift out of sync with
 * the code it is testing. No network — everything it touches is on disk.
 *
 * What it protects, and why each one matters:
 *   - the search is exhaustive and says so, with a true occurrence count
 *   - the 16 textually-disputed verses are FINDABLE, badged, and attributed to
 *     the KJV rather than passed off as the chosen translation's own text
 *   - a zero result says "this word is absent", never "Scripture is silent"
 *   - Strong's numbers are testament-scoped (G = NT, H = OT) and their tags
 *     never leak into the displayed text
 *   - the vocabulary bridge still renders on a two-verse result set, which is
 *     when a student most needs another way in
 */

const fs = require('fs');
const path = require('path');

const REPO = path.dirname(__dirname);
const HTML = path.join(REPO, 'Noble_Mind_Study_Tool_v2.html');

// ---- extract the shipped code ----------------------------------------------
const src = fs.readFileSync(HTML, 'utf8');
function grab(re, what) {
  const m = src.match(re);
  if (!m) {
    console.error(`FATAL: could not find ${what} in ${path.basename(HTML)}.`);
    console.error('The code moved or was renamed — update this test rather than deleting it.');
    process.exit(2);
  }
  return m[0];
}
const code = [
  grab(/const THOUGHT_BOOK_NAMES = \[null,[\s\S]*?\];/, 'THOUGHT_BOOK_NAMES'),
  grab(/function escapeHtml\(s\) \{[\s\S]*?\n\}/, 'escapeHtml'),
  grab(/\/\/ --- Vocabulary bridge[\s\S]*?\nfunction clearWordSearch\(\) \{[\s\S]*?\n\}/, 'the word-search section'),
].join('\n');

// ---- minimal DOM / fetch stubs ---------------------------------------------
const els = {
  wordSearchInput: { value: '', scrollIntoView() {} },
  wordSearchTranslation: { value: 'BSB' },
  wordSearchWhole: { checked: true },
  wordSearchResults: { innerHTML: '' },
};
global.document = { getElementById: (id) => els[id] };
global.fetch = async (p) => {
  const f = path.join(REPO, p.replace(/^\//, ''));
  if (!fs.existsSync(f)) return { ok: false, status: 404 };
  return { ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(f, 'utf8')) };
};
eval(code);

// ---- tiny assert harness ----------------------------------------------------
const strip = (h) => h.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
let pass = 0, fail = 0;
function check(name, cond, detail) {
  if (cond) { pass++; console.log('  PASS  ' + name); }
  else { fail++; console.log('  FAIL  ' + name + (detail ? '\n          ' + detail : '')); }
}
const search = async (translation, query, whole = true) => {
  els.wordSearchTranslation.value = translation;
  els.wordSearchInput.value = query;
  els.wordSearchWhole.checked = whole;
  await performWordSearch();
  return els.wordSearchResults.innerHTML;
};

(async () => {
  console.log('\n=== exhaustive word search ===');
  let out = await search('ASV', 'assembling');
  check('ASV "assembling" finds Hebrews 10:25', out.includes('Hebrews 10:25'), strip(out).slice(0, 150));
  check('reports a true occurrence + verse total', /\d+ occurrences? in \d+ verses?/.test(strip(out)), strip(out).slice(0, 120));
  check('states the result is exhaustive', out.includes('This is every one'));

  out = await search('BSB', 'meeting together');
  check('BSB renders Heb 10:25 as "meeting together"', out.includes('Hebrews 10:25'));
  out = await search('BSB', 'assembling');
  check('BSB honestly reports "assembling" absent', out.includes('does not occur'));
  check('absence is reported as absent, not as silence',
        out.includes('not that Scripture is silent'));

  console.log('\n=== the 16 disputed verses ===');
  for (const t of ['BSB', 'ASV']) {
    out = await search(t, 'believest with all thine heart');
    check(`${t}: Acts 8:37 is findable`, out.includes('Acts 8:37'), strip(out).slice(0, 160));
    check(`${t}: Acts 8:37 badged "textually disputed"`, out.includes('textually disputed'));
    check(`${t}: Acts 8:37 attributed to the KJV`, out.includes('(KJV)'));
    check(`${t}: the caveat explains why it is bracketed`,
          out.includes('judged it a later addition'));
  }

  console.log('\n=== whole-word toggle ===');
  const wholeN = ((await search('ASV', 'sin', true)).match(/search-result-item/g) || []).length;
  const partN  = ((await search('ASV', 'sin', false)).match(/search-result-item/g) || []).length;
  check('both modes return results', wholeN > 0 && partN > 0, `whole=${wholeN} substring=${partN}`);

  console.log("\n=== Strong's number search (KJV) ===");
  out = await search('KJV', 'G907');
  check('G907 (baptizo) finds Acts 2:38', out.includes('Acts 2:38'), strip(out).slice(0, 160));
  check('G907 is scoped to the New Testament', !/(Genesis|Exodus|Psalms) \d+:/.test(out));
  check("Strong's tags never reach the display", !out.includes('<S>'));
  out = await search('KJV', 'H430');
  check('H430 (Elohim) finds Genesis 1:1', out.includes('Genesis 1:1'));
  check('H430 is scoped to the Old Testament', !/(Matthew|Acts|Romans) \d+:/.test(out));

  console.log('\n=== vocabulary bridge ===');
  const bridge = buildVocabularyBridge([
    { book: 58, chapter: 10, verse: 25, text: 'not forsaking the assembling of ourselves together, as the manner of some is' },
    { book: 44, chapter: 20, verse: 7,  text: 'And upon the first day of the week, when the disciples came together to break bread' },
    { book: 46, chapter: 16, verse: 2,  text: 'Upon the first day of the week let every one of you lay by him in store' },
  ]);
  check('offers clickable words drawn from the verses', bridge.includes('runWordSearchFor'), strip(bridge).slice(0, 180));
  check('drops grammatical stopwords', !/>the<|>and<|>of</.test(bridge));
  const tiny = buildVocabularyBridge([
    { book: 19, chapter: 56, verse: 3, text: 'When I am afraid, I will put my trust in You.' },
    { book: 20, chapter: 3,  verse: 5, text: 'Trust in the LORD with all your heart and do not lean on your own understanding.' },
  ]);
  check('still renders on a two-verse result set', tiny.includes('runWordSearchFor'), strip(tiny).slice(0, 200));

  console.log(`\n${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
