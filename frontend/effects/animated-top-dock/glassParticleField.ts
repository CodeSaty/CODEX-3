/**
 * glassParticleField.ts
 * TypeScript export for Three.js r128 refracting glass particle rail pass
 */

export interface GlassParticleField {
  start: () => void;
  stop: () => void;
  resize: () => void;
  updatePointer: (x: number, y: number, active?: boolean) => void;
  dispose: () => void;
}

export { createGlassParticleField } from './glassParticleField.js';
