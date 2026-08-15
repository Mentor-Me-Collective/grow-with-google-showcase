import { WeaveMark } from "@/components/brand/weave-mark";

/**
 * 8.5: the mark at 48px in border-default, a line, one sentence saying what
 * will fill this space and when, and either one action or nothing at all.
 * Never an illustration of a person, never a shrug, never "Nothing here yet."
 *
 * The reference copy from 8.5, which does three things at once — sets a date,
 * shows the person they are already part of something populated, and gives
 * one useful action:
 *
 *   Matching opens 14 September. Twelve mentors have joined so far. Finish
 *   your profile before then and you'll be included in the first round.
 *
 * `emphasis="display"` is the only route to the display face here. Section 5.2
 * allows it in exactly five places, and the only empty state among them is
 * Home before matching.
 */
export function EmptyState({
  title,
  body,
  action,
  emphasis = "default",
  markId = "empty-state-mark",
}: {
  title: string;
  body?: string;
  action?: React.ReactNode;
  emphasis?: "default" | "display";
  markId?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-16 px-16 py-48 text-center">
      <span className="text-default">
        <WeaveMark size={48} mono id={markId} title={null} />
      </span>

      <div className="flex max-w-public flex-col gap-8">
        <p
          className={
            emphasis === "display"
              ? "type-display-l text-primary"
              : "type-heading-m text-primary"
          }
        >
          {title}
        </p>
        {body && <p className="type-body-m text-secondary">{body}</p>}
      </div>

      {action}
    </div>
  );
}
