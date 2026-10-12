/**
 * retroPixelField.ts
 * TypeScript export for WebGL CRT phosphor retro pixel field pass
 */

export interface RetroPixelField {
  start: () => void;
  stop: () => void;
  resize: () => void;
  updatePointer: (x: number, y: number, active?: boolean) => void;
  dispose: () => void;
}

export { createRetroPixelField } from './retroPixelField.js';
