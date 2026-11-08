const { chromium } = require('playwright');
(async () => {
  const [url, out, w, h] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: +w, height: +h } });
  const errs = []; p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); }); p.on('pageerror', e => errs.push(String(e)));
  await p.goto(url);
  await p.waitForFunction(() => window.__done || window.__err, null, { timeout: 120000 });
  console.log(JSON.stringify(await p.evaluate(() => ({ err: window.__err, log: window.__log }))));
  if (errs.length) console.log('CONSOLE', errs.slice(0, 5));
  await p.screenshot({ path: out });
  await b.close();
})();
