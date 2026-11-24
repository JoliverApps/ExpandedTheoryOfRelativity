/* Reading preferences and optional GoatCounter statistics. No analytics credentials. */
(() => {
  'use strict';
  const root = document.documentElement;
  const size = document.getElementById('reader-text-size');
  const theme = document.getElementById('reader-theme');
  const status = document.getElementById('reader-status');
  const preferenceKey = 'relativity-reader-preferences';
  const validSizes = ['1', '1.15', '1.3'];
  const validThemes = ['auto', 'light', 'dark'];
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(preferenceKey) || '{}') || {}; } catch (_) {}

  function applyPreferences(announce) {
    root.style.setProperty('--reader-scale', size.value);
    if (theme.value === 'auto') delete root.dataset.readerTheme;
    else root.dataset.readerTheme = theme.value;
    if (announce && status) {
      status.textContent = `Reading options updated: ${size.selectedOptions[0].text}, ${theme.selectedOptions[0].text}.`;
    }
    try { localStorage.setItem(preferenceKey, JSON.stringify({size: size.value, theme: theme.value})); } catch (_) {}
  }
  if (size && theme) {
    size.value = validSizes.includes(saved.size) ? saved.size : '1';
    theme.value = validThemes.includes(saved.theme) ? saved.theme : 'auto';
    applyPreferences(false);
    size.disabled = false;
    theme.disabled = false;
    size.addEventListener('change', () => applyPreferences(true));
    theme.addEventListener('change', () => applyPreferences(true));
  }

  // Only scrollable equations become keyboard stops and labelled regions.
  // Short equations remain ordinary content, without hundreds of extra stops.
  const equations = Array.from(document.querySelectorAll('.equation-scroll'));
  function updateEquation(wrapper) {
    if (wrapper.scrollWidth > wrapper.clientWidth + 2) {
      wrapper.tabIndex = 0;
      wrapper.setAttribute('role', 'region');
      const number = wrapper.querySelector('.ltx_tag_equation');
      wrapper.setAttribute('aria-label', `${number ? 'Equation ' + number.textContent.trim() : 'Equation'}; scroll horizontally to read`);
    } else {
      wrapper.removeAttribute('tabindex');
      wrapper.removeAttribute('role');
      wrapper.removeAttribute('aria-label');
    }
  }
  const updateEquations = () => equations.forEach(updateEquation);
  updateEquations();
  if ('ResizeObserver' in window) {
    const observer = new ResizeObserver(entries => entries.forEach(entry => updateEquation(entry.target)));
    equations.forEach(wrapper => observer.observe(wrapper));
  } else window.addEventListener('resize', updateEquations);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(updateEquations);

  const configNode = document.getElementById('reader-config');
  let analytics;
  try { analytics = JSON.parse(configNode ? configNode.textContent : '{}').analytics; } catch (_) { return; }
  if (!analytics || !analytics.url) return;

  async function publicTotal(path, id) {
    const output = document.getElementById(id);
    if (!output) return;
    try {
      const response = await fetch(`${analytics.url}/counter/${encodeURIComponent(path)}.json`, {
        credentials: 'omit', referrerPolicy: 'no-referrer'
      });
      if (!response.ok && response.status !== 404) throw new Error('Counter unavailable');
      const result = await response.json();
      if (!['string', 'number'].includes(typeof result.count)) throw new Error('No total');
      // An unused path returns HTTP 404 with a genuine zero from GoatCounter.
      if (response.status === 404 && String(result.count) !== '0') throw new Error('No total');
      output.textContent = String(result.count).slice(0, 32);
      output.removeAttribute('aria-label');
    } catch (_) {
      output.textContent = '—';
      output.setAttribute('aria-label', 'Total not available yet');
    } finally { output.setAttribute('aria-busy', 'false'); }
  }
  // Reading a public total is separate from sending a visit or click event.
  if (analytics.public_totals) {
    publicTotal(analytics.path, 'visit-count');
    publicTotal(analytics.event, 'pdf-count');
  }
  const optedOut = navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.globalPrivacyControl === true;
  if (optedOut) return;
  window.goatcounter = {path: analytics.path, referrer: ''};
  const tracker = document.createElement('script');
  tracker.async = true;
  tracker.src = 'https://gc.zgo.at/count.js';
  tracker.referrerPolicy = 'no-referrer';
  tracker.setAttribute('data-goatcounter', `${analytics.url}/count`);
  document.head.appendChild(tracker);
})();
