import React from 'react';

/**
 * AnimatedGradientBackground - A component for the dynamic, interactive background.
 * It's memoized to prevent re-renders on parent state changes.
 */
const AnimatedGradientBackground = React.memo(({ mousePosition }) => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none">
    <div 
      className="absolute w-96 h-96 rounded-full opacity-10 transition-transform duration-500 ease-out will-change-transform"
      style={{
        background: `radial-gradient(circle, rgba(37, 99, 235, 0.3) 0%, transparent_70%)`,
        transform: `translate(${mousePosition.x - 192}px, ${mousePosition.y - 192}px)`,
      }}
    />
    <div className="absolute inset-0 opacity-5">
      <div className="h-full w-full bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]"></div>
    </div>
  </div>
));

AnimatedGradientBackground.displayName = 'AnimatedGradientBackground';

export default AnimatedGradientBackground;



