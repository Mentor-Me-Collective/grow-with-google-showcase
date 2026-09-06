/**
 * Four bars in strict alternating over-under, per design-direction 3.1. The
 * alternation needs masks: z-order alone cannot weave, because the top bar has
 * to sit over one vertical and under the other.
 *
 * `id` scopes the mask definitions. Two marks in one document need two ids.
 */
export function WeaveMark({
  size = 96,
  mono = false,
  id = "braid-mark",
  title = "Braid",
}: {
  size?: number;
  mono?: boolean;
  id?: string;
  /** Pass null where a heading already names the thing, e.g. an empty state. */
  title?: string | null;
}) {
  // Below 20px the bars thicken so the weave survives as a favicon (3.1).
  const thickness = size < 20 ? 18 : 16;
  const half = thickness / 2;
  const leftX = 45 - half;
  const rightX = 85 - half;

  // Mono widens the cut so the gap still reads once the colours are gone.
  const gap = mono ? 3 : 0;
  const cutWidth = thickness + gap * 2;

  const top = mono ? "currentColor" : "var(--strand-1)";
  const bottom = mono ? "currentColor" : "var(--strand-3)";
  const left = mono ? "currentColor" : "var(--strand-2)";
  const right = mono ? "currentColor" : "var(--text-primary)";

  return (
    <svg
      viewBox="0 0 140 140"
      width={size}
      height={size}
      {...(title === null
        ? { "aria-hidden": true as const }
        : { role: "img", "aria-label": title })}
      style={{ display: "block", overflow: "visible" }}
    >
      <defs>
        <mask id={`${id}-top`} maskUnits="userSpaceOnUse" x="0" y="0" width="140" height="140">
          <rect x="0" y="0" width="140" height="140" fill="white" />
          <rect x={leftX - gap} y="30" width={cutWidth} height="30" fill="black" />
        </mask>
        <mask id={`${id}-bottom`} maskUnits="userSpaceOnUse" x="0" y="0" width="140" height="140">
          <rect x="0" y="0" width="140" height="140" fill="white" />
          <rect x={rightX - gap} y="70" width={cutWidth} height="30" fill="black" />
        </mask>
      </defs>

      <rect x={leftX} y="20" width={thickness} height="100" rx={half} fill={left} />
      <rect x={rightX} y="20" width={thickness} height="100" rx={half} fill={right} />
      <rect
        x="20"
        y={leftX}
        width="100"
        height={thickness}
        rx={half}
        fill={top}
        mask={`url(#${id}-top)`}
      />
      <rect
        x="20"
        y={rightX}
        width="100"
        height={thickness}
        rx={half}
        fill={bottom}
        mask={`url(#${id}-bottom)`}
      />
    </svg>
  );
}
