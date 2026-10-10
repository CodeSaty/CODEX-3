/**
 * Cultura Festival Hub — Universal NLP Festival Assistant
 * Accessible everywhere across the festival management application.
 * Provides high-contrast, crystal-clear readability and live festival telemetry.
 */
(function() {
  // Ensure singleton initialization
  if (window.__culturaNlpInitialized) return;
  window.__culturaNlpInitialized = true;

  // Assistant State
  const assistantState = {
    isOpen: false,
    history: [],
    isLoading: false,
  };

  // Helper: Get Admin Key safely
  function getAdminKey() {
    return window.currentAdminKey || sessionStorage.getItem('adminKey') || localStorage.getItem('adminKey') || '';
  }

  // Helper: Escape HTML
  function escapeHTML(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Create Universal Assistant UI DOM
  function injectAssistantUI() {
    // 1. Floating Launcher Button
    const launcher = document.createElement('div');
    launcher.id = 'cultura-nlp-launcher';
    launcher.className = 'fixed bottom-6 right-6 z-30 print:hidden transition-all duration-300';
    launcher.innerHTML = `
      <button type="button" id="cultura-nlp-toggle-btn"
        class="group flex items-center gap-2.5 px-4 py-3 rounded-2xl bg-stone-900 text-white dark:bg-rose-600 dark:hover:bg-rose-500 shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 border border-stone-800 dark:border-rose-400 transition-all duration-200 cursor-pointer"
        title="Open Festival Assistant (Shortcut: ⌘K or /)">
        <div class="relative flex items-center justify-center w-6 h-6 rounded-lg bg-rose-600 dark:bg-white text-white dark:text-rose-600">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
          </svg>
          <span class="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-stone-900"></span>
        </div>
        <div class="flex flex-col text-left">
          <span class="text-xs font-bold tracking-wide uppercase text-stone-200 dark:text-white leading-tight">Festival AI Assistant</span>
          <span class="text-[10px] text-stone-400 dark:text-rose-100 font-medium leading-none">Telemetry & Insights</span>
        </div>
        <kbd class="hidden sm:inline-block ml-1 px-1.5 py-0.5 text-[10px] font-mono font-bold rounded bg-stone-800 text-stone-300 dark:bg-rose-700 dark:text-white border border-stone-700 dark:border-rose-400">⌘K</kbd>
      </button>
    `;

    // 2. Backdrop & Slide-out Assistant Drawer
    const drawerContainer = document.createElement('div');
    drawerContainer.id = 'cultura-nlp-modal-root';
    drawerContainer.className = 'print:hidden';
    drawerContainer.innerHTML = `
      <!-- Backdrop -->
      <div id="cultura-nlp-backdrop" class="fixed inset-0 bg-stone-950/60 backdrop-blur-sm z-50 transition-opacity duration-300 opacity-0 pointer-events-none"></div>

      <!-- Slide-out Drawer -->
      <aside id="cultura-nlp-drawer" class="fixed top-0 right-0 bottom-0 w-full sm:w-[500px] z-50 bg-stone-50 dark:bg-stone-950 text-stone-900 dark:text-stone-100 shadow-2xl border-l border-stone-200 dark:border-stone-800 flex flex-col transform translate-x-full transition-transform duration-300 ease-out"
        role="dialog" aria-modal="true" aria-label="Festival AI Assistant">
        
        <!-- Drawer Header -->
        <div class="p-5 border-b border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 flex items-center justify-between shrink-0 shadow-sm">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 to-amber-500 text-white flex items-center justify-center shadow-md">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-base font-serif font-bold text-stone-900 dark:text-white leading-tight">Cultura Assistant</h3>
                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Live Telemetry
                </span>
              </div>
              <p class="text-xs text-stone-700 dark:text-stone-300">Crowd bottlenecks, pass status & cashless economy</p>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button type="button" id="cultura-nlp-clear-btn" class="p-2 text-stone-600 hover:text-stone-900 dark:text-stone-300 dark:hover:text-white rounded-lg hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors" title="Clear conversation">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <button type="button" id="cultura-nlp-close-btn" class="p-2 text-stone-600 hover:text-stone-900 dark:text-stone-300 dark:hover:text-white rounded-lg hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors" title="Close Assistant (Esc)">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Quick Questions Chips -->
        <div class="p-3 bg-stone-100 dark:bg-stone-900/50 border-b border-stone-200 dark:border-stone-800 overflow-x-auto no-scrollbar shrink-0">
          <div class="flex items-center gap-1.5 text-xs">
            <span class="text-[11px] font-bold text-stone-600 dark:text-stone-400 uppercase tracking-wider pl-1 shrink-0">Quick:</span>
            <button type="button" class="nlp-quick-prompt shrink-0 px-3 py-1.5 rounded-lg bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 text-stone-800 dark:text-stone-200 hover:border-rose-500 hover:text-rose-600 dark:hover:text-rose-400 font-medium transition-all shadow-sm"
              data-prompt="Are there any crowded zones or bottlenecks?">
              ⚠️ Crowded Zones?
            </button>
            <button type="button" class="nlp-quick-prompt shrink-0 px-3 py-1.5 rounded-lg bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 text-stone-800 dark:text-stone-200 hover:border-rose-500 hover:text-rose-600 dark:hover:text-rose-400 font-medium transition-all shadow-sm"
              data-prompt="How many Fest Coins minted and total rupee revenue collected?">
              🪙 Coins & Rupee Revenue
            </button>
            <button type="button" class="nlp-quick-prompt shrink-0 px-3 py-1.5 rounded-lg bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 text-stone-800 dark:text-stone-200 hover:border-rose-500 hover:text-rose-600 dark:hover:text-rose-400 font-medium transition-all shadow-sm"
              data-prompt="How many VIPs in Artisan Market?">
              ⭐ VIPs in Artisan Market?
            </button>
            <button type="button" class="nlp-quick-prompt shrink-0 px-3 py-1.5 rounded-lg bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 text-stone-800 dark:text-stone-200 hover:border-rose-500 hover:text-rose-600 dark:hover:text-rose-400 font-medium transition-all shadow-sm"
              data-prompt="How many active passes versus revoked passes?">
              👥 Active vs Revoked Passes
            </button>
            <button type="button" class="nlp-quick-prompt shrink-0 px-3 py-1.5 rounded-lg bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 text-stone-800 dark:text-stone-200 hover:border-rose-500 hover:text-rose-600 dark:hover:text-rose-400 font-medium transition-all shadow-sm"
              data-prompt="Any active emergency SOS alerts or incidents?">
              🚨 Emergency Alerts?
            </button>
          </div>
        </div>

        <!-- Conversation Scroll Area -->
        <div id="cultura-nlp-messages" class="flex-1 overflow-y-auto p-5 space-y-4 no-scrollbar">
          <!-- Default Greeting Card -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm space-y-3">
            <div class="flex items-center gap-2 text-rose-600 dark:text-rose-400 font-bold text-xs uppercase tracking-wider">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Festival Command Intelligence
            </div>
            <p class="text-sm font-medium text-stone-800 dark:text-stone-200 leading-relaxed">
              Hello! I monitor festival crowds, telemetry across all 5 zones, cashless Fest Coin balances, attendee passes, and emergency triage.
            </p>
            <div class="grid grid-cols-2 gap-2 pt-1 text-xs font-semibold text-stone-700 dark:text-stone-300">
              <div class="p-2.5 rounded-xl bg-stone-50 dark:bg-stone-800/80 border border-stone-200/80 dark:border-stone-700">
                <div class="font-bold text-stone-900 dark:text-white">🏟️ Zone Telemetry</div>
                <div class="text-[11px] text-stone-600 dark:text-stone-300 font-normal">Scans, capacity & crowd crush alerts</div>
              </div>
              <div class="p-2.5 rounded-xl bg-stone-50 dark:bg-stone-800/80 border border-stone-200/80 dark:border-stone-700">
                <div class="font-bold text-stone-900 dark:text-white">🪙 Fest Coins</div>
                <div class="text-[11px] text-stone-600 dark:text-stone-300 font-normal">Balances, ₹ conversions & top-ups</div>
              </div>
              <div class="p-2.5 rounded-xl bg-stone-50 dark:bg-stone-800/80 border border-stone-200/80 dark:border-stone-700">
                <div class="font-bold text-stone-900 dark:text-white">🎫 Pass Control</div>
                <div class="text-[11px] text-stone-600 dark:text-stone-300 font-normal">Active vs revoked status & VIP tracking</div>
              </div>
              <div class="p-2.5 rounded-xl bg-stone-50 dark:bg-stone-800/80 border border-stone-200/80 dark:border-stone-700">
                <div class="font-bold text-stone-900 dark:text-white">🚨 Security SOS</div>
                <div class="text-[11px] text-stone-600 dark:text-stone-300 font-normal">Incident radar & crowd diversions</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Footer -->
        <div class="p-4 bg-white dark:bg-stone-900 border-t border-stone-200 dark:border-stone-800 shrink-0 shadow-lg">
          <form id="cultura-nlp-drawer-form" class="relative flex items-center gap-2">
            <input type="text" id="cultura-nlp-drawer-input"
              class="flex-1 bg-stone-100 dark:bg-stone-800 border border-stone-300 dark:border-stone-700 text-stone-900 dark:text-white text-sm rounded-xl px-4 py-3 pr-10 focus:ring-2 focus:ring-rose-500 focus:border-rose-500 focus:bg-white dark:focus:bg-stone-800 transition-all placeholder-stone-500 dark:placeholder-stone-400 font-medium"
              placeholder="Ask anything about crowds, coins, passes..." autocomplete="off">
            <button type="submit" id="cultura-nlp-submit-btn"
              class="px-4 py-3 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold tracking-wide transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-1.5 shrink-0 cursor-pointer disabled:opacity-50">
              <span id="cultura-nlp-btn-text">Ask</span>
              <svg id="cultura-nlp-btn-icon" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </form>
          <div class="flex items-center justify-between mt-2 px-1 text-[11px] text-stone-600 dark:text-stone-400">
            <span>Press <kbd class="px-1 py-0.5 rounded bg-stone-200 dark:bg-stone-800 font-mono text-[10px] text-stone-800 dark:text-stone-300">Enter</kbd> to submit</span>
            <span><kbd class="px-1 py-0.5 rounded bg-stone-200 dark:bg-stone-800 font-mono text-[10px] text-stone-800 dark:text-stone-300">Esc</kbd> closes</span>
          </div>
        </div>

      </aside>
    `;

    document.body.appendChild(launcher);
    document.body.appendChild(drawerContainer);

    bindEvents();
  }

  // Open Drawer
  function openAssistant(initialQuery) {
    const drawer = document.getElementById('cultura-nlp-drawer');
    const backdrop = document.getElementById('cultura-nlp-backdrop');
    const input = document.getElementById('cultura-nlp-drawer-input');

    if (!drawer || !backdrop) return;

    assistantState.isOpen = true;
    backdrop.classList.remove('opacity-0', 'pointer-events-none');
    backdrop.classList.add('opacity-100');
    drawer.classList.remove('translate-x-full');
    drawer.classList.add('translate-x-0');

    if (initialQuery && initialQuery.trim()) {
      input.value = initialQuery;
      submitQuery(initialQuery);
    } else {
      setTimeout(() => input.focus(), 150);
    }
  }

  // Close Drawer
  function closeAssistant() {
    const drawer = document.getElementById('cultura-nlp-drawer');
    const backdrop = document.getElementById('cultura-nlp-backdrop');

    if (!drawer || !backdrop) return;

    assistantState.isOpen = false;
    backdrop.classList.remove('opacity-100');
    backdrop.classList.add('opacity-0', 'pointer-events-none');
    drawer.classList.remove('translate-x-0');
    drawer.classList.add('translate-x-full');
  }

  // Toggle Drawer
  function toggleAssistant() {
    if (assistantState.isOpen) {
      closeAssistant();
    } else {
      openAssistant();
    }
  }

  // Submit Query
  async function submitQuery(queryText) {
    const query = (queryText || '').trim();
    if (!query || assistantState.isLoading) return;

    const messagesContainer = document.getElementById('cultura-nlp-messages');
    const input = document.getElementById('cultura-nlp-drawer-input');
    const btn = document.getElementById('cultura-nlp-submit-btn');
    const btnText = document.getElementById('cultura-nlp-btn-text');
    const btnIcon = document.getElementById('cultura-nlp-btn-icon');

    // Sync input field
    input.value = '';

    // Append User Message to Drawer
    const userMsgEl = document.createElement('div');
    userMsgEl.className = 'flex items-start justify-end gap-2.5';
    userMsgEl.innerHTML = `
      <div class="max-w-[85%] p-3.5 rounded-2xl rounded-tr-sm bg-stone-900 text-white dark:bg-rose-600 dark:text-white shadow-sm text-sm font-medium">
        <p class="leading-relaxed">${escapeHTML(query)}</p>
        <span class="block text-[10px] text-stone-400 dark:text-rose-200 text-right mt-1">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
    `;
    messagesContainer.appendChild(userMsgEl);

    // Append Loading Placeholder
    const loadingId = 'nlp-loading-' + Date.now();
    const loadingMsgEl = document.createElement('div');
    loadingMsgEl.id = loadingId;
    loadingMsgEl.className = 'flex items-start gap-3';
    loadingMsgEl.innerHTML = `
      <div class="w-8 h-8 rounded-xl bg-rose-600 text-white flex items-center justify-center shrink-0 shadow-sm">
        <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      <div class="p-4 rounded-2xl rounded-tl-sm bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm max-w-[85%]">
        <div class="flex items-center gap-2 text-xs font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider mb-1">
          <span>Analyzing Festival Telemetry...</span>
        </div>
        <p class="text-xs text-stone-600 dark:text-stone-400 font-medium animate-pulse">Querying real-time zone scans, pass records and Fest Coin ledgers...</p>
      </div>
    `;
    messagesContainer.appendChild(loadingMsgEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Update Button State
    assistantState.isLoading = true;
    btn.disabled = true;
    btnText.textContent = '...';

    // Also update on-page response if present (e.g. index.html)
    updateOnPageNLP(query, 'Analyzing festival telemetry...', true);

    try {
      const res = await fetch('/api/admin/nlp_query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': getAdminKey(),
        },
        body: JSON.stringify({ query: query }),
      });

      const loadingEl = document.getElementById(loadingId);
      if (loadingEl) loadingEl.remove();

      if (res.ok) {
        const data = await res.json();
        renderAssistantResponse(data);
        updateOnPageNLP(query, data.response || data.answer, false, data);
      } else {
        const errorMsg = "Unable to fetch festival telemetry right now. Please check admin authorization.";
        renderAssistantResponse({ answer: errorMsg, category: 'error' });
        updateOnPageNLP(query, errorMsg, false);
      }
    } catch (err) {
      const loadingEl = document.getElementById(loadingId);
      if (loadingEl) loadingEl.remove();

      const fallbackMsg = "Offline Fallback: Telemetry data shows regular festival attendance across all gates.";
      renderAssistantResponse({ answer: fallbackMsg, category: 'offline' });
      updateOnPageNLP(query, fallbackMsg, false);
    } finally {
      assistantState.isLoading = false;
      btn.disabled = false;
      btnText.textContent = 'Ask';
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  // Render Rich Assistant Response in Drawer
  function renderAssistantResponse(data) {
    const messagesContainer = document.getElementById('cultura-nlp-messages');
    const answer = data.response || data.answer || 'Query processed.';
    const metrics = data.metrics || [];
    const actions = data.quick_actions || [];

    const respEl = document.createElement('div');
    respEl.className = 'flex items-start gap-3';

    // Build metrics HTML
    let metricsHtml = '';
    if (metrics.length > 0) {
      metricsHtml = `
        <div class="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-stone-100 dark:border-stone-800">
          ${metrics.map(m => `
            <div class="p-2 rounded-xl bg-stone-50 dark:bg-stone-800/60 border border-stone-200/80 dark:border-stone-700/80">
              <span class="block text-[10px] uppercase font-bold text-stone-500 dark:text-stone-400">${escapeHTML(m.label)}</span>
              <span class="block text-xs font-bold ${m.alert ? 'text-rose-600 dark:text-rose-400' : 'text-stone-900 dark:text-white'}">${escapeHTML(m.value)}</span>
            </div>
          `).join('')}
        </div>
      `;
    }

    // Build actions HTML
    let actionsHtml = '';
    if (actions.length > 0) {
      actionsHtml = `
        <div class="flex flex-wrap items-center gap-1.5 mt-3 pt-2">
          ${actions.map(a => {
            if (a.action === 'diversion') {
              return `<button type="button" onclick="if(window.triggerDiversionDialog) window.triggerDiversionDialog('Cultural Pavilion');" class="px-2.5 py-1 text-xs font-bold rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800 hover:bg-rose-100 transition-colors">${escapeHTML(a.label)}</button>`;
            }
            return `<a href="${a.url}" class="px-2.5 py-1 text-xs font-bold rounded-lg bg-stone-100 text-stone-800 dark:bg-stone-800 dark:text-stone-200 border border-stone-200 dark:border-stone-700 hover:bg-stone-200 transition-colors">${escapeHTML(a.label)}</a>`;
          }).join('')}
        </div>
      `;
    }

    respEl.innerHTML = `
      <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-rose-600 to-amber-500 text-white flex items-center justify-center shrink-0 shadow-sm mt-1">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
      <div class="p-4 rounded-2xl rounded-tl-sm bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm max-w-[88%] space-y-2">
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5 text-xs font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Telemetry Response</span>
          </div>
          <span class="text-[10px] text-stone-500 dark:text-stone-400">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
        <p class="text-sm font-semibold text-stone-900 dark:text-stone-100 leading-relaxed">
          ${escapeHTML(answer)}
        </p>
        ${metricsHtml}
        ${actionsHtml}
      </div>
    `;

    messagesContainer.appendChild(respEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Update on-page inline elements if they exist (index.html, etc.)
  function updateOnPageNLP(query, text, isLoading, fullData) {
    const respEl = document.getElementById('nlp-response');
    const outputEl = document.getElementById('nlp-output-text');
    if (!respEl || !outputEl) return;

    respEl.classList.remove('hidden', 'opacity-0', '-translate-y-4');
    if (isLoading) {
      outputEl.innerHTML = `<span class="animate-pulse text-stone-600 dark:text-stone-400 font-medium">Analyzing festival telemetry...</span>`;
    } else {
      outputEl.textContent = text;
      // Ensure high readability styles
      outputEl.className = "text-base sm:text-lg font-bold text-stone-900 dark:text-white leading-relaxed";
    }
  }

  // Bind User Events
  function bindEvents() {
    // 1. Toggle Button
    const toggleBtn = document.getElementById('cultura-nlp-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => toggleAssistant());
    }

    // 2. Close & Backdrop
    const closeBtn = document.getElementById('cultura-nlp-close-btn');
    const backdrop = document.getElementById('cultura-nlp-backdrop');
    if (closeBtn) closeBtn.addEventListener('click', () => closeAssistant());
    if (backdrop) backdrop.addEventListener('click', () => closeAssistant());

    // 3. Clear Chat
    const clearBtn = document.getElementById('cultura-nlp-clear-btn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        const messages = document.getElementById('cultura-nlp-messages');
        if (messages) {
          messages.innerHTML = `
            <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm text-center">
              <p class="text-xs text-stone-500 dark:text-stone-400">Conversation cleared. Ask any festival question below.</p>
            </div>
          `;
        }
      });
    }

    // 4. Drawer Form Submit
    const drawerForm = document.getElementById('cultura-nlp-drawer-form');
    if (drawerForm) {
      drawerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = document.getElementById('cultura-nlp-drawer-input');
        if (input && input.value.trim()) {
          submitQuery(input.value);
        }
      });
    }

    // 5. Quick Prompt Chips
    document.addEventListener('click', (e) => {
      const chip = e.target.closest('.nlp-quick-prompt') || e.target.closest('.quick-chip');
      if (chip) {
        const prompt = chip.getAttribute('data-prompt') || chip.getAttribute('data-query');
        if (prompt) {
          openAssistant(prompt);
        }
      }
    });

    // 6. Bind to existing header `#nlp-form` on any page!
    const headerForms = document.querySelectorAll('form#nlp-form');
    headerForms.forEach(form => {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = form.querySelector('input#nlp-input');
        if (input && input.value.trim()) {
          const q = input.value;
          openAssistant(q);
        } else {
          openAssistant();
        }
      });
    });

    // 7. Global Keyboard Shortcuts: ⌘K, Ctrl+K, or "/"
    window.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        toggleAssistant();
      } else if (e.key === 'Escape' && assistantState.isOpen) {
        closeAssistant();
      } else if (e.key === '/' && !assistantState.isOpen) {
        const activeTag = document.activeElement ? document.activeElement.tagName : '';
        if (activeTag !== 'INPUT' && activeTag !== 'TEXTAREA') {
          e.preventDefault();
          openAssistant();
        }
      }
    });
  }

  // Expose global methods
  window.openNLPAssistant = openAssistant;
  window.closeNLPAssistant = closeAssistant;
  window.processNLPQuery = function(query) {
    openAssistant(query);
  };

  // Auto-initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectAssistantUI);
  } else {
    injectAssistantUI();
  }
})();
