/**
 * A person, at the four sizes the product uses.
 *
 * Tinted with the partner's strand colour, which section 4.4 allows in exactly
 * three places — the mark, the match reveal, and participant identity. The
 * avatar and the role chip are one identity unit and take the same colour.
 *
 * 8.3 records why the initials sit on the 900 stop rather than the 800 the
 * design file draws: at 800 the marigold and jade tints measure 4.48:1 and
 * 4.26:1, and the floor is 4.5.
 */

export type AvatarSize = 32 | 36 | 40 | 64;
export type Tone = "1" | "2" | "3" | "none";

const BOX: Record<AvatarSize, string> = {
  32: "avatar-32",
  36: "avatar-36",
  40: "avatar-40",
  64: "avatar-64",
};

// The 64px avatar carries two letters at heading-m; the smaller three take the
// label token. Nothing between, because nothing needs it.
const TYPE: Record<AvatarSize, string> = {
  32: "type-label",
  36: "type-label",
  40: "type-label",
  64: "type-heading-m",
};

/**
 * Which of the three strand colours a person gets. Derived from the
 * participation id rather than from the position in a list, so the same person
 * is the same colour on every screen and a re-sort does not reshuffle the page.
 * Neither the design file nor 8.3 specifies the rule.
 */
export function strandColour(participationId: string): "1" | "2" | "3" {
  let h = 0;
  for (let i = 0; i < participationId.length; i++) {
    h = (h * 31 + participationId.charCodeAt(i)) % 3;
  }
  return String(h + 1) as "1" | "2" | "3";
}

export function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

/**
 * The other half of the identity unit, which is why it lives beside the avatar
 * rather than in a file of its own: the two carry the same person's colour at
 * two depths and are never meant to drift apart.
 */
export function RoleChip({
  tone,
  children,
}: {
  tone: Tone;
  children: React.ReactNode;
}) {
  return (
    <span
      data-strand={tone}
      className="inline-flex shrink-0 items-center rounded-full bg-strand-chip px-8 type-caption text-strand-chip-text"
    >
      {children}
    </span>
  );
}

export function Avatar({
  name,
  participationId,
  size = 40,
  /** Drops the colour. An ended strand keeps the person and loses the tint. */
  neutral = false,
  className = "",
}: {
  name: string;
  participationId: string;
  size?: AvatarSize;
  neutral?: boolean;
  className?: string;
}) {
  return (
    <span
      data-strand={neutral ? "none" : strandColour(participationId)}
      aria-hidden="true"
      className={`${BOX[size]} ${TYPE[size]} inline-flex items-center justify-center rounded-full bg-strand-avatar text-strand-avatar-text ${className}`}
    >
      {initials(name)}
    </span>
  );
}
