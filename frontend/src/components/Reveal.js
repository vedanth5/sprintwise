import React, { useEffect, useRef, useState } from 'react';

/**
 * Reveal Component
 * Uses Intersection Observer to add a 'reveal-visible' class when the element
 * enters the viewport.
 * 
 * Props:
 * @param {React.ReactNode} children - Elements to be revealed
 * @param {string} effect - Animation type ('slide-up', 'slide-in-left', etc.)
 * @param {number} delay - Delay in ms before animation starts
 * @param {number} threshold - 0 to 1, how much of element must be visible
 */
const Reveal = ({ 
  children, 
  effect = 'slide-up', 
  delay = 0, 
  threshold = 0.1,
  width = 'fit-content'
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          // Once visible, we can stop observing if we only want one-time animation
          if (ref.current) observer.unobserve(ref.current);
        }
      },
      { threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [threshold]);

  return (
    <div
      ref={ref}
      className={`reveal-init reveal-${effect} ${isVisible ? 'reveal-visible' : ''}`}
      style={{ 
        width,
        transitionDelay: `${delay}ms` 
      }}
    >
      {children}
    </div>
  );
};

export default Reveal;
