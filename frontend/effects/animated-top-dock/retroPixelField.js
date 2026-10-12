/**
 * retroPixelField.js
 * WebGL CRT Phosphor Sub-pixel Matrix & Scanline Pass
 * Used by the Retro fit of the Animated Top Dock.
 */

const VERTEX_SHADER = `
attribute vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const FRAGMENT_SHADER = `
precision highp float;
uniform vec2 uResolution;
uniform float uTime;
uniform vec2 uPointer;
uniform float uPointerActive;

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution;
  
  // CRT scanlines
  float scanline = sin(gl_FragCoord.y * 1.5) * 0.12 + 0.88;
  
  // Sub-pixel phosphor dot-matrix grid (4px cells)
  vec2 gridCoord = mod(gl_FragCoord.xy, 5.0) - vec2(2.5);
  float dotMask = 1.0 - smoothstep(0.8, 2.0, length(gridCoord));
  
  // Subtle amber/emerald phosphor matrix color
  vec3 baseColor = vec3(0.04, 0.72, 0.42);
  
  // Drift pulse
  float pulse = 0.85 + 0.15 * sin(uTime * 2.5 + uv.x * 6.0);
  
  // Pointer proximity glow
  float pDist = length(gl_FragCoord.xy - uPointer);
  float pointerGlow = exp(-pDist * 0.035) * uPointerActive;
  
  vec3 finalColor = baseColor * dotMask * scanline * pulse;
  finalColor += vec3(0.12, 0.95, 0.55) * pointerGlow * 0.7;
  
  float alpha = (dotMask * 0.28 + pointerGlow * 0.35) * scanline;
  gl_FragColor = vec4(finalColor, clamp(alpha, 0.0, 0.85));
}
`;

export function createRetroPixelField(container) {
  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none;border-radius:inherit;';
  container.appendChild(canvas);

  const gl = canvas.getContext('webgl', { alpha: true, antialias: false, powerPreference: 'low-power' });
  if (!gl) {
    console.warn('[retroPixelField] WebGL not available, skipping retro shader pass.');
    return { resize() {}, updatePointer() {}, render() {}, dispose() { canvas.remove(); } };
  }

  // Compile shaders
  function createShader(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    return s;
  }

  const prog = gl.createProgram();
  gl.attachShader(prog, createShader(gl.VERTEX_SHADER, VERTEX_SHADER));
  gl.attachShader(prog, createShader(gl.FRAGMENT_SHADER, FRAGMENT_SHADER));
  gl.linkProgram(prog);

  const posBuf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);

  const posAttr = gl.getAttribLocation(prog, 'position');
  const uResLoc = gl.getUniformLocation(prog, 'uResolution');
  const uTimeLoc = gl.getUniformLocation(prog, 'uTime');
  const uPointerLoc = gl.getUniformLocation(prog, 'uPointer');
  const uPointerActiveLoc = gl.getUniformLocation(prog, 'uPointerActive');

  let width = 1, height = 1;
  let dpr = 1;
  let pointerX = -999, pointerY = -999;
  let pointerActive = 0;
  let running = false;
  let rafId = 0;
  let startTime = performance.now();

  function resize() {
    width = Math.max(1, container.clientWidth);
    height = Math.max(1, container.clientHeight);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    gl.viewport(0, 0, canvas.width, canvas.height);
  }

  function updatePointer(x, y, active = true) {
    const rect = canvas.getBoundingClientRect();
    pointerX = (x - rect.left) * dpr;
    pointerY = (rect.bottom - y) * dpr; // WebGL flip Y
    pointerActive = active ? 1 : 0;
  }

  function frame(now) {
    if (!running) return;
    rafId = requestAnimationFrame(frame);
    const time = (now - startTime) / 1000;

    gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
    gl.enableVertexAttribArray(posAttr);
    gl.vertexAttribPointer(posAttr, 2, gl.FLOAT, false, 0, 0);

    gl.uniform2f(uResLoc, canvas.width, canvas.height);
    gl.uniform1f(uTimeLoc, time);
    gl.uniform2f(uPointerLoc, pointerX, pointerY);
    gl.uniform1f(uPointerActiveLoc, pointerActive);

    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
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
      if (gl) {
        gl.deleteBuffer(posBuf);
        gl.deleteProgram(prog);
      }
      canvas.remove();
    }
  };
}
