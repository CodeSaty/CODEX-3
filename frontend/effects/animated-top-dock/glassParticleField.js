/**
 * glassParticleField.js
 * Three.js r128 / WebGL Refracting Glass Rail & Caustic Dispersion Pass
 * Used by the Glass / Vertical fits of the Animated Top Dock.
 */

function getThree() {
  if (typeof window !== 'undefined' && window.THREE) return window.THREE;
  return null;
}

export function createGlassParticleField(container) {
  const THREE = getThree();
  if (!THREE) {
    return {
      start() {},
      stop() {},
      resize() {},
      updatePointer() {},
      dispose() {}
    };
  }

  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none;border-radius:inherit;';
  container.appendChild(canvas);

  const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: false,
    powerPreference: 'low-power'
  });
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  // Shader quad with chromatic aberration and refracting glass flecks
  const vertexShader = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    uniform vec2 uResolution;
    uniform float uTime;
    uniform vec2 uPointer;
    uniform float uPointerStrength;
    varying vec2 vUv;

    void main() {
      vec2 uv = vUv;
      
      // Floating caustic glass specks
      vec2 p = uv * vec2(uResolution.x / uResolution.y, 1.0) * 12.0;
      float speck = sin(p.x * 3.0 + uTime * 1.5) * cos(p.y * 3.0 - uTime * 1.2);
      speck = smoothstep(0.75, 0.98, speck) * 0.45;
      
      // Travelling specular refraction bar driven by pointer
      float barDist = abs(uv.x - uPointer.x);
      float bar = exp(-barDist * barDist * 40.0) * uPointerStrength;
      
      // Chromatic dispersion offsets (R, G, B)
      float r = bar * 1.1 + speck * 0.9;
      float g = bar * 0.95 + speck * 0.7;
      float b = bar * 1.35 + speck * 1.2;
      
      // Subtle edge vignette
      float edge = smoothstep(0.0, 0.15, uv.x) * smoothstep(1.0, 0.85, uv.x);
      
      vec3 color = vec3(r, g, b) * 0.35 * edge;
      float alpha = clamp(bar * 0.45 + speck * 0.25, 0.0, 0.6) * edge;
      
      gl_FragColor = vec4(color, alpha);
    }
  `;

  const uniforms = {
    uResolution: { value: new THREE.Vector2(1, 1) },
    uTime: { value: 0 },
    uPointer: { value: new THREE.Vector2(0.5, 0.5) },
    uPointerStrength: { value: 0.0 }
  };

  const material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  });

  const geometry = new THREE.PlaneGeometry(2, 2);
  const mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);

  let running = false;
  let rafId = 0;
  let startTime = performance.now();
  let pointerTargetX = 0.5;
  let pointerTargetActive = 0;

  function resize() {
    const w = Math.max(1, container.clientWidth);
    const h = Math.max(1, container.clientHeight);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    renderer.setPixelRatio(dpr);
    renderer.setSize(w, h, false);
    uniforms.uResolution.value.set(w * dpr, h * dpr);
  }

  function updatePointer(x, y, active = true) {
    const rect = canvas.getBoundingClientRect();
    if (rect.width > 0) {
      pointerTargetX = Math.max(0, Math.min(1, (x - rect.left) / rect.width));
    }
    pointerTargetActive = active ? 1 : 0;
  }

  function frame(now) {
    if (!running) return;
    rafId = requestAnimationFrame(frame);
    const time = (now - startTime) / 1000;
    uniforms.uTime.value = time;

    // Smooth ease toward pointer target
    uniforms.uPointer.value.x += (pointerTargetX - uniforms.uPointer.value.x) * 0.18;
    uniforms.uPointerStrength.value += (pointerTargetActive - uniforms.uPointerStrength.value) * 0.12;

    renderer.render(scene, camera);
  }

  resize();

  return {
    start() {
      if (running) return;
      running = true;
      rafId = requestAnimationFrame(frame);
    },
    stop() {
      running = false;
      if (rafId) cancelAnimationFrame(rafId);
      rafId = 0;
    },
    resize,
    updatePointer,
    dispose() {
      running = false;
      if (rafId) cancelAnimationFrame(rafId);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      canvas.remove();
    }
  };
}
