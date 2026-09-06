import Link from "next/link";
import { WeaveMark } from "@/components/brand/weave-mark";

/**
 * The public header, and the only chrome any public route gets.
 *
 * Landing and apply only, per architecture 7. The rest of the public routes
 * stay bare: someone on /verify is one click from being signed in and does not
 * need a way out of it. Someone arriving on the landing page from a WhatsApp
 * link needs to know who is asking and needs a door if they already have an
 * account.
 *
 * Full bleed rather than inside the 720 column, because it is chrome. The
 * content under it is what stays at 720.
 */
export function PublicHeader({ right }: { right?: React.ReactNode }) {
  return (
    <header className="flex h-header-sm items-center justify-between gap-16 border-b border-subtle px-16 md:h-header md:px-32">
      <Link
        href="/"
        aria-label="Braid, home"
        className="flex items-center rounded-sm outline-focus outline-offset-2 focus-visible:outline-2"
      >
        <WeaveMark size={32} id="public-mark" title={null} />
        {/* 5.2 place five is the landing page. The wordmark is the identity,
            not a heading, so it is a span and not an h1. */}
        <span className="wordmark text-primary">Braid</span>
      </Link>
      {right}
    </header>
  );
}

/** The 720 column every public route reads in. */
export function PublicMain({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <main className={`mx-auto w-full max-w-public flex-1 px-16 py-48 ${className}`}>
      {children}
    </main>
  );
}

export function PublicFooter({ children }: { children?: React.ReactNode }) {
  return (
    <footer className="border-t border-subtle px-16 py-24 md:px-32">
      <div className="mx-auto flex w-full max-w-public flex-wrap gap-x-32 gap-y-8 type-body-s text-muted">
        {children ?? "Braid"}
      </div>
    </footer>
  );
}
