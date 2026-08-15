type IconProps = { className?: string };

function Svg({ className, children }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      {children}
    </svg>
  );
}

export function HomeIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5.5 9.5V20h13V9.5" />
    </Svg>
  );
}

/** Two strands crossing once — the mark's gesture, reduced to a line icon. */
export function StrandsIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M7 4c0 6 10 10 10 16" />
      <path d="M17 4c0 6-10 10-10 16" />
    </Svg>
  );
}

export function DirectoryIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="9" cy="8.5" r="3.25" />
      <path d="M3.5 20c0-3 2.5-5 5.5-5s5.5 2 5.5 5" />
      <path d="M16 6.5a3 3 0 0 1 0 5.5" />
      <path d="M17.5 15c1.9.5 3 2.2 3 5" />
    </Svg>
  );
}

export function ResourcesIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H11v16H5.5A1.5 1.5 0 0 1 4 18.5Z" />
      <path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H13v16h5.5a1.5 1.5 0 0 0 1.5-1.5Z" />
    </Svg>
  );
}

export function ProfileIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20c0-3.3 3.1-5.5 7-5.5s7 2.2 7 5.5" />
    </Svg>
  );
}

export function ChevronDownIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="m6 9.5 6 5.5 6-5.5" />
    </Svg>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="m5 12.5 4.5 4.5L19 7" />
    </Svg>
  );
}

export function MenuIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </Svg>
  );
}

export function SignOutIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M14 4h4.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5H14" />
      <path d="M9 8.5 5 12l4 3.5" />
      <path d="M5 12h10" />
    </Svg>
  );
}

/** 12px in field errors, per 8.2. Sized by the caller. */
export function AlertIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.75v5" />
      <path d="M12 16.25h.01" />
    </Svg>
  );
}

/** Sort direction on a table header. Points the way a click would order. */
export function SortIcon({
  direction,
  className,
}: IconProps & { direction: "asc" | "desc" }) {
  return (
    <Svg className={className}>
      {direction === "asc" ? (
        <path d="M12 19V5m0 0-5 5m5-5 5 5" />
      ) : (
        <path d="M12 5v14m0 0 5-5m-5 5-5-5" />
      )}
    </Svg>
  );
}
