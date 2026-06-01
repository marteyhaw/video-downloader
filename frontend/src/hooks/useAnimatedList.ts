import autoAnimate from "@formkit/auto-animate";
import { useLayoutEffect, useRef } from "react";

/**
 * Attaches @formkit/auto-animate to a container ref.
 *
 * auto-animate only animates **direct children** of the observed element. Use one
 * hook instance per container whose children should move (e.g. nested layout:
 * outer wrapper for a chip row, inner wrapper for list items).
 *
 * `scanKey` re-inits the controller when scan results change. Filter-driven
 * add/remove should rely on DOM mutations without changing the key.
 */
export function useAnimatedList(scanKey: string) {
  const ref = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    const controller = autoAnimate(el, {
      duration: 350,
      easing: "ease-in-out",
    });
    return () => {
      controller.destroy?.();
    };
  }, [scanKey]);

  return ref;
}
