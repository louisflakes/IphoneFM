const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1500, height: 1100 } });
const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
await p.goto('file://' + process.argv[2]);
await p.waitForTimeout(800);
await p.locator('.sheet').screenshot({ path: process.argv[3] });
console.log('errors:', JSON.stringify(errs));
await b.close();
})();
