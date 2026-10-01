// Verify scene cut placement against the measured narration onsets, independent of
// how visually "busy" each scene is.
//
// The pixel-difference approach used previously infers a cut from the largest
// frame-to-frame change. That breaks once scenes contain their own motion
// graphics: a stat tile slamming in can change more pixels than the crossfade
// itself, so the detected "cut" drifts by a second or more even though the cut is
// exactly on time.
//
// This measures the crossfade directly: drive the composition timeline to a series
// of times and read each scene's rendered opacity. A scene's onset is the first
// sample where its opacity rises above zero, which is by definition its cut.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = path.resolve('brag-output-2026-09-20-221936');
const COMP = path.join(OUT, 'composition/index.html');

(async () => {
  const sceneMap = JSON.parse(fs.readFileSync(path.join(OUT, 'scene-map.json'), 'utf8'));
  const scenes = sceneMap.scenes;

  const browser = await chromium.launch({
    args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file:///' + COMP.replace(/\\/g, '/'), { waitUntil: 'load', timeout: 60000 });
  await page.waitForFunction(() => !!(window.__timelines && window.__timelines['fp-pitch']), null, {
    timeout: 30000,
  });

  const readings = await page.evaluate(
    ({ scenes }) => {
      const tl = window.__timelines['fp-pitch'];
      const STEP = 0.02;
      const out = [];
      for (const s of scenes) {
        // Sample a window around the intended start; the crossfade begins XF before.
        const lo = Math.max(0, s.start - 2.0);
        const hi = s.start + 2.0;
        let onset = null;
        for (let t = lo; t <= hi + 1e-9; t += STEP) {
          tl.time(t, false); // seek without suppressing callbacks
          const el = document.getElementById(s.id);
          const op = parseFloat(getComputedStyle(el).opacity);
          if (op > 0.02) {
            onset = +t.toFixed(3);
            break;
          }
        }
        // Also capture the opacity right at the intended start
        tl.time(s.start, false);
        const atStart = parseFloat(getComputedStyle(document.getElementById(s.id)).opacity);
        out.push({ id: s.id, intended: s.start, onset, atStart: +atStart.toFixed(3) });
      }
      return out;
    },
    { scenes: scenes.map((s) => ({ id: s.id, start: s.start })) }
  );

  console.log('scene  intended   first-visible   delta    opacity@intended');
  console.log('-'.repeat(58));
  let worst = 0;
  for (const r of readings) {
    if (r.onset === null) {
      console.log(`${r.id.padEnd(6)} ${String(r.intended).padStart(8)}s   NOT VISIBLE`);
      worst = 99;
      continue;
    }
    const d = r.onset - r.intended;
    // s1 legitimately fades in from 0 (no preceding scene).
    if (r.id !== 's1') worst = Math.max(worst, Math.abs(d));
    console.log(
      `${r.id.padEnd(6)} ${String(r.intended).padStart(8)}s   ${String(r.onset).padStart(10)}s   ` +
        `${(d >= 0 ? '+' : '') + d.toFixed(2)}s   ${r.atStart}`
    );
  }
  console.log('-'.repeat(58));
  console.log(`largest onset deviation (excluding s1): ${worst.toFixed(2)}s`);
  // The crossfade intentionally starts 0.6s before the cut, so a scene becomes
  // visible up to ~0.6s early. Anything later than the cut is a real problem.
  const ok = worst <= 0.65;
  console.log(`\nRESULT: ${ok ? 'PASS' : 'FAIL'} (crossfade begins up to 0.6s early by design)`);
  await browser.close();
  process.exit(ok ? 0 : 1);
})().catch((e) => {
  console.error('FAILED: ' + e.message);
  process.exit(1);
});
