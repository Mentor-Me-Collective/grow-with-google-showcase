"use client";

import { useRouter } from "next/navigation";
import { useRef, useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Field, TextareaField } from "@/components/ui/input";
import {
  insertAtCursor,
  resolveMergeCodes,
  unknownMergeCodes,
} from "@/lib/comms/merge-codes";
import { sendBroadcast } from "./actions";

type Segment = Schemas["BroadcastSegment"];

const SEGMENT_LABEL: Record<Segment, string> = {
  everyone: "Everyone",
  mentors: "Mentors",
  mentees: "Mentees",
  unmatched: "Unmatched",
  quiet_strands: "People in quiet strands",
  incomplete_profiles: "Incomplete profiles",
};

/** Names the recipients, so the confirmation reads as a sentence rather than
 *  gluing a segment key into one: "24 people", not "24 people in everyone". */
const SEGMENT_NOUN: Record<Segment, (n: number) => string> = {
  everyone: (n) => (n === 1 ? "person" : "people"),
  mentors: (n) => (n === 1 ? "mentor" : "mentors"),
  mentees: (n) => (n === 1 ? "mentee" : "mentees"),
  unmatched: (n) => (n === 1 ? "unmatched person" : "unmatched people"),
  quiet_strands: (n) =>
    n === 1 ? "person in a quiet strand" : "people in quiet strands",
  incomplete_profiles: (n) =>
    n === 1 ? "person with an unfinished profile" : "people with unfinished profiles",
};

const dateTime = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
});

export function BroadcastComposer({
  listing,
  templates,
  programId,
}: {
  listing: Schemas["BroadcastListing"];
  templates: Schemas["MessageTemplate"][];
  programId: string;
}) {
  const router = useRouter();
  const [segment, setSegment] = useState<Segment>("everyone");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [scheduled, setScheduled] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | undefined>();
  const [notice, setNotice] = useState<string | undefined>();
  const bodyRef = useRef<HTMLTextAreaElement>(null);

  const codes = listing.mergeCodes;
  const recipients =
    listing.segments.find((s) => s.segment === segment)?.count ?? 0;
  const unknown = unknownMergeCodes(`${subject} ${body}`, codes);
  const ready = subject.trim() && body.trim() && recipients > 0 && unknown.length === 0;

  const insert = (code: string) => {
    const { text, caret } = insertAtCursor(bodyRef.current, body, code);
    setBody(text);
    requestAnimationFrame(() => {
      bodyRef.current?.focus();
      bodyRef.current?.setSelectionRange(caret, caret);
    });
  };

  const send = () =>
    startTransition(async () => {
      const result = await sendBroadcast({
        programId,
        segment,
        subject,
        body,
        scheduledFor: scheduled ? new Date(scheduled).toISOString() : null,
      });
      setConfirming(false);
      if (result.ok) {
        setError(undefined);
        setNotice(
          result.broadcast.state === "scheduled"
            ? `Scheduled for ${dateTime.format(new Date(result.broadcast.scheduledFor!))}.`
            : `Sent to ${result.broadcast.recipientCount} people.`,
        );
        setSubject("");
        setBody("");
        setScheduled("");
        router.refresh();
      } else {
        setError(result.message);
        setNotice(undefined);
      }
    });

  return (
    <div className="flex flex-col gap-32">
      <section className="flex flex-col gap-24">
        <h2 className="type-heading-m text-primary">Write a message</h2>

        <fieldset className="flex flex-col gap-12">
          <legend className="mb-8 type-label text-primary">Who it goes to</legend>
          <div className="flex flex-wrap gap-8">
            {listing.segments.map((s) => {
              const active = s.segment === segment;
              return (
                <label
                  key={s.segment}
                  className={[
                    "pointer-coarse:min-h-field inline-flex cursor-pointer items-center gap-8 rounded-sm px-12 py-8 type-body-s",
                    "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-focus",
                    active
                      ? "bg-accent text-on-accent"
                      : "border border-default text-secondary",
                    // A segment with nobody in it cannot be written to, and the
                    // count says why rather than the control just refusing.
                    s.count === 0 ? "opacity-60" : "",
                  ].join(" ")}
                >
                  <input
                    type="radio"
                    name="segment"
                    className="sr-only"
                    checked={active}
                    onChange={() => setSegment(s.segment)}
                  />
                  {SEGMENT_LABEL[s.segment]}
                  <span className="type-data-m">{s.count}</span>
                </label>
              );
            })}
          </div>
          <p className="type-body-s text-secondary" role="status">
            {recipients === 0
              ? "Nobody is in that group right now, so there is nobody to write to."
              : `This goes to ${recipients} ${recipients === 1 ? "person" : "people"}.`}
          </p>
        </fieldset>

        {templates.length > 0 && (
          <div className="flex flex-col gap-8">
            <h3 className="type-label text-muted">Start from a template</h3>
            <div className="flex flex-wrap gap-8">
              {templates.map((t) => (
                <Button
                  key={t.kind}
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setSubject(t.subject);
                    setBody(t.body);
                  }}
                >
                  {t.kind.replace(/_/g, " ")}
                </Button>
              ))}
            </div>
          </div>
        )}

        <Field
          label="Subject"
          value={subject}
          mark="none"
          onChange={(e) => setSubject(e.target.value)}
        />

        <TextareaField
          ref={bodyRef}
          label="Message"
          value={body}
          rows={10}
          mark="none"
          onChange={(e) => setBody(e.target.value)}
          helper="Codes in braces are replaced for each person when it sends."
        />

        <div className="flex flex-col gap-8">
          <h3 className="type-label text-muted">Insert a code</h3>
          <div className="flex flex-wrap gap-8">
            {codes.map((code) => (
              <Button
                key={code.code}
                size="sm"
                variant="secondary"
                onClick={() => insert(code.code)}
                title={code.description}
              >
                {code.code}
              </Button>
            ))}
          </div>
        </div>

        <section className="flex flex-col gap-12 rounded-lg border border-subtle bg-sunken p-24">
          <h3 className="type-label text-muted">
            Preview, as one person will read it
          </h3>
          <p className="type-heading-s text-primary">
            {resolveMergeCodes(subject, codes) || "No subject yet"}
          </p>
          <p className="whitespace-pre-wrap type-body-m text-secondary">
            {resolveMergeCodes(body, codes) || "Nothing written yet."}
          </p>
          {unknown.length > 0 && (
            <p role="alert" className="type-body-s text-danger">
              There is no code called {`{${unknown[0]}}`}. It would be sent as
              written.
            </p>
          )}
        </section>

        <Field
          label="Send later"
          type="datetime-local"
          value={scheduled}
          mark="none"
          onChange={(e) => setScheduled(e.target.value)}
          helper="Leave empty to send as soon as you confirm."
        />

        {error && (
          <p role="alert" className="type-body-m text-danger">
            {error}
          </p>
        )}
        {notice && (
          <p role="status" className="type-body-m text-secondary">
            {notice}
          </p>
        )}

        <div className="flex">
          <Button
            size="lg"
            disabled={!ready}
            onClick={() => setConfirming(true)}
          >
            {scheduled ? "Schedule it" : "Send it"}
          </Button>
        </div>
      </section>

      <History items={listing.items} />

      <ConfirmDialog
        open={confirming}
        title={scheduled ? "Schedule this message?" : `Send to ${recipients}?`}
        confirmLabel={scheduled ? "Schedule it" : "Send it"}
        busy={pending}
        busyLabel={scheduled ? "Scheduling" : "Sending"}
        onCancel={() => setConfirming(false)}
        onConfirm={send}
        body={
          <div className="flex flex-col gap-12">
            <p>
              {recipients} {SEGMENT_NOUN[segment](recipients)}{" "}
              {scheduled
                ? `will receive this on ${scheduled.replace("T", " at ")}.`
                : "receive this straight away."}
            </p>
            <p>Once it has gone it cannot be recalled.</p>
          </div>
        }
      />
    </div>
  );
}

function History({ items }: { items: Schemas["Broadcast"][] }) {
  if (items.length === 0) {
    return (
      <section className="flex flex-col gap-16">
        <h2 className="type-heading-m text-primary">Sent before</h2>
        <div className="rounded-lg border border-subtle bg-surface">
          <EmptyState
            markId="comms-empty"
            title="Nothing sent yet."
            body="Every message you send to a group appears here with who it reached, so you can see what a cohort has already been told."
          />
        </div>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-16">
      <h2 className="type-heading-m text-primary">Sent before</h2>
      <ul className="flex flex-col gap-12">
        {items.map((item) => (
          <li
            key={item.id}
            className="flex flex-col gap-8 rounded-md border border-subtle bg-surface p-16"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-12">
              <p className="type-heading-s text-primary">{item.subject}</p>
              <p className="type-body-s text-muted">
                {SEGMENT_LABEL[item.segment]} ·{" "}
                {dateTime.format(new Date(item.createdAt))}
              </p>
            </div>
            <p className="type-body-s text-secondary">
              {item.state === "scheduled"
                ? `Scheduled for ${item.scheduledFor ? dateTime.format(new Date(item.scheduledFor)) : "later"}. Nobody has it yet.`
                : `Delivered to ${item.deliveredCount} of ${item.recipientCount}.`}
              {(item.failedCount ?? 0) > 0 &&
                ` ${item.failedCount} did not arrive — usually a dead address.`}
            </p>
            <p className="type-caption text-muted">Sent by {item.createdBy}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
