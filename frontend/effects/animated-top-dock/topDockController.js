/**
 * topDockController.js
 * Authored Proximity-Spring Layout Controller for Sable Top Dock
 *
 * Physics:
 *   influence = smoothstep(clamp(1 - distance / proximity, 0, 1))
 *   state.velocity += (influence - state.value) * spring
 *   state.velocity *= damping
 *   state.value += state.velocity
 *   transform = translateY(state.value * 3.5px)
 *   width growth: max 17px
 *   height growth: max 16px
 */

function clamp(val, min, max) {
  return Math.max(min, Math.min(max, val));
}

function smoothstep(t) {
  return t * t * (3 - 2 * t);
}

export function createTopDockController(container, options = {}) {
  const proximityRadius = options.proximity ?? 122;
  const spring = options.spring ?? 0.19;
  const damping = options.damping ?? 0.70;
  const isVertical = options.vertical ?? false;
  const onPointerChange = options.onPointerChange ?? null;

  const itemElements = Array.from(container.querySelectorAll('.top-dock-item'));
  const brandElement = container.querySelector('.top-dock-brand');
  const allInteractive = [brandElement, ...itemElements].filter(Boolean);

  const coarseMq = window.matchMedia('(pointer: coarse)');
  const reducedMotionMq = window.matchMedia('(prefers-reduced-motion: reduce)');

  let isCoarse = coarseMq.matches || window.innerWidth <= 768;
  let isReducedMotion = reducedMotionMq.matches;

  // State table per item
  const itemStates = itemElements.map((el) => ({
    element: el,
    value: 0,
    velocity: 0,
    target: 0,
    centerX: 0,
    centerY: 0,
    baseWidth: 0,
    baseHeight: 0,
    isFocused: false,
  }));

  let rafId = 0;
  let pointerActive = false;
  let pointerX = -9999;
  let pointerY = -9999;
  let isSettled = true;

  // Measure center positions at rest
  function measure() {
    isCoarse = coarseMq.matches || window.innerWidth <= 768;
    isReducedMotion = reducedMotionMq.matches;

    itemStates.forEach((state) => {
      const rect = state.element.getBoundingClientRect();
      state.centerX = rect.left + rect.width / 2;
      state.centerY = rect.top + rect.height / 2;
      state.baseWidth = rect.width;
      state.baseHeight = rect.height;
    });
  }

  // Calculate proximity influence for each item
  function updateTargets() {
    if (isCoarse || isReducedMotion) {
      itemStates.forEach((s) => { s.target = 0; });
      return;
    }

    itemStates.forEach((state) => {
      if (state.isFocused) {
        state.target = 1.0;
        return;
      }

      if (!pointerActive) {
        state.target = 0;
        return;
      }

      const dist = isVertical
        ? Math.abs(pointerY - state.centerY)
        : Math.abs(pointerX - state.centerX);

      const norm = clamp(1 - dist / proximityRadius, 0, 1);
      state.target = smoothstep(norm);
    });
  }

  // Physics animation tick
  function tick() {
    let activeSprings = false;

    itemStates.forEach((state) => {
      // Spring integration
      state.velocity += (state.target - state.value) * spring;
      state.velocity *= damping;
      state.value += state.velocity;

      // Rest threshold settling
      if (Math.abs(state.value - state.target) < 0.0002 && Math.abs(state.velocity) < 0.0002) {
        state.value = state.target;
        state.velocity = 0;
      } else {
        activeSprings = true;
      }

      // Apply authored growth bounds:
      // translateY: max 3.5px
      // width growth: max 17px
      // height growth: max 16px
      const el = state.element;
      if (isCoarse || isReducedMotion) {
        el.style.transform = '';
        el.style.paddingLeft = '';
        el.style.paddingRight = '';
        el.style.height = '';
        return;
      }

      const translateY = state.value * 3.5;
      const growthW = state.value * 17;
      const growthH = state.value * 16;

      el.style.transform = `translateY(${translateY.toFixed(2)}px)`;
      el.style.paddingLeft = `${(13 + growthW * 0.5).toFixed(2)}px`;
      el.style.paddingRight = `${(13 + growthW * 0.5).toFixed(2)}px`;
      el.style.height = `${(34 + growthH * 0.35).toFixed(2)}px`;
      el.style.setProperty('--spring-val', state.value.toFixed(3));
    });

    if (activeSprings || pointerActive) {
      rafId = requestAnimationFrame(tick);
      isSettled = false;
    } else {
      rafId = 0;
      isSettled = true;
    }
  }

  function startLoop() {
    if (rafId) return;
    rafId = requestAnimationFrame(tick);
  }

  // Pointer event listeners
  const onPointerMove = (e) => {
    pointerActive = true;
    pointerX = e.clientX;
    pointerY = e.clientY;
    updateTargets();
    startLoop();

    if (onPointerChange) {
      onPointerChange(pointerX, pointerY, true);
    }
  };

  const onPointerLeave = () => {
    pointerActive = false;
    updateTargets();
    startLoop();

    if (onPointerChange) {
      onPointerChange(-999, -999, false);
    }
  };

  // Keyboard focus mirroring
  const focusHandlers = itemStates.map((state) => {
    const onFocus = () => {
      state.isFocused = true;
      updateTargets();
      startLoop();
    };
    const onBlur = () => {
      state.isFocused = false;
      updateTargets();
      startLoop();
    };
    state.element.addEventListener('focus', onFocus);
    state.element.addEventListener('blur', onBlur);
    return { state, onFocus, onBlur };
  });

  // Media query handlers
  const onCoarseChange = (e) => {
    isCoarse = e.matches || window.innerWidth <= 768;
    measure();
    updateTargets();
  };
  const onReducedMotionChange = (e) => {
    isReducedMotion = e.matches;
    measure();
    updateTargets();
  };

  coarseMq.addEventListener('change', onCoarseChange);
  reducedMotionMq.addEventListener('change', onReducedMotionChange);

  // ResizeObserver
  const ro = new ResizeObserver(() => {
    measure();
    updateTargets();
  });
  ro.observe(container);

  container.addEventListener('pointermove', onPointerMove, { passive: true });
  container.addEventListener('pointerleave', onPointerLeave);
  window.addEventListener('resize', measure, { passive: true });

  // Initial measure
  measure();

  return {
    measure,
    setSelected(targetIndexOrHref) {
      itemElements.forEach((el, idx) => {
        const matches = (typeof targetIndexOrHref === 'number' && idx === targetIndexOrHref) ||
                        (typeof targetIndexOrHref === 'string' && (el.getAttribute('href') === targetIndexOrHref || el.dataset.item === targetIndexOrHref));
        el.classList.toggle('is-selected', Boolean(matches));
        el.setAttribute('aria-current', matches ? 'page' : 'false');
      });
    },
    dispose() {
      if (rafId) cancelAnimationFrame(rafId);
      ro.disconnect();
      container.removeEventListener('pointermove', onPointerMove);
      container.removeEventListener('pointerleave', onPointerLeave);
      window.removeEventListener('resize', measure);
      coarseMq.removeEventListener('change', onCoarseChange);
      reducedMotionMq.removeEventListener('change', onReducedMotionChange);

      focusHandlers.forEach(({ state, onFocus, onBlur }) => {
        state.element.removeEventListener('focus', onFocus);
        state.element.removeEventListener('blur', onBlur);
      });

      itemStates.forEach((state) => {
        state.element.style.transform = '';
        state.element.style.paddingLeft = '';
        state.element.style.paddingRight = '';
        state.element.style.height = '';
      });
    }
  };
}
