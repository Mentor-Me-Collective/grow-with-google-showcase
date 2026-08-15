import type { components } from "@/lib/api/types";
import { Avatar, RoleChip, strandColour, type Tone } from "@/components/ui/avatar";

type S = components["schemas"];

const shortDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  }).format(new Date(iso));

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/**
 * Design direction 9: "the why you were matched line sits directly under the
 * partner's name in body-s, always visible, never behind a disclosure.
 * Participants should not have to hunt for the reason they are talking to this
 * person."
 *
 * Architecture 4.7 lists more facts than the contract carries. What is here is
 * what a `StrandMember` actually has; years in the field and meeting cadence
 * are answers to form questions and belong with the profile work.
 */
export function PartnerCard({
  strand,
  others,
}: {
  strand: S["Strand"];
  others: S["StrandMember"][];
}) {
  const isGroup = others.length > 1;
  const partner = others[0];
  if (!partner) return null;

  const tone: Tone = isGroup ? "none" : strandColour(partner.participationId);

  return (
    <div className="flex flex-col gap-16 rounded-lg border border-subtle bg-surface p-24">
      <div className="flex items-start gap-16">
        {isGroup ? (
          <span className="flex shrink-0 items-center">
            {others.slice(0, 3).map((m, i) => (
              <span
                key={m.participationId}
                className={i === 0 ? "" : "-ml-16 rounded-full outline-2 outline-surface"}
              >
                <Avatar name={m.name} participationId={m.participationId} size={40} />
              </span>
            ))}
          </span>
        ) : (
          <Avatar
            name={partner.name}
            participationId={partner.participationId}
            size={64}
          />
        )}

        <div className="flex min-w-0 flex-col gap-8">
          <div className="flex flex-col gap-4">
            <h2 className="type-heading-m text-primary">
              {isGroup ? others.map((m) => m.name).join(", ") : partner.name}
            </h2>
            {strand.matchRationale && (
              <p className="type-body-s text-secondary">{strand.matchRationale}</p>
            )}
          </div>
          <span className="flex">
            <RoleChip tone={tone}>
              {isGroup ? `Group of ${others.length + 1}` : capitalise(partner.role)}
            </RoleChip>
          </span>
        </div>
      </div>

      <hr className="border-t border-subtle" />

      <dl className="flex flex-col gap-12">
        {!isGroup && partner.headline && (
          <Row label="Works on" value={partner.headline} />
        )}
        {!isGroup && partner.timezone && (
          <Row label="Time zone" value={partner.timezone.replace("_", " ")} />
        )}
        {!isGroup && (partner.skills?.length ?? 0) > 0 && (
          <Row label="Works with" value={partner.skills!.join(", ")} />
        )}
        <Row label="Strand started" value={shortDate(strand.createdAt)} numeric />
        {strand.endedAt && (
          <Row label="Ended" value={shortDate(strand.endedAt)} numeric />
        )}
      </dl>

      {isGroup && (
        <>
          <hr className="border-t border-subtle" />
          <ul className="flex flex-col gap-12">
            {others.map((m) => (
              <li key={m.participationId} className="flex items-center gap-12">
                <Avatar name={m.name} participationId={m.participationId} size={32} />
                <span className="min-w-0 flex-1 truncate type-body-m text-primary">
                  {m.name}
                </span>
                <RoleChip tone={strandColour(m.participationId)}>
                  {capitalise(m.role)}
                </RoleChip>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function Row({
  label,
  value,
  numeric = false,
}: {
  label: string;
  value: string;
  numeric?: boolean;
}) {
  return (
    <div className="flex justify-between gap-16">
      <dt className="shrink-0 type-body-s text-muted">{label}</dt>
      <dd className={`text-right text-primary ${numeric ? "type-data-m" : "type-body-s"}`}>
        {value}
      </dd>
    </div>
  );
}
