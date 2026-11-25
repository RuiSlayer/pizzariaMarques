/*
 * Pizzaria Marquês — the only script the site loads (bundled + minified by tools/build-assets.mjs).
 * Bootstrap: just the three components in use, from source, so the rest is never shipped.
 */
import Alert from 'bootstrap/js/src/alert'
import Carousel from 'bootstrap/js/src/carousel'
import Collapse from 'bootstrap/js/src/collapse'

// Importing registers Bootstrap's data-api handlers (data-bs-toggle, data-bs-ride, data-bs-dismiss).
window.bootstrapComponentes = { Alert, Carousel, Collapse }

/* Map: static image first; the interactive map (third-party iframe) only on request. */
document.addEventListener('click', (evento) => {
  const botao = evento.target.closest('[data-mapa-abrir]')
  if (!botao) return
  const moldura = botao.closest('[data-mapa]').querySelector('[data-mapa-moldura]')
  const iframe = document.createElement('iframe')
  iframe.src = botao.dataset.src
  iframe.title = botao.dataset.titulo   // translated in _mapa.html
  iframe.className = 'mapa-iframe'
  iframe.referrerPolicy = 'no-referrer'
  moldura.replaceChildren(iframe)
  // keep the button in place (no layout shift), just mark it as done
  botao.disabled = true
  botao.lastChild.textContent = ` ${botao.dataset.aberto}`
})

/*
 * Menu: quantity stepper (− [n] +, _quantidade.html). The buttons step the number field and keep
 * focus (aria-disabled at the limits, never disabled, so keyboard focus is not lost); typing or the
 * arrow keys work on the field itself. The new value is announced to screen readers.
 */
function definirQtd(campo, valor, anunciar = true) {
  const min = Number(campo.min) || 1
  const max = Number(campo.max) || 20
  const n = Math.min(max, Math.max(min, Math.round(Number(valor)) || min))
  campo.value = n
  const grupo = campo.closest('.qtd')
  grupo.querySelector('[data-qtd-passo="-1"]').setAttribute('aria-disabled', String(n <= min))
  grupo.querySelector('[data-qtd-passo="1"]').setAttribute('aria-disabled', String(n >= max))
  const leitor = document.querySelector('[data-aviso-leitor]')
  if (anunciar && leitor) leitor.textContent = `${campo.dataset.qtdAnuncio}: ${n}`
}

document.addEventListener('click', (evento) => {
  const botao = evento.target.closest('[data-qtd-passo]')
  if (!botao || botao.getAttribute('aria-disabled') === 'true') return
  const campo = botao.closest('.qtd').querySelector('.qtd-valor')
  definirQtd(campo, Number(campo.value) + Number(botao.dataset.qtdPasso))
})

// Typed values: fix the buttons as you type, clamp to 1-20 when you leave the field.
document.addEventListener('input', (evento) => {
  const campo = evento.target
  if (!campo.classList || !campo.classList.contains('qtd-valor') || campo.value === '') return
  definirQtd(campo, campo.value, false)
})
document.addEventListener('change', (evento) => {
  if (evento.target.classList && evento.target.classList.contains('qtd-valor')) definirQtd(evento.target, evento.target.value, false)
})

/*
 * Menu: add to the cart without reloading the page (forms with data-adicionar).
 * The page keeps its scroll position; the button confirms for 2 s, the header count updates and a
 * notice links to the cart. Any unexpected answer falls back to the normal form submit, so adding
 * never fails silently (and without JS the form works as it is).
 */
const aviso = document.querySelector('[data-aviso]')
const avisoLeitor = document.querySelector('[data-aviso-leitor]')
let avisoTempo

function esconderAviso() {
  if (aviso) aviso.hidden = true
}

function mostrarAviso(texto) {
  if (avisoLeitor) avisoLeitor.textContent = texto          // screen readers (live region)
  if (!aviso) return
  aviso.querySelector('[data-aviso-texto]').textContent = texto
  aviso.hidden = false
  clearTimeout(avisoTempo)
  avisoTempo = setTimeout(esconderAviso, 5000)
}

if (aviso) {
  // Stays while the pointer or focus is on it (time to reach "Ver carrinho").
  aviso.addEventListener('pointerenter', () => clearTimeout(avisoTempo))
  aviso.addEventListener('focusin', () => clearTimeout(avisoTempo))
  aviso.addEventListener('pointerleave', () => { avisoTempo = setTimeout(esconderAviso, 2500) })
  aviso.addEventListener('focusout', () => { avisoTempo = setTimeout(esconderAviso, 2500) })
}

document.addEventListener('submit', async (evento) => {
  const form = evento.target.closest('form[data-adicionar]')
  if (!form || !window.fetch) return
  evento.preventDefault()
  const botao = form.querySelector('[type="submit"]')
  if (botao.getAttribute('aria-busy') === 'true') return   // double tap
  botao.setAttribute('aria-busy', 'true')
  try {
    const resposta = await fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
    })
    const dados = await resposta.json()
    if (dados.redirect) { window.location.href = dados.redirect; return }   // not logged in
    if (!resposta.ok) { mostrarAviso(dados.mensagem); return }

    document.querySelectorAll('[data-carrinho-total]').forEach((contador) => {
      contador.textContent = dados.total
      contador.hidden = !dados.total
      contador.classList.remove('contador-novo')
      void contador.offsetWidth                              // restart the animation
      contador.classList.add('contador-novo')
    })
    mostrarAviso(dados.mensagem)
    definirQtd(form.querySelector('.qtd-valor'), 1, false)
    botao.classList.add('feito')
    clearTimeout(botao.feitoTempo)
    botao.feitoTempo = setTimeout(() => botao.classList.remove('feito'), 2000)
  } catch (erro) {
    form.submit()                                            // network error, HTML answer, ...: do it the plain way
  } finally {
    botao.removeAttribute('aria-busy')
  }
})

/*
 * Cart: − n + and Remover without reloading (forms with data-carrinho, checkout.html).
 * Each button posts the quantity it leads to; the line, subtotal and header count update in place.
 * At 1 and 20 the − / + are aria-disabled (not disabled), so keyboard focus stays on them.
 * Anything unexpected falls back to the plain form submit.
 */
function atualizarLinhaCarrinho(form, dados) {
  const item = form.closest('.item-carrinho')
  const menos = form.querySelector('[data-carrinho-passo="-1"]')
  const mais = form.querySelector('[data-carrinho-passo="1"]')
  const max = Number(form.dataset.max) || 20
  const q = dados.quantidade
  item.querySelector('[data-item-qtd]').textContent = q
  item.querySelector('[data-item-linha]').textContent = dados.linha
  menos.value = q - 1
  mais.value = q + 1
  for (const [botao, limite] of [[menos, q <= 1], [mais, q >= max]]) {
    botao.disabled = false
    botao.setAttribute('aria-disabled', String(limite))
  }
}

function removerLinhaCarrinho(form) {
  const item = form.closest('.item-carrinho')
  const lista = item.parentElement
  // Focus goes to the next line's Remover (or the previous one, or the heading): never lost.
  const vizinho = item.nextElementSibling || item.previousElementSibling
  item.remove()
  const alvo = vizinho ? vizinho.querySelector('.botao-remover') : document.getElementById('titulo-carrinho')
  if (!lista.children.length) {
    lista.remove()
    document.querySelector('[data-carrinho-vazio]').hidden = false
    const finalizar = document.querySelector('[data-finalizar]')
    if (finalizar) finalizar.disabled = true
  }
  if (alvo) alvo.focus()
}

document.addEventListener('submit', async (evento) => {
  const form = evento.target.closest('form[data-carrinho]')
  if (!form || !window.fetch) return
  evento.preventDefault()
  const botao = evento.submitter
  if (!botao || botao.getAttribute('aria-disabled') === 'true' || form.getAttribute('aria-busy') === 'true') return
  form.setAttribute('aria-busy', 'true')
  const corpo = new FormData(form)
  corpo.set('quantidade', botao.value)
  try {
    const resposta = await fetch(form.action, {
      method: 'POST', body: corpo, headers: { Accept: 'application/json' }, credentials: 'same-origin',
    })
    const dados = await resposta.json()
    if (!resposta.ok) throw new Error(dados.mensagem)
    if (dados.quantidade === 0) removerLinhaCarrinho(form)
    else atualizarLinhaCarrinho(form, dados)
    document.querySelectorAll('[data-carrinho-subtotal]').forEach((el) => { el.textContent = dados.subtotal })
    document.querySelectorAll('[data-carrinho-total]').forEach((contador) => {
      contador.textContent = dados.total
      contador.hidden = !dados.total
    })
    const leitor = document.querySelector('[data-aviso-leitor]')
    if (leitor) leitor.textContent = dados.mensagem
  } catch (erro) {
    // Plain submit with the button's value (the server answers with a message and the cart page).
    const campo = document.createElement('input')
    campo.type = 'hidden'
    campo.name = 'quantidade'
    campo.value = botao.value
    form.querySelectorAll('[name="quantidade"]').forEach((b) => b.removeAttribute('name'))
    form.append(campo)
    form.submit()
  } finally {
    form.removeAttribute('aria-busy')
  }
})

/* Checkout: show the detail that belongs to the chosen radio (data-revela="id"). */
document.addEventListener('change', (evento) => {
  const radio = evento.target
  if (radio.type !== 'radio' || !radio.form) return
  radio.form.querySelectorAll(`input[type="radio"][name="${radio.name}"][data-revela]`).forEach((opcao) => {
    const alvo = document.getElementById(opcao.dataset.revela)
    if (alvo) alvo.hidden = !opcao.checked
  })
})

/*
 * Carousel autoplay: starts only once the visitor engages with the page (scroll, pointer, key,
 * touch) and never with prefers-reduced-motion. Slides that change on their own while someone is
 * still reading the first one are an accessibility problem (WCAG 2.2.2), and they also make page-
 * load metrics (Speed Index) measure the slideshow instead of the page. Hover/focus pauses it.
 */
const carrosseis = document.querySelectorAll('.carousel[data-autoplay]')
if (carrosseis.length && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const eventos = ['scroll', 'pointermove', 'keydown', 'touchstart']
  const iniciar = () => {
    eventos.forEach((e) => window.removeEventListener(e, iniciar))
    carrosseis.forEach((el) => {
      const c = Carousel.getOrCreateInstance(el, { interval: 6000, pause: 'hover' })
      c.cycle()
      el.addEventListener('focusin', () => c.pause())
      el.addEventListener('focusout', () => c.cycle())
    })
  }
  eventos.forEach((e) => window.addEventListener(e, iniciar, { once: true, passive: true }))
}

/* Carousel: hidden slides are lazy; warm up the next one so a slide never appears blank. */
function prepararSeguinte(item) {
  const seguinte = item && (item.nextElementSibling || item.parentElement.firstElementChild)
  const img = seguinte && seguinte.querySelector('img[loading="lazy"]')
  if (img) img.loading = 'eager'
}

window.addEventListener('load', () => {
  const idle = window.requestIdleCallback || ((fn) => setTimeout(fn, 1500))
  idle(() => document.querySelectorAll('.carousel .carousel-item.active').forEach(prepararSeguinte))
})

document.addEventListener('slid.bs.carousel', (evento) => prepararSeguinte(evento.relatedTarget))
