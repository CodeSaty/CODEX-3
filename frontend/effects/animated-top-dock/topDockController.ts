/**
 * topDockController.ts
 * TypeScript interface and controller for Animated Top Dock
 */

export interface TopDockState {
  element: HTMLElement;
  value: number;
  velocity: number;
  target: number;
  centerX: number;
  centerY: number;
  baseWidth: number;
  baseHeight: number;
  isFocused: boolean;
}

export interface TopDockControllerOptions {
  proximity?: number;
  spring?: number;
  damping?: number;
  vertical?: boolean;
  onPointerChange?: (x: number, y: number, active: boolean) => void;
}

export interface TopDockController {
  measure: () => void;
  setSelected: (idOrIndex: number | string) => void;
  dispose: () => void;
}

export { createTopDockController } from './topDockController.js';
