import { useState, useEffect } from 'react';

/**
 * useMousePosition - A hook that tracks mouse position within a container
 * @param {React.RefObject} containerRef - Reference to the container element
 * @returns {Object} - Object containing x and y coordinates
 */
export function useMousePosition(containerRef) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    let animationFrameId;
    
    const handleMouseMove = (e) => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      
      animationFrameId = requestAnimationFrame(() => {
        if (containerRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          setMousePosition({ 
            x: e.clientX - rect.left, 
            y: e.clientY - rect.top 
          });
        }
      });
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('mousemove', handleMouseMove, { passive: true });
    }

    return () => {
      if (container) {
        container.removeEventListener('mousemove', handleMouseMove);
      }
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [containerRef]);

  return mousePosition;
}

