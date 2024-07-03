// components/AnimatedLoadingDots.tsx
import React from 'react';

const AnimatedLoadingDots: React.FC = () => {
  return (
    <div className="flex items-center space-x-1">
      {[0, 1, 2].map((index) => (
        <div
          key={index}
          className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: `${index * 0.15}s` }}
        ></div>
      ))}
    </div>
  );
};

export default AnimatedLoadingDots;