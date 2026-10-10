/**
 * Structure Flow — dark-mode WebGL background for the Cultura dashboard.
 *
 * NOTE: This is an original implementation inspired by the "Structure Flow"
 * field-study description (flowing particle horizon + rising embers). The
 * authored source files referenced by the spec were not available, so this
 * is NOT a copy of that renderer.
 *
 * Runtime: Three.js r160 (ES module from CDN).
 * Passes:  2 point-cloud ShaderMaterial passes (flow field + embers).
 *
 * Lifecycle handled here: resize (ResizeObserver), high-DPI, tab visibility,
 * prefers-reduced-motion, coarse pointer / small screens (lower density),
 * WebGL context loss/restore, and full disposal.
 */
import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';

// --- Palette (raw sRGB, no colour management applied in the shaders) -------
const hexToVec3 = (hex) => {
  const n = parseInt(hex.slice(1), 16);
  return new THREE.Vector3(((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255);
};
const PALETTE_DARK = {
  base: hexToVec3('#3b0764'),   // deep violet valleys
  rose: hexToVec3('#f43f5e'),   // mid-height ridges
  amber: hexToVec3('#fbbf24'),  // peaks
  ember: hexToVec3('#fb923c'),
};
const PALETTE_LIGHT = {
  base: hexToVec3('#4c1d95'),   // much darker violet
  rose: hexToVec3('#9f1239'),   // darker rose
  amber: hexToVec3('#92400e'),  // darker amber
  ember: hexToVec3('#9a3412'),
};

// --- GLSL -----------------------------------------------------------------
// 3D simplex noise — Ashima Arts / Stefan Gustavson (MIT).
const NOISE = /* glsl */ `
vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-0.85373472095314*r;}
float snoise(vec3 v){
  const vec2 C=vec2(1.0/6.0,1.0/3.0);
  const vec4 D=vec4(0.0,0.5,1.0,2.0);
  vec3 i=floor(v+dot(v,C.yyy));
  vec3 x0=v-i+dot(i,C.xxx);
  vec3 g=step(x0.yzx,x0.xyz);
  vec3 l=1.0-g;
  vec3 i1=min(g.xyz,l.zxy);
  vec3 i2=max(g.xyz,l.zxy);
  vec3 x1=x0-i1+C.xxx;
  vec3 x2=x0-i2+C.yyy;
  vec3 x3=x0-D.yyy;
  i=mod289(i);
  vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
  float n_=0.142857142857;
  vec3 ns=n_*D.wyz-D.xzx;
  vec4 j=p-49.0*floor(p*ns.z*ns.z);
  vec4 x_=floor(j*ns.z);
  vec4 y_=floor(j-7.0*x_);
  vec4 x=x_*ns.x+ns.yyyy;
  vec4 y=y_*ns.x+ns.yyyy;
  vec4 h=1.0-abs(x)-abs(y);
  vec4 b0=vec4(x.xy,y.xy);
  vec4 b1=vec4(x.zw,y.zw);
  vec4 s0=floor(b0)*2.0+1.0;
  vec4 s1=floor(b1)*2.0+1.0;
  vec4 sh=-step(h,vec4(0.0));
  vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;
  vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
  vec3 p0=vec3(a0.xy,h.x);
  vec3 p1=vec3(a0.zw,h.y);
  vec3 p2=vec3(a1.xy,h.z);
  vec3 p3=vec3(a1.zw,h.w);
  vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
  p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
  vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0);
  m=m*m;
  return 42.0*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
}
`;

const FIELD_VERT = /* glsl */ `
uniform float uTime;
uniform float uPixelRatio;
uniform float uSize;
uniform vec2  uPointer;          // pointer position on the field plane (x, z)
uniform float uPointerStrength;  // 0..1, rises while the pointer moves
attribute float aSeed;
varying float vHeight;
varying float vDepth;
varying float vGlow;
${NOISE}
void main(){
  vec3 p = position;
  float t = uTime;
  vec2 q = p.xz * 0.045;

  // Layered flow: broad swell + fine detail + a slowly drifting ridge line.
  float swell  = snoise(vec3(q.x - t*0.06, q.y*1.4, t*0.05));
  float detail = snoise(vec3(q*2.3 + vec2(t*0.04, -t*0.03), t*0.11));
  float ridge  = 1.0 - abs(snoise(vec3(q*0.6 + vec2(-t*0.025, 0.0), 3.0 + t*0.02)));
  float h = swell*3.2 + detail*1.0 + ridge*ridge*2.6;

  // Pointer: travelling ripple + soft lift around the cursor.
  vec2  d    = p.xz - uPointer;
  float dist = length(d);
  float ripple = sin(dist*0.55 - t*3.0) * exp(-dist*0.09) * uPointerStrength;
  float lift   = exp(-dist*dist*0.004) * uPointerStrength;
  h += ripple*1.6 + lift*3.0;

  p.y += h;
  vHeight = h;
  vGlow = lift;

  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vDepth = -mv.z;
  gl_Position = projectionMatrix * mv;

  float twinkle = 0.75 + 0.25*sin(t*1.7 + aSeed*40.0);
  gl_PointSize = uSize * uPixelRatio * twinkle * (1.0 + lift*0.8) * (60.0 / max(-mv.z, 1.0));
}
`;

const FIELD_FRAG = /* glsl */ `
uniform vec3  uBase;
uniform vec3  uRose;
uniform vec3  uAmber;
uniform float uFogNear;
uniform float uFogFar;
uniform float uOpacity;
varying float vHeight;
varying float vDepth;
varying float vGlow;
void main(){
  vec2 c = gl_PointCoord - 0.5;
  float r = length(c);
  if (r > 0.5) discard;
  float core = pow(smoothstep(0.5, 0.0, r), 1.6);

  float hN = clamp((vHeight + 2.5) / 8.0, 0.0, 1.0);
  vec3 col = mix(uBase, uRose, smoothstep(0.0, 0.55, hN));
  col = mix(col, uAmber, smoothstep(0.55, 1.0, hN));
  col += vGlow * uRose * 0.5; // use the rose color for a warmer, less wash-out glow

  float fog = 1.0 - smoothstep(uFogNear, uFogFar, vDepth);
  float alpha = core * fog * uOpacity * (0.35 + 0.65*hN) * 1.5; // boost opacity slightly
  gl_FragColor = vec4(col, alpha);
}
`;

const EMBER_VERT = /* glsl */ `
uniform float uTime;
uniform float uPixelRatio;
uniform float uSize;
attribute float aSeed;
attribute float aSpeed;
varying float vLife;
void main(){
  vec3 p = position;
  float span = 26.0;
  float y = mod(p.y + uTime * aSpeed, span);
  vLife = y / span;
  p.y = y - 2.0;
  p.x += sin(uTime*0.4 + aSeed*12.0) * 1.6;
  p.z += cos(uTime*0.3 + aSeed*7.0) * 1.2;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * uPixelRatio * (0.6 + aSeed*0.8) * (40.0 / max(-mv.z, 1.0));
}
`;

const EMBER_FRAG = /* glsl */ `
uniform vec3 uColor;
uniform float uOpacity;
varying float vLife;
void main(){
  float r = length(gl_PointCoord - 0.5);
  if (r > 0.5) discard;
  float core = pow(smoothstep(0.5, 0.0, r), 2.2);
  float fade = smoothstep(0.0, 0.15, vLife) * (1.0 - smoothstep(0.6, 1.0, vLife));
  gl_FragColor = vec4(uColor, core * fade * uOpacity * 1.5); // boost opacity
}
`;

// --- Factory ----------------------------------------------------------------
/**
 * Mounts the Structure Flow background into `container`.
 * @param {HTMLElement} container  Sized, overflow-hidden host element.
 * @param {{speed?: number, density?: number}} [options]
 * @returns {{start(): void, stop(): void, dispose(): void}}
 */
export function createStructureFlow(container, { speed = 1, density = 1 } = {}) {
  const coarse = window.matchMedia('(pointer: coarse)').matches || window.innerWidth < 768;
  const reducedMotionMq = window.matchMedia('(prefers-reduced-motion: reduce)');
  const densityScale = density * (coarse ? 0.5 : 1);

  // Renderer ---------------------------------------------------------------
  const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: 'low-power' });
  renderer.setClearColor(0x000000, 0);
  const canvas = renderer.domElement;
  canvas.setAttribute('aria-hidden', 'true');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;';
  container.appendChild(canvas);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 400);
  const camBase = new THREE.Vector3(0, 9, 34);
  const lookTarget = new THREE.Vector3(0, 1.5, -40);
  camera.position.copy(camBase);
  camera.lookAt(lookTarget);

  // Flow field -------------------------------------------------------------
  const cols = Math.round(260 * Math.sqrt(densityScale));
  const rows = Math.round(160 * Math.sqrt(densityScale));
  const width = 240, depth = 190, zOffset = -75;
  const fieldCount = cols * rows;
  const fieldPos = new Float32Array(fieldCount * 3);
  const fieldSeed = new Float32Array(fieldCount);
  for (let i = 0, k = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++, k++) {
      fieldPos[k * 3] = (j / (cols - 1) - 0.5) * width + (Math.random() - 0.5) * 0.35;
      fieldPos[k * 3 + 1] = 0;
      fieldPos[k * 3 + 2] = (i / (rows - 1) - 0.5) * depth + zOffset + (Math.random() - 0.5) * 0.35;
      fieldSeed[k] = Math.random();
    }
  }
  const fieldGeo = new THREE.BufferGeometry();
  fieldGeo.setAttribute('position', new THREE.BufferAttribute(fieldPos, 3));
  fieldGeo.setAttribute('aSeed', new THREE.BufferAttribute(fieldSeed, 1));

  const fieldMat = new THREE.ShaderMaterial({
    vertexShader: FIELD_VERT,
    fragmentShader: FIELD_FRAG,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uTime: { value: 0 },
      uPixelRatio: { value: 1 },
      uSize: { value: coarse ? 2.6 : 2.2 },
      uPointer: { value: new THREE.Vector2(0, -20) },
      uPointerStrength: { value: 0 },
      uBase: { value: PALETTE_DARK.base.clone() },
      uRose: { value: PALETTE_DARK.rose.clone() },
      uAmber: { value: PALETTE_DARK.amber.clone() },
      uFogNear: { value: 30 },
      uFogFar: { value: 150 },
      uOpacity: { value: 0.9 },
    },
  });
  const field = new THREE.Points(fieldGeo, fieldMat);
  field.frustumCulled = false;
  scene.add(field);

  // Embers -----------------------------------------------------------------
  const emberCount = Math.round(700 * densityScale);
  const emberPos = new Float32Array(emberCount * 3);
  const emberSeed = new Float32Array(emberCount);
  const emberSpeed = new Float32Array(emberCount);
  for (let i = 0; i < emberCount; i++) {
    emberPos[i * 3] = (Math.random() - 0.5) * 120;
    emberPos[i * 3 + 1] = Math.random() * 26;
    emberPos[i * 3 + 2] = -Math.random() * 110 + 10;
    emberSeed[i] = Math.random();
    emberSpeed[i] = 0.6 + Math.random() * 1.4;
  }
  const emberGeo = new THREE.BufferGeometry();
  emberGeo.setAttribute('position', new THREE.BufferAttribute(emberPos, 3));
  emberGeo.setAttribute('aSeed', new THREE.BufferAttribute(emberSeed, 1));
  emberGeo.setAttribute('aSpeed', new THREE.BufferAttribute(emberSpeed, 1));
  const emberMat = new THREE.ShaderMaterial({
    vertexShader: EMBER_VERT,
    fragmentShader: EMBER_FRAG,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uTime: { value: 0 },
      uPixelRatio: { value: 1 },
      uSize: { value: 3.0 },
      uColor: { value: PALETTE_DARK.ember.clone() },
      uOpacity: { value: 0.85 },
    },
  });
  const embers = new THREE.Points(emberGeo, emberMat);
  embers.frustumCulled = false;
  scene.add(embers);

  // Sizing -----------------------------------------------------------------
  const resize = () => {
    const w = Math.max(1, container.clientWidth);
    const h = Math.max(1, container.clientHeight);
    // Native-or-better backing resolution, capped at 2x for fill-rate.
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    renderer.setPixelRatio(dpr);
    renderer.setSize(w, h, false);
    fieldMat.uniforms.uPixelRatio.value = dpr;
    emberMat.uniforms.uPixelRatio.value = dpr;
    camera.aspect = w / h;
    camera.fov = camera.aspect < 0.8 ? 70 : 55; // wider view on portrait/mobile
    camera.updateProjectionMatrix();
    if (running && reducedMotion) renderFrame(0);
  };
  const ro = new ResizeObserver(resize);

  // Pointer ----------------------------------------------------------------
  const ndc = new THREE.Vector2(0, 0);
  const ndcSmooth = new THREE.Vector2(0, 0);
  const raycaster = new THREE.Raycaster();
  const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  const hit = new THREE.Vector3();
  const pointerTarget = new THREE.Vector2(0, -20);
  let pointerEnergy = 0;
  const onPointerMove = (e) => {
    ndc.set((e.clientX / window.innerWidth) * 2 - 1, -(e.clientY / window.innerHeight) * 2 + 1);
    raycaster.setFromCamera(ndc, camera);
    if (raycaster.ray.intersectPlane(plane, hit)) pointerTarget.set(hit.x, hit.z);
    pointerEnergy = 1;
  };

  // Loop -------------------------------------------------------------------
  let running = false;
  let rafId = 0;
  let elapsed = 0;
  let last = 0;
  let reducedMotion = reducedMotionMq.matches;
  let contextLost = false;

  function renderFrame(dt) {
    if (contextLost) return;
    elapsed += dt * speed;
    const u = fieldMat.uniforms;
    u.uTime.value = elapsed;
    emberMat.uniforms.uTime.value = elapsed;

    // Ease pointer + camera parallax.
    const k = Math.min(1, dt * 4);
    u.uPointer.value.lerp(pointerTarget, k);
    pointerEnergy = Math.max(0, pointerEnergy - dt * 0.6);
    u.uPointerStrength.value += (pointerEnergy - u.uPointerStrength.value) * Math.min(1, dt * 3);
    ndcSmooth.lerp(ndc, Math.min(1, dt * 2));
    camera.position.set(camBase.x + ndcSmooth.x * 3, camBase.y + ndcSmooth.y * 1.5, camBase.z);
    camera.lookAt(lookTarget);

    renderer.render(scene, camera);
  }

  function tick(now) {
    rafId = requestAnimationFrame(tick);
    const dt = last ? Math.min((now - last) / 1000, 0.05) : 0.016;
    last = now;
    renderFrame(dt);
  }

  function loopStart() {
    if (rafId || !running || document.hidden || reducedMotion || contextLost) return;
    last = 0;
    rafId = requestAnimationFrame(tick);
  }
  function loopStop() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = 0;
  }

  const onVisibility = () => (document.hidden ? loopStop() : loopStart());
  const onReducedMotion = (e) => {
    reducedMotion = e.matches;
    if (reducedMotion) { loopStop(); renderFrame(0); } else loopStart();
  };
  const onContextLost = (e) => { e.preventDefault(); contextLost = true; loopStop(); };
  const onContextRestored = () => { contextLost = false; resize(); loopStart(); };

  ro.observe(container);
  window.addEventListener('pointermove', onPointerMove, { passive: true });
  document.addEventListener('visibilitychange', onVisibility);
  reducedMotionMq.addEventListener('change', onReducedMotion);
  canvas.addEventListener('webglcontextlost', onContextLost, false);
  canvas.addEventListener('webglcontextrestored', onContextRestored, false);
  resize();

  return {
    start() {
      running = true;
      if (reducedMotion) renderFrame(0); else loopStart();
    },
    stop() {
      running = false;
      loopStop();
    },
    setTheme(isDark) {
      if (isDark) {
        fieldMat.blending = THREE.AdditiveBlending;
        emberMat.blending = THREE.AdditiveBlending;
        fieldMat.uniforms.uBase.value.copy(PALETTE_DARK.base);
        fieldMat.uniforms.uRose.value.copy(PALETTE_DARK.rose);
        fieldMat.uniforms.uAmber.value.copy(PALETTE_DARK.amber);
        emberMat.uniforms.uColor.value.copy(PALETTE_DARK.ember);
      } else {
        fieldMat.blending = THREE.NormalBlending;
        emberMat.blending = THREE.NormalBlending;
        fieldMat.uniforms.uBase.value.copy(PALETTE_LIGHT.base);
        fieldMat.uniforms.uRose.value.copy(PALETTE_LIGHT.rose);
        fieldMat.uniforms.uAmber.value.copy(PALETTE_LIGHT.amber);
        emberMat.uniforms.uColor.value.copy(PALETTE_LIGHT.ember);
      }
      fieldMat.needsUpdate = true;
      emberMat.needsUpdate = true;
      if (running && reducedMotion) renderFrame(0);
    },
    dispose() {
      running = false;
      loopStop();
      ro.disconnect();
      window.removeEventListener('pointermove', onPointerMove);
      document.removeEventListener('visibilitychange', onVisibility);
      reducedMotionMq.removeEventListener('change', onReducedMotion);
      canvas.removeEventListener('webglcontextlost', onContextLost);
      canvas.removeEventListener('webglcontextrestored', onContextRestored);
      fieldGeo.dispose(); fieldMat.dispose();
      emberGeo.dispose(); emberMat.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
    },
  };
}
