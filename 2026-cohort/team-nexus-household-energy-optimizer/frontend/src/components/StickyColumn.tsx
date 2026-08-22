import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

interface StickyColumnProps {
  gap?: number;
  breakpoint?: number;
  /** Bump this (e.g. appliances.length) when content that changes the column's height changes. */
  watch?: unknown;
  children: ReactNode;
}

/**
 * A sticky sidebar that works the same at every accessibility text-size
 * setting. Native CSS position:sticky renders inconsistently when an
 * ancestor uses the `zoom` property (how the text-size control scales the
 * page - see .top-bar in App.css), so this portals the content out of the
 * zoomed ancestor while stuck and repositions it with plain screen-pixel
 * math (getBoundingClientRect always reports real screen pixels, zoom or
 * not). To keep the portaled content visually the right size, it's wrapped
 * in a `transform: scale()` rather than re-applying `zoom` directly: zoom
 * turned out to also scale the element's *own* top/left/offsetHeight when
 * applied to a position:fixed element, which is exactly the kind of
 * position/zoom inconsistency this was meant to avoid - transform has
 * well-defined semantics (it doesn't affect layout or the transformed
 * element's own positioning), so no compensation math is needed.
 *
 * Bounds are measured against the grid row (outer's parent), not outer
 * itself: outer's own box is only as tall as its content, and once that
 * content is portaled away while stuck, outer's box is no longer a
 * trustworthy measurement. The row's height is set by the other, taller
 * column and is never touched by anything this component does.
 *
 * Deliberately not using a ResizeObserver: this component's own state
 * changes resize the elements it would be watching, which is a feedback
 * loop by construction. Scroll/resize events aren't affected by this
 * component's own DOM writes, so they're the only triggers used.
 */
export function StickyColumn({ gap = 20, breakpoint = 860, watch, children }: StickyColumnProps) {
  const outerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const stuckRef = useRef(false);
  const zoomFactorRef = useRef(1);
  const [stuck, setStuck] = useState(false);
  const [box, setBox] = useState({ top: 0, left: 0, width: 0 });
  const [zoomFactor, setZoomFactor] = useState(1);

  useEffect(() => {
    let frame = 0;

    function measure() {
      const outer = outerRef.current;
      const inner = innerRef.current;
      const container = outer?.parentElement;
      if (!outer || !inner || !container) return;

      if (window.innerWidth <= breakpoint) {
        stuckRef.current = false;
        setStuck(false);
        return;
      }

      // .top-bar drops its own position:sticky at non-default text sizes (see
      // App.css), so it scrolls away like ordinary content there - measuring
      // its live position would go nonsensical once scrolled past it. Only
      // reserve space for it when it's actually pinned in place.
      const topBar = document.querySelector<HTMLElement>(".top-bar");
      const topBarPinned = topBar ? getComputedStyle(topBar).position === "sticky" : false;
      const topOffset = (topBarPinned && topBar ? topBar.getBoundingClientRect().height : 0) + gap;

      const containerRect = container.getBoundingClientRect();
      const outerRect = outer.getBoundingClientRect(); // left/width - column track sizing, unaffected by stuck state

      // transform:scale doesn't affect layout, so inner.offsetHeight is
      // always its true CURRENT content height - just in different units
      // depending on state: while stuck it's pre-scale (natural) since the
      // transform wrapper isn't counted, so scale it back up to real screen
      // pixels. No caching needed (and caching this once caused its own
      // bug: content that changes size *while already stuck*, like the
      // mini score card appearing mid-scroll, went stale forever and let
      // the column overflow past where it should have stopped).
      const innerHeight = stuckRef.current ? inner.offsetHeight * zoomFactorRef.current : inner.offsetHeight;

      if (innerHeight >= containerRect.height || containerRect.top > topOffset) {
        stuckRef.current = false;
        setStuck(false);
        return;
      }

      const maxTop = containerRect.top + containerRect.height - innerHeight;
      const zoomValue = Number.parseFloat(
        getComputedStyle(document.documentElement).getPropertyValue("--a11y-zoom"),
      );
      const nextZoomFactor = Number.isFinite(zoomValue) && zoomValue > 0 ? zoomValue : 1;

      stuckRef.current = true;
      zoomFactorRef.current = nextZoomFactor;
      setZoomFactor(nextZoomFactor);
      setBox({ top: Math.min(topOffset, maxTop), left: outerRect.left, width: outerRect.width });
      setStuck(true);
    }

    function onScrollOrResize() {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(measure);
    }

    measure();
    window.addEventListener("scroll", onScrollOrResize, { passive: true });
    window.addEventListener("resize", onScrollOrResize);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScrollOrResize);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [gap, breakpoint, watch]);

  const contentDiv = (
    <div ref={innerRef} className="sticky-column-inner">
      {children}
    </div>
  );

  return (
    <div ref={outerRef} className="sticky-column-outer">
      {stuck
        ? createPortal(
            <div style={{ position: "fixed", top: box.top, left: box.left }}>
              <div style={{ transform: `scale(${zoomFactor})`, transformOrigin: "top left", width: box.width / zoomFactor }}>
                {contentDiv}
              </div>
            </div>,
            document.body,
          )
        : contentDiv}
    </div>
  );
}
