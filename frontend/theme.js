/**
 * Cultura theme controller.
 * - Follows the OS colour scheme by default; a manual choice (light / dark)
 *   is persisted in localStorage and overrides it. "System" clears it.
 * - Applies the `dark` class on <html> as early as possible (load in <head>)
 *   to avoid a light flash.
 * - Lazy-loads the Structure Flow WebGL background only when dark mode is on.
 */
(function () {
  const STORAGE_KEY = 'cultura-theme'; // 'light' | 'dark' | (absent = system)
  const root = document.documentElement;
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)');

  const getChoice = () => {
    try {
      const v = localStorage.getItem(STORAGE_KEY);
      return v === 'light' || v === 'dark' ? v : 'dark';
    } catch (_) { return 'dark'; }
  };
  const resolve = (choice) => (choice === 'system' ? 'dark' : (choice || 'dark'));

  // ---- Background (lazy) --------------------------------------------------
  let bgHost = null;
  let bgInstance = null;
  let bgLoading = null;
  let bgHideTimer = 0;

  function ensureHost() {
    if (bgHost) return bgHost;
    if (!document.body) return null;
    bgHost = document.getElementById('structure-flow-bg');
    if (!bgHost) {
      bgHost = document.createElement('div');
      bgHost.id = 'structure-flow-bg';
      bgHost.setAttribute('aria-hidden', 'true');
      document.body.prepend(bgHost);
    }
    return bgHost;
  }

  function showBackground() {
    if (!ensureHost()) return;
    clearTimeout(bgHideTimer);
    bgHost.classList.add('is-visible');
    if (bgInstance) { 
      if (bgInstance.setTheme) bgInstance.setTheme(true);
      bgInstance.start(); 
      return; 
    }
    if (bgLoading) return;
    bgLoading = import('/structure-flow.js')
      .then((m) => {
        bgInstance = m.createStructureFlow(bgHost, { speed: 1, density: 1 });
        if (bgInstance.setTheme) bgInstance.setTheme(true);
        bgInstance.start();
      })
      .catch((err) => console.warn('[theme] Structure Flow background unavailable:', err))
      .finally(() => { bgLoading = null; });
  }

  function hideBackground() {
    if (!bgHost) return;
    bgHost.classList.remove('is-visible');
    clearTimeout(bgHideTimer);
    // Stop rendering once the fade-out finishes.
    bgHideTimer = setTimeout(() => bgInstance && bgInstance.stop(), 700);
  }

  // ---- Chart.js integration ----------------------------------------------
  function chartColors(dark) {
    return dark
      ? { text: '#a8a29e', grid: 'rgba(255,255,255,0.06)' }
      : { text: '#78716c', grid: 'rgba(0,0,0,0.05)' };
  }
  function applyChartTheme(chart, dark) {
    const c = chartColors(dark);
    const scales = (chart.options && chart.options.scales) || {};
    Object.keys(scales).forEach((id) => {
      const s = scales[id];
      if (s.ticks) s.ticks.color = c.text;
      if (s.grid && s.grid.display !== false) s.grid.color = c.grid;
    });
  }
  let chartPluginRegistered = false;
  function registerChartPlugin() {
    if (chartPluginRegistered || !window.Chart) return;
    chartPluginRegistered = true;
    window.Chart.register({
      id: 'culturaTheme',
      beforeUpdate(chart) { applyChartTheme(chart, root.classList.contains('dark')); },
    });
  }
  function refreshCharts() {
    if (!window.Chart || !window.Chart.instances) return;
    Object.values(window.Chart.instances).forEach((ch) => ch.update('none'));
  }

  // ---- Apply ---------------------------------------------------------------
  function apply(animate) {
    const choice = getChoice();
    const mode = resolve(choice);
    if (animate) {
      root.classList.add('theme-transition');
      setTimeout(() => root.classList.remove('theme-transition'), 450);
    }
    root.classList.toggle('dark', mode === 'dark');
    root.style.colorScheme = mode;
    root.dataset.themeChoice = choice;

    document.querySelectorAll('[data-theme-choice]').forEach((btn) => {
      btn.setAttribute('aria-checked', String(btn.dataset.themeChoice === choice));
    });

    if (document.body) {
      showBackground();
      refreshCharts();
    }
  }

  function setChoice(choice) {
    try {
      if (choice === 'system') localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, choice);
    } catch (_) { /* storage disabled — still apply for this page */ }
    apply(true);
  }

  // ---- Toggle UI -------------------------------------------------------------
  const ICONS = {
    light: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    system: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>',
    dark: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
  };
  const LABELS = { light: 'Light', system: 'System', dark: 'Dark' };

  function mountToggle() {
    if (document.getElementById('theme-switch')) return;
    const host = document.querySelector('aside');
    if (!host) return;
    const wrap = document.createElement('div');
    wrap.className = 'theme-switch-wrap';
    wrap.innerHTML =
      '<span class="theme-switch-label">Appearance</span>' +
      '<div id="theme-switch" class="theme-switch" role="radiogroup" aria-label="Colour theme">' +
      '<span class="theme-switch-thumb" aria-hidden="true"></span>' +
      ['light', 'system', 'dark'].map((c) =>
        `<button type="button" id="theme-${c}" role="radio" data-theme-choice="${c}" title="${LABELS[c]}" aria-label="${LABELS[c]} theme">${ICONS[c]}</button>`
      ).join('') +
      '</div>';
    host.appendChild(wrap);
    wrap.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-theme-choice]');
      if (btn) setChoice(btn.dataset.themeChoice);
    });
  }

  // ---- Boot ------------------------------------------------------------------
  apply(false); // runs in <head>: sets the class before first paint

  systemDark.addEventListener('change', () => { if (getChoice() === 'system') apply(true); });
  window.addEventListener('storage', (e) => { if (e.key === STORAGE_KEY) apply(true); });

  const initTheme = () => {
    mountToggle();
    registerChartPlugin();
    apply(false);
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }

  window.addEventListener('pagehide', (e) => {
    if (!e.persisted && bgInstance) { bgInstance.dispose(); bgInstance = null; }
  });

  // In-app non-blocking toast notifications (replaces window.alert for iframe compatibility)
  window.showToast = function (message, type = 'info') {
    let container = document.getElementById('cultura-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'cultura-toast-container';
      container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:999999;display:flex;flex-direction:column;gap:10px;pointer-events:none;max-width:380px;';
      if (document.body) document.body.appendChild(container);
    }
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'cultura-toast';
    toast.style.cssText = 'pointer-events:auto;background:rgba(18,24,38,0.92);backdrop-filter:blur(10px);color:#f8fafc;padding:12px 18px;border-radius:12px;border:1px solid rgba(255,255,255,0.15);box-shadow:0 10px 25px -5px rgba(0,0,0,0.5);font-size:13px;font-family:sans-serif;line-height:1.4;display:flex;align-items:center;gap:12px;opacity:0;transform:translateY(10px);transition:all 0.25s ease;';
    const isError = type === 'error' || (typeof message === 'string' && (message.toLowerCase().includes('fail') || message.toLowerCase().includes('error') || message.toLowerCase().includes('alert') || message.toLowerCase().includes('rejected')));
    toast.innerHTML = `<span style="font-size:16px;">${isError ? '⚠️' : '✨'}</span><span>${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4200);
  };
  window.alert = function (msg) {
    window.showToast(msg);
  };

  window.CulturaTheme = { set: setChoice, get: getChoice, resolved: () => resolve(getChoice()) };
})();
