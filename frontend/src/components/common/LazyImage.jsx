import React, { useState } from 'react';

/**
 * LazyImage Component
 * Prevents harsh flashing with smooth fade-in transitions and skeleton placeholder.
 */
export const LazyImage = ({
  src,
  alt = '',
  className = '',
  aspectRatio = 'aspect-[16/10]',
  loading = 'lazy',
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  return (
    <div className={`relative overflow-hidden ${aspectRatio} bg-surface-elevated ${className}`}>
      {/* Skeleton Shimmer Background while loading */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 skeleton-shimmer z-0" />
      )}

      {/* Fallback if error */}
      {hasError ? (
        <div className="absolute inset-0 flex items-center justify-center text-text-muted text-xs bg-surface-elevated">
          <span>Image unavailable</span>
        </div>
      ) : (
        <img
          src={src}
          alt={alt}
          loading={loading}
          onLoad={() => setIsLoaded(true)}
          onError={() => setHasError(true)}
          className={`w-full h-full object-cover transition-opacity duration-350 ease-smooth ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          {...props}
        />
      )}
    </div>
  );
};

export default LazyImage;
