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
  iframe.title = 'Mapa interativo com a localização da Pizzaria Marquês'
  iframe.className = 'mapa-iframe'
  iframe.referrerPolicy = 'no-referrer'
  moldura.replaceChildren(iframe)
  // keep the button in place (no layout shift), just mark it as done
  botao.disabled = true
  botao.lastChild.textContent = ' Mapa interativo aberto'
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
