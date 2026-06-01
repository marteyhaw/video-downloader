import { useLayoutEffect, useState, type RefObject } from "react";

interface Options {
  rootMargin?: string;
  enabled?: boolean;
}

/** True when the target element is not intersecting the viewport. */
export function useIntersectionVisibility(
  targetRef: RefObject<HTMLElement | null>,
  options: Options = {},
): boolean {
  const { rootMargin = "0px", enabled = true } = options;
  const [visible, setVisible] = useState(false);
  const [bindKey, setBindKey] = useState(0);

  useLayoutEffect(() => {
    if (!enabled) {
      setVisible(false);
      return;
    }

    const target = targetRef.current;
    if (!target) {
      setVisible(false);
      const id = requestAnimationFrame(() => setBindKey((k) => k + 1));
      return () => cancelAnimationFrame(id);
    }

    const observer = new IntersectionObserver(([entry]) => setVisible(!entry.isIntersecting), {
      threshold: 0,
      rootMargin,
    });
    observer.observe(target);
    return () => observer.disconnect();
  }, [enabled, rootMargin, targetRef, bindKey]);

  return visible;
}
