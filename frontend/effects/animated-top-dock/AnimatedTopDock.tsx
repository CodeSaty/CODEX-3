/**
 * AnimatedTopDock.tsx
 * TypeScript / React Component wrapper for Sable Animated Top Dock
 */

import React, { useEffect, useRef } from 'react';
import { createAnimatedTopDock, DEFAULT_DOCK_ITEMS } from './AnimatedTopDock.js';

export interface DockItem {
  id: string;
  label: string;
  href?: string;
  icon?: string;
  description?: string;
}

export interface AnimatedTopDockProps {
  fit?: 'centred' | 'sable' | 'modern' | 'retro' | 'glass' | 'vertical';
  proximity?: number;
  spring?: number;
  damping?: number;
  items?: DockItem[];
  activeItem?: number | string;
  onItemClick?: (item: DockItem, index: number) => void;
  className?: string;
}

export const AnimatedTopDock: React.FC<AnimatedTopDockProps> = ({
  fit = 'centred',
  proximity = 122,
  spring = 0.19,
  damping = 0.70,
  items = DEFAULT_DOCK_ITEMS,
  activeItem = 0,
  onItemClick,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<ReturnType<typeof createAnimatedTopDock> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    instanceRef.current = createAnimatedTopDock(containerRef.current, {
      fit,
      proximity,
      spring,
      damping,
      items,
      activeItem,
      onItemClick,
    });

    return () => {
      if (instanceRef.current) {
        instanceRef.current.dispose();
        instanceRef.current = null;
      }
    };
  }, [fit, proximity, spring, damping, items]);

  return (
    <div ref={containerRef} className={`animated-top-dock-wrapper ${className}`} />
  );
};

export default AnimatedTopDock;
