import React, {
  Children,
  cloneElement,
  useEffect,
  useState,
  useId,
} from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export function AnimatedBackground({
  children,
  defaultValue,
  onValueChange,
  className,
  transition = {
    type: 'spring',
    bounce: 0.2,
    duration: 0.6,
  },
  enableHover = false,
}) {
  const [activeId, setActiveId] = useState(null);
  const uniqueId = useId();

  const handleSetActiveId = (id) => {
    setActiveId(id);

    if (onValueChange) {
      onValueChange(id);
    }
  };

  useEffect(() => {
    if (defaultValue !== undefined) {
      setActiveId(defaultValue);
    }
  }, [defaultValue]);

  return Children.map(children, (child, index) => {
    if (!React.isValidElement(child)) return child;
    const id = child.props['data-id'] ?? `card-${index}`;

    const interactionProps = enableHover
      ? {
          onMouseEnter: (e) => {
            handleSetActiveId(id);
            child.props.onMouseEnter?.(e);
          },
          onMouseLeave: (e) => {
            handleSetActiveId(null);
            child.props.onMouseLeave?.(e);
          },
        }
      : {
          onClick: (e) => {
            handleSetActiveId(id);
            child.props.onClick?.(e);
          },
        };

    return cloneElement(
      child,
      {
        key: child.key || index,
        className: cn('relative inline-flex', child.props.className),
        'data-checked': activeId === id ? 'true' : 'false',
        ...interactionProps,
      },
      <>
        <AnimatePresence initial={false}>
          {activeId === id && (
            <motion.div
              layoutId={`background-${uniqueId}`}
              className={cn('absolute inset-0 pointer-events-none', className)}
              transition={transition}
              initial={{ opacity: defaultValue ? 1 : 0 }}
              animate={{
                opacity: 1,
              }}
              exit={{
                opacity: 0,
              }}
            />
          )}
        </AnimatePresence>
        <div className="z-10 w-full h-full flex flex-col">{child.props.children}</div>
      </>
    );
  });
}

export function AnimatedCardBackgroundHover() {
  const ITEMS = [
    {
      id: 1,
      title: 'Dialog',
      description: 'Enhances modal presentations.',
    },
    {
      id: 2,
      title: 'Popover',
      description: 'For small interactive overlays.',
    },
    {
      id: 3,
      title: 'Accordion',
      description: 'Collapsible sections for more content.',
    },
    {
      id: 4,
      title: 'Collapsible',
      description: 'Collapsible sections for more content.',
    },
    {
      id: 5,
      title: 'Drag to Reorder',
      description: 'Reorder items with drag and drop.',
    },
    {
      id: 6,
      title: 'Swipe to Delete',
      description: 'Delete items with swipe gestures.',
    },
  ];

  return (
    <div className='grid grid-cols-2 p-10 md:grid-cols-3'>
      <AnimatedBackground
        className='rounded-lg bg-zinc-100 dark:bg-zinc-800'
        transition={{
          type: 'spring',
          bounce: 0.2,
          duration: 0.6,
        }}
        enableHover
      >
        {ITEMS.map((item, index) => (
          <div key={index} data-id={`card-${index}`}>
            <div className='flex select-none flex-col space-y-1 p-4'>
              <h3 className='text-base font-medium text-zinc-800 dark:text-zinc-50'>
                {item.title}
              </h3>
              <p className='text-base text-zinc-600 dark:text-zinc-400'>
                {item.description}
              </p>
            </div>
          </div>
        ))}
      </AnimatedBackground>
    </div>
  );
}

export default AnimatedBackground;
