/**
 * AnimatedTopDock.js
 * Sable Proximity-Spring Menu in Four Fits:
 * - Centred Dock (sable)
 * - Modern Command Bar
 * - Retro Pixel-Terminal Strip
 * - Vertical Refracting Glass Rail
 *
 * Authored Items:
 * - Logo brand control
 * - SYSTEM, METHOD, WORK, ACCESS, NOTES
 */

import { createTopDockController } from './topDockController.js';
import { createRetroPixelField } from './retroPixelField.js';
import { createGlassParticleField } from './glassParticleField.js';

export const AUTHORED_ICONS = {
  brand: `
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="12 2 2 7 12 12 22 7 12 2"/>
      <polyline points="2 17 12 22 22 17"/>
      <polyline points="2 12 12 17 22 12"/>
    </svg>
  `,
  OVERVIEW: `
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2"/>
      <rect x="9" y="9" width="6" height="6"/>
      <line x1="9" y1="1" x2="9" y2="4"/>
      <line x1="15" y1="1" x2="15" y2="4"/>
      <line x1="9" y1="20" x2="9" y2="23"/>
      <line x1="15" y1="20" x2="15" y2="23"/>
      <line x1="20" y1="9" x2="23" y2="9"/>
      <line x1="20" y1="14" x2="23" y2="14"/>
      <line x1="1" y1="9" x2="4" y2="9"/>
      <line x1="1" y1="14" x2="4" y2="14"/>
    </svg>
  `,
  WORKFLOWS: `
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="18" cy="5" r="3"/>
      <circle cx="6" cy="12" r="3"/>
      <circle cx="18" cy="19" r="3"/>
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
    </svg>
  `,
  ANALYTICS: `
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="14"/>
      <polyline points="2 6 7 11 12 7 22 17"/>
    </svg>
  `,
  SENTIMENT: `
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <circle cx="12" cy="11" r="2.5"/>
      <path d="M7.5 15.5a6 6 0 0 0 9 0"/>
    </svg>
  `,
  COPILOT: `
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  `,
  // Backward compatibility aliases
  SYSTEM: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>`,
  METHOD: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>`,
  WORK: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  ACCESS: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>`,
  NOTES: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
};

export const DEFAULT_DOCK_ITEMS = [
  { id: 'overview', label: 'Overview', href: '/', icon: 'OVERVIEW', description: 'Executive System Overview' },
  { id: 'workflows', label: 'Workflows', href: '/workflows.html', icon: 'WORKFLOWS', description: 'Cross-Functional Role Boards' },
  { id: 'sentiment', label: 'Sentiment Radar', href: '/sentiment.html', icon: 'SENTIMENT', description: 'Community Sentiment Radar' },
  { id: 'analytics', label: 'Velocity & Analytics', href: '/analytics.html', icon: 'ANALYTICS', description: 'Registration Velocity & Trajectory' },
  { id: 'copilot', label: 'AI Copilot', href: '/copilot.html', icon: 'COPILOT', description: 'Gemini AI Copilot War Room' },
];

/**
 * Creates and mounts an AnimatedTopDock instance into the given container.
 */
export function createAnimatedTopDock(hostEl, options = {}) {
  const {
    fit = 'centred', // 'centred' | 'sable' | 'modern' | 'retro' | 'glass' | 'vertical'
    proximity = 122,
    spring = 0.19,
    damping = 0.70,
    items = DEFAULT_DOCK_ITEMS,
    activeItem = null,
    onItemClick = null,
  } = options;

  const isVertical = fit === 'vertical';

  // Construct DOM structure
  const host = document.createElement('nav');
  host.className = `top-dock-host fit-${fit}`;
  host.setAttribute('aria-label', 'Primary Command Dock');

  const container = document.createElement('div');
  container.className = 'top-dock-container';

  // Canvas field container
  const fieldContainer = document.createElement('div');
  fieldContainer.className = 'top-dock-field-canvas';
  container.appendChild(fieldContainer);

  // Logo Brand Control
  const brandBtn = document.createElement('button');
  brandBtn.type = 'button';
  brandBtn.className = 'top-dock-brand';
  brandBtn.setAttribute('aria-label', 'Command Centre Core');
  brandBtn.innerHTML = AUTHORED_ICONS.brand;
  brandBtn.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = '/';
  });
  container.appendChild(brandBtn);

  // Divider
  const divider = document.createElement('div');
  divider.className = 'top-dock-divider';
  container.appendChild(divider);

  // Menu items list
  const ul = document.createElement('ul');
  ul.className = 'top-dock-items';
  ul.setAttribute('role', 'menubar');

  const itemButtons = [];

  // Determine current active item from URL pathname if not explicitly passed
  const currentPath = (window.location.pathname || '').replace(/\/$/, '') || '/';

  items.forEach((item, index) => {
    const li = document.createElement('li');
    li.setAttribute('role', 'none');

    const a = document.createElement('a');
    a.className = 'top-dock-item';
    a.href = item.href || '#';
    a.setAttribute('role', 'menuitem');
    a.setAttribute('data-item', item.id);
    a.title = item.description || item.label;

    const iconSvg = AUTHORED_ICONS[item.icon] || AUTHORED_ICONS[item.id?.toUpperCase()] || AUTHORED_ICONS.OVERVIEW;
    a.innerHTML = `${iconSvg}<span class="top-dock-label">${item.label}</span>`;

    const itemPath = (item.href || '').replace(/\/$/, '') || '/';
    let isSelected = false;

    if (activeItem !== null && activeItem !== undefined) {
      isSelected = (typeof activeItem === 'number' && index === activeItem) ||
                   (typeof activeItem === 'string' && (item.id === activeItem || item.href === activeItem));
    } else {
      // Auto-detect from current URL
      isSelected = (currentPath === itemPath) ||
                   ((currentPath === '/index.html' || currentPath === '/admin.html') && itemPath === '/') ||
                   (currentPath.endsWith(itemPath) && itemPath !== '/');
    }

    if (isSelected) {
      a.classList.add('is-selected');
      a.setAttribute('aria-current', 'page');
    }

    a.addEventListener('click', (e) => {
      if (onItemClick) {
        e.preventDefault();
        onItemClick(item, index);
      }
      itemButtons.forEach((b) => {
        b.classList.remove('is-selected');
        b.removeAttribute('aria-current');
      });
      a.classList.add('is-selected');
      a.setAttribute('aria-current', 'page');
    });

    li.appendChild(a);
    ul.appendChild(li);
    itemButtons.push(a);
  });

  container.appendChild(ul);
  host.appendChild(container);
  hostEl.appendChild(host);

  // Initialize shader pass based on fit
  let shaderPass = null;
  if (fit === 'retro') {
    shaderPass = createRetroPixelField(fieldContainer);
    shaderPass.start();
  } else if (fit === 'glass' || fit === 'vertical') {
    shaderPass = createGlassParticleField(fieldContainer);
    shaderPass.start();
  }

  // Initialize proximity spring physics controller
  const controller = createTopDockController(container, {
    proximity,
    spring,
    damping,
    vertical: isVertical,
    onPointerChange: (x, y, active) => {
      if (shaderPass && shaderPass.updatePointer) {
        shaderPass.updatePointer(x, y, active);
      }
    }
  });

  return {
    element: host,
    controller,
    shaderPass,
    setFit(newFit) {
      host.className = `top-dock-host fit-${newFit}`;
      if (shaderPass) {
        shaderPass.dispose();
        shaderPass = null;
      }
      if (newFit === 'retro') {
        shaderPass = createRetroPixelField(fieldContainer);
        shaderPass.start();
      } else if (newFit === 'glass' || newFit === 'vertical') {
        shaderPass = createGlassParticleField(fieldContainer);
        shaderPass.start();
      }
      controller.measure();
    },
    setSelected(idOrIdx) {
      controller.setSelected(idOrIdx);
    },
    dispose() {
      controller.dispose();
      if (shaderPass) shaderPass.dispose();
      host.remove();
    }
  };
}
