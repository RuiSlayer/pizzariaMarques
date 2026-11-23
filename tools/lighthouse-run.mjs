// Lighthouse matrix for the site. Usage:
//   BASE=http://127.0.0.1:8000 OUT=./lighthouse-reports CHROME=/usr/bin/chromium \
//   LH_USER=... LH_PASS=... node tools/lighthouse-run.mjs [quick]
// Runs navigation audits (mobile + desktop, simulated and DevTools throttling) on every public page,
// logged-in navigations (checkout, profile), timespan flows (carousel, mobile nav, map, add to cart)
// and snapshots. Writes one JSON + HTML per run and a summary.json.
import { mkdirSync, writeFileSync } from 'node:fs'
import puppeteer from 'puppeteer-core'
import lighthouse, { startFlow, desktopConfig } from 'lighthouse'

const BASE = process.env.BASE || 'http://127.0.0.1:8000'
const OUT = process.env.OUT || 'lighthouse-reports'
const CHROME = process.env.CHROME || '/usr/bin/chromium'
const QUICK = process.argv.includes('quick')
mkdirSync(OUT, { recursive: true })

const PAGES = ['/', '/menu', '/sobrenos', '/contactos', '/login', '/registo']
const resumo = []

function guardar(nome, lhr, html) {
  writeFileSync(`${OUT}/${nome}.json`, JSON.stringify(lhr))
  if (html) writeFileSync(`${OUT}/${nome}.html`, html)
  const cat = Object.fromEntries(Object.entries(lhr.categories).map(([k, v]) => [k, v.score == null ? null : Math.round(v.score * 100)]))
  const a = lhr.audits
  const m = (id) => a[id]?.displayValue ?? null
  const falhas = Object.values(a)
    .filter((x) => x.score !== null && x.score < 0.9 && ['binary', 'numeric', 'metricSavings'].includes(x.scoreDisplayMode))
    .map((x) => `${x.id}${x.displayValue ? ` (${x.displayValue})` : ''}`)
  const linha = { nome, gatherMode: lhr.gatherMode, ...cat, FCP: m('first-contentful-paint'), LCP: m('largest-contentful-paint'), TBT: m('total-blocking-time'), CLS: m('cumulative-layout-shift'), SI: m('speed-index'), INP: m('interaction-to-next-paint'), bytes: m('total-byte-weight'), falhas }
  resumo.push(linha)
  console.log(JSON.stringify(linha))
}

async function navegar(browser, url, nome, settings) {
  const page = await browser.newPage()
  const r = await lighthouse(url, { output: 'html', logLevel: 'error' }, settings, page)
  guardar(nome, r.lhr, r.report)
  await page.close()
}

async function login(page) {
  await page.goto(`${BASE}/login`)
  await page.type('#username', process.env.LH_USER)
  await page.type('#password', process.env.LH_PASS)
  await Promise.all([page.waitForNavigation(), page.click('button[type=submit]')])
}

const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox'] })

const devtools = (cfg) => ({ ...(cfg || { extends: 'lighthouse:default' }), settings: { ...((cfg && cfg.settings) || {}), throttlingMethod: 'devtools' } })

// 1. Navigation: every page, mobile + desktop (simulated throttling = Lighthouse default)
for (const p of PAGES) {
  const slug = p === '/' ? 'home' : p.slice(1)
  await navegar(browser, BASE + p, `nav-mobile-${slug}`, undefined)
  await navegar(browser, BASE + p, `nav-desktop-${slug}`, desktopConfig)
  if (QUICK) continue
  // DevTools (applied) throttling, as in the original reports
  await navegar(browser, BASE + p, `nav-desktop-devtools-${slug}`, devtools(desktopConfig))
}
if (!QUICK) await navegar(browser, `${BASE}/`, 'nav-mobile-devtools-home', devtools())

// 1b. Other devices / networks
const tablet = {
  extends: 'lighthouse:default',
  settings: {
    formFactor: 'mobile',
    screenEmulation: { mobile: true, width: 768, height: 1024, deviceScaleFactor: 2, disabled: false },
  },
}
const lento = {
  extends: 'lighthouse:default',
  settings: {
    // low-end phone on a poor 3G connection
    throttling: { rttMs: 300, throughputKbps: 400, cpuSlowdownMultiplier: 6, requestLatencyMs: 300 * 3.75, downloadThroughputKbps: 400 * 0.9, uploadThroughputKbps: 400 * 0.9 },
  },
}
if (!QUICK) {
  for (const p of ['/', '/menu', '/sobrenos']) {
    const slug = p === '/' ? 'home' : p.slice(1)
    await navegar(browser, BASE + p, `nav-tablet-${slug}`, tablet)
    await navegar(browser, BASE + p, `nav-3g-lento-${slug}`, lento)
  }
}

// 2. Logged-in pages + flows (same browser context keeps the session cookie)
const page = await browser.newPage()
await login(page)
for (const p of ['/menu/checkout', `/sobrenos`]) {
  const slug = p.replaceAll('/', '-').replace(/^-/, '')
  const r = await lighthouse(BASE + p, { output: 'html', logLevel: 'error', disableStorageReset: true }, desktopConfig, page)
  guardar(`nav-desktop-auth-${slug}`, r.lhr, r.report)
}

// 3. Timespan + snapshot flows
{
  // Home on mobile: open the nav, step the carousel, open the interactive map
  const flow = await startFlow(page, { name: 'Home (mobile)', flags: { disableStorageReset: true } })
  await flow.navigate(`${BASE}/`)
  await flow.startTimespan({ name: 'nav + carrossel + mapa' })
  await page.click('.navbar-toggler')
  await new Promise((r) => setTimeout(r, 600))
  await page.click('.carousel-control-next')
  await new Promise((r) => setTimeout(r, 900))
  await page.evaluate(() => document.querySelector('[data-mapa-abrir]').scrollIntoView())
  await page.click('[data-mapa-abrir]')
  await new Promise((r) => setTimeout(r, 1500))
  await flow.endTimespan()
  await flow.snapshot({ name: 'menu aberto + mapa interativo' })
  const res = await flow.createFlowResult()
  res.steps.forEach((s, i) => guardar(`flow-home-mobile-${i}-${s.lhr.gatherMode}`, s.lhr))
  writeFileSync(`${OUT}/flow-home-mobile.html`, await flow.generateReport())
}
{
  // Menu on desktop: scroll the whole menu, add a pizza to the cart (form POST + redirect)
  const flow = await startFlow(page, { name: 'Menu (desktop)', config: desktopConfig, flags: { disableStorageReset: true } })
  await flow.navigate(`${BASE}/menu`)
  await flow.startTimespan({ name: 'scroll + adicionar ao carrinho' })
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 80)) }
  })
  await page.evaluate(() => window.scrollTo(0, 0))
  await Promise.all([page.waitForNavigation(), page.click('.lista-pizzas .form-pedido button')])
  await flow.endTimespan()
  await flow.snapshot({ name: 'menu com mensagem' })
  await flow.navigate(`${BASE}/menu/checkout`, { name: 'checkout (cache quente)' })
  const res = await flow.createFlowResult()
  res.steps.forEach((s, i) => guardar(`flow-menu-desktop-${i}-${s.lhr.gatherMode}`, s.lhr))
  writeFileSync(`${OUT}/flow-menu-desktop.html`, await flow.generateReport())
}

await browser.close()
writeFileSync(`${OUT}/summary.json`, JSON.stringify(resumo, null, 1))
