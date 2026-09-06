"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Field, TextareaField } from "@/components/ui/input";
import { DataTable, type Column, type SortState } from "@/components/ui/table";
import {
  StrandCard,
  StrandCardError,
  StrandCardSkeleton,
} from "@/components/strand/strand-card";
import type { components } from "@/lib/api/types";
import { ErrorSummary, FormRenderer } from "@/components/form/form-renderer";
import { useAnswerForm, type AnswerInputMap } from "@/components/form/use-answer-form";
import { FORM_VERSIONS } from "@/lib/api/msw/fixtures";
import { visibleFieldIds, type FormValues } from "@/lib/form/conditions";
import { toJsonSchema } from "@/lib/form/json-schema";

type Person = { id: string; name: string; role: string; load: number; score: number };

type StrandSummary = components["schemas"]["StrandSummary"];
type StrandMember = components["schemas"]["StrandMember"];

/** Fixed clock, so the quiet and ended lines read the same on every visit. */
const NOW = new Date("2026-08-08T09:00:00.000Z");
const shiftDays = (n: number) =>
  new Date(NOW.getTime() + n * 86_400_000).toISOString();

const participation = (n: number) =>
  `00000004-0000-4000-8000-${String(n).padStart(12, "0")}`;

// 101, 102 and 103 hash to strand colours 1, 2 and 3, so one of each is on
// screen without the card being told which to use.
const demoMember = (n: number, name: string, role: "mentor" | "mentee"): StrandMember => ({
  participationId: participation(n),
  name,
  role,
  headline: null,
  photoUrl: null,
  timezone: "Africa/Lagos",
  skills: [],
});

const BLESSING = demoMember(101, "Blessing Adewale", "mentee");
const FATIMA = demoMember(102, "Fatima Yusuf", "mentee");
const TOBI = demoMember(103, "Tobi Salami", "mentee");
const GRACE = demoMember(104, "Grace Mwangi", "mentee");
const AMARA = demoMember(105, "Amara Okonkwo", "mentor");

const strandDemo = (
  n: number,
  members: StrandMember[],
  over: Partial<StrandSummary>,
): StrandSummary => ({
  id: `00000008-0000-4000-8000-${String(n).padStart(12, "0")}`,
  programId: "00000002-0000-4000-8000-000000000001",
  state: "active",
  originMode: "batch",
  members,
  lastMessage: {
    authorName: members[0].name,
    body: "Wrote three tests. One of them caught a bug where I was not handling an empty result.",
    sentAt: shiftDays(-1),
  },
  lastActivityAt: shiftDays(-1),
  unreadCount: 0,
  nextSessionAt: null,
  endedAt: null,
  ...over,
});

const UNREAD = strandDemo(1, [BLESSING], {
  unreadCount: 2,
  nextSessionAt: shiftDays(4),
});
const SESSION = strandDemo(2, [FATIMA], {
  lastMessage: {
    authorName: "Amara Okonkwo",
    body: "Send it over when the first endpoint works end to end.",
    sentAt: shiftDays(-5),
  },
  lastActivityAt: shiftDays(-5),
  nextSessionAt: shiftDays(11),
});
const QUIET = strandDemo(3, [TOBI], {
  lastMessage: {
    authorName: "Tobi Salami",
    body: "Thank you. I will come back with something specific this week.",
    sentAt: shiftDays(-23),
  },
  lastActivityAt: shiftDays(-23),
});
const ENDED = strandDemo(4, [GRACE], {
  state: "ended",
  lastActivityAt: shiftDays(-40),
  endedAt: shiftDays(-38),
});
const GROUP = strandDemo(5, [BLESSING, FATIMA, TOBI, AMARA], {
  unreadCount: 12,
  lastMessage: {
    authorName: "Fatima Yusuf",
    body: "I have pushed the branch. Anyone free to look before Thursday?",
    sentAt: shiftDays(-1),
  },
});
const GROUP_QUIET = strandDemo(6, [BLESSING, FATIMA, AMARA], {
  lastActivityAt: shiftDays(-57),
  lastMessage: {
    authorName: "Amara Okonkwo",
    body: "Let us pick this up after the break.",
    sentAt: shiftDays(-57),
  },
});

const PEOPLE: Person[] = [
  { id: "p1", name: "Amara Okonkwo", role: "Mentor", load: 3, score: 0.91 },
  { id: "p2", name: "Blessing Adewale", role: "Mentee", load: 1, score: 0.84 },
  { id: "p3", name: "Wanjiru Kamau", role: "Mentor", load: 2, score: 0.8 },
  { id: "p4", name: "Fatima Yusuf", role: "Mentee", load: 1, score: 0.72 },
];

const COLUMNS: Array<Column<Person>> = [
  { key: "name", header: "Name", sortable: true, cell: (r) => r.name, csv: (r) => r.name },
  { key: "role", header: "Role", sortable: true, cell: (r) => r.role, csv: (r) => r.role },
  { key: "load", header: "Load", numeric: true, sortable: true, cell: (r) => r.load, csv: (r) => r.load },
  { key: "score", header: "Score", numeric: true, cell: (r) => r.score.toFixed(2), csv: (r) => r.score },
];

function Section({ n, title, children }: { n: string; title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-16">
      <div className="flex flex-col gap-4 border-b border-subtle pb-8">
        <span className="type-label text-muted">{n}</span>
        <h2 className="type-heading-m text-primary">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-16">
      <span className="w-96 shrink-0 type-caption text-muted">{label}</span>
      {children}
    </div>
  );
}

export function Gallery() {
  const [sort, setSort] = useState<SortState>({ key: "name", direction: "asc" });
  const [selected, setSelected] = useState<string[]>([]);
  const [selectedDemo, setSelectedDemo] = useState<string[]>(["p1", "p2"]);

  return (
    // `w-full` is load-bearing: an auto inline margin on a flex item overrides
    // stretch, so without it this sizes to max-content and the page scrolls
    // sideways on anything narrower than the widest section.
    <main className="mx-auto flex w-full max-w-coordinator flex-col gap-64 bg-page px-32 py-48">
      <header className="flex flex-col gap-4">
        <span className="type-label text-muted">Development only</span>
        <h1 className="type-heading-l text-primary">ui/ primitives, every state</h1>
        <p className="type-body-m text-secondary">
          Not reachable in a production build. Change a primitive and check this
          page before checking the screen you were working on.
        </p>
      </header>

      <Section n="01" title="Button — variants and sizes">
        {(["primary", "secondary", "ghost", "danger"] as const).map((variant) => (
          <Row key={variant} label={variant}>
            <Button variant={variant} size="sm">Publish</Button>
            <Button variant={variant} size="md">Publish</Button>
            <Button variant={variant} size="lg">Publish</Button>
          </Row>
        ))}
      </Section>

      <Section n="02" title="Button — states">
        <Row label="default"><Button>Say hello</Button></Row>
        <Row label="hover"><Button className="bg-accent-hover">Say hello</Button></Row>
        <Row label="focus"><Button autoFocus>Say hello</Button></Row>
        <Row label="active"><Button className="scale-98">Say hello</Button></Row>
        <Row label="disabled">
          <Button disabled>Say hello</Button>
          <Button variant="secondary" disabled>Say hello</Button>
          <Button variant="ghost" disabled>Say hello</Button>
          <Button variant="danger" disabled>Say hello</Button>
        </Row>
        <Row label="loading">
          <Button loading loadingLabel="Publishing">Publish 42 strands</Button>
          <Button variant="secondary" loading loadingLabel="Saving">Save</Button>
        </Row>
        <Row label="width held">
          <span className="flex flex-col gap-4">
            <Button id="btn-idle">Publish 42 strands</Button>
            <Button id="btn-loading" loading>Publish 42 strands</Button>
          </span>
        </Row>
      </Section>

      <Section n="03" title="Form field — states">
        <div className="grid max-w-participant gap-24 md:grid-cols-2">
          <Field label="Full name" placeholder="Amara Okonkwo" />
          <Field label="Full name" defaultValue="Amara Okonkwo" helper="As it appears on your certificate." />
          <Field label="Email address" required helper="We send the magic link here." />
          <Field label="Phone number" mark="optional" />
          <Field label="Cohort" defaultValue="Backend cohort 4" disabled />
          <Field
            label="Start date"
            defaultValue="2026-08-01"
            error="Enter a date after 14 September."
          />
          <TextareaField
            label="Why do you want a mentor?"
            helper="Two or three sentences is plenty."
          />
          <TextareaField
            label="What went wrong"
            error="Say what happened so a coordinator can act on it."
          />
        </div>
      </Section>

      <Section n="04" title="Data table — default, sortable, selectable">
        <DataTable
          caption="Roster of participants"
          columns={COLUMNS}
          rows={PEOPLE}
          getRowId={(r) => r.id}
          filters={<span className="type-body-s text-muted">Filter slot</span>}
          sort={sort}
          onSortChange={setSort}
          selectable
          selectedIds={selected}
          onSelectionChange={setSelected}
          bulkActions={(ids) => (
            <>
              <Button size="sm" variant="secondary">Message {ids.length}</Button>
              <Button size="sm" variant="ghost">Change role</Button>
            </>
          )}
          csvFileName="roster.csv"
        />
      </Section>

      <Section n="05" title="Data table — selection replaces the header row">
        <DataTable
          caption="Roster with a live selection"
          columns={COLUMNS}
          rows={PEOPLE}
          getRowId={(r) => r.id}
          filters={null}
          selectable
          selectedIds={selectedDemo}
          onSelectionChange={setSelectedDemo}
          bulkActions={() => (
            <Button size="sm" variant="secondary">Message selected</Button>
          )}
        />
      </Section>

      <Section n="06" title="Data table — loading, error, empty">
        <DataTable caption="Loading" columns={COLUMNS} rows={[]} getRowId={(r) => r.id} filters={null} loading />
        <DataTable
          caption="Error"
          columns={COLUMNS}
          rows={[]}
          getRowId={(r) => r.id}
          filters={null}
          error="The roster did not load."
          onRetry={() => undefined}
        />
        <DataTable caption="Empty" columns={COLUMNS} rows={[]} getRowId={(r) => r.id} filters={null} />
      </Section>

      <Section n="07" title="Empty state">
        <div className="rounded-md border border-subtle bg-surface">
          <EmptyState
            markId="es-1"
            title="No strands yet"
            body="When matching runs on 14 September your strand will appear here."
            action={<Button variant="secondary">Finish your profile</Button>}
          />
        </div>
        <div className="rounded-md border border-subtle bg-surface">
          <EmptyState
            markId="es-2"
            emphasis="display"
            title="Matching opens 14 September."
            body="Twelve mentors have joined so far. Finish your profile before then and you'll be included in the first round."
            action={<Button>Finish your profile</Button>}
          />
        </div>
        <div className="rounded-md border border-subtle bg-surface">
          <EmptyState markId="es-3" title="No results" body="No one matches those filters." />
        </div>
      </Section>

      <Section n="08" title="Strand card — one to one">
        <div className="flex max-w-participant flex-col gap-12">
          <StrandCard strand={SESSION} href="#" now={NOW} />
          <StrandCard strand={UNREAD} href="#" now={NOW} />
          <StrandCard strand={QUIET} href="#" now={NOW} />
          <StrandCard strand={ENDED} href="#" now={NOW} />
        </div>
        <p className="type-caption text-muted">
          Read down: default with a next session, two unread, quiet for 3 weeks,
          and ended. The unread card holds a session on 12 August too — 8.3 puts
          one thing on the right, and the count outranks it until the messages
          are read.
        </p>
      </Section>

      <Section n="09" title="Strand card — group">
        <div className="flex max-w-participant flex-col gap-12">
          <StrandCard strand={GROUP} href="#" now={NOW} />
          <StrandCard strand={GROUP_QUIET} href="#" now={NOW} />
        </div>
        <p className="type-caption text-muted">
          Three avatars at most, overlapping by 12. The chip counts everyone
          including you, so the preview line is not spent on the count. Group
          chips are neutral because no single partner owns the colour.
        </p>
      </Section>

      <Section n="10" title="Strand card — loading, error, empty">
        <div className="flex max-w-participant flex-col gap-12">
          <StrandCardSkeleton />
          <StrandCardSkeleton />
          <StrandCardError onRetry={() => undefined} />
          <div className="rounded-md border border-subtle bg-surface">
            <EmptyState
              markId="es-strand"
              title="No strands yet"
              body="Matching runs on 14 September. Your strand will appear here the moment it does."
            />
          </div>
        </div>
      </Section>

      <Section n="11" title="Strand card — narrow, 264px">
        <div className="flex max-w-sidebar flex-col gap-12">
          <StrandCard strand={UNREAD} href="#" now={NOW} />
          <StrandCard strand={GROUP} href="#" now={NOW} />
          <StrandCard strand={ENDED} href="#" now={NOW} />
        </div>
        <p className="type-caption text-muted">
          Narrower than any real column, so if truncation holds here it holds
          everywhere. Nothing on the right is pushed out of the card.
        </p>
      </Section>

      <Section n="12" title="Dynamic form renderer">
        <p className="max-w-public type-body-m text-secondary">
          The published mentee form for this programme, rendered from the schema
          with no page-level knowledge of any question. Answer &ldquo;No&rdquo;
          to &ldquo;Have you been mentored before?&rdquo; and a follow-up
          appears, carrying its own required rule with it. Submit while it is
          hidden and that rule does not fire.
        </p>
        <FormPlayground />
      </Section>
    </main>
  );
}

const MENTEE_FORM = FORM_VERSIONS[0];

function FormPlayground() {
  const [values, setValues] = useState<FormValues>({});
  const [payload, setPayload] = useState<string | null>(null);
  const form = useAnswerForm({ version: MENTEE_FORM });

  const visible = visibleFieldIds(MENTEE_FORM, values);
  const jsonSchema = toJsonSchema(MENTEE_FORM, visible);

  return (
    <div className="grid gap-32 lg:grid-cols-2">
      <form
        noValidate
        className="flex max-w-public flex-col gap-48"
        onChange={() => setValues(form.getValues())}
        onSubmit={form.submit((answers: AnswerInputMap) =>
          setPayload(JSON.stringify(answers, null, 2)),
        )}
      >
        {form.isSubmitted && <ErrorSummary form={form} />}
        <FormRenderer form={form} />
        <div className="flex">
          <Button type="submit" size="lg" loading={form.isSubmitting} loadingLabel="Sending">
            Send
          </Button>
        </div>
      </form>

      <div className="flex min-w-0 flex-col gap-24 lg:sticky lg:top-32 lg:self-start">
        <Panel
          title="Generated JSON Schema"
          note={`${visible.size} of ${MENTEE_FORM.sections.flatMap((s) => s.fields).length} fields on screen. Derived from the same generator the browser validates with, so the two cannot drift.`}
          body={JSON.stringify(jsonSchema, null, 2)}
        />
        <Panel
          title="Submitted payload"
          note="Hidden fields and the file field are absent, not null. Local state keeps them, so toggling an answer back does not lose what was typed."
          body={payload ?? "Nothing sent yet."}
        />
      </div>
    </div>
  );
}

function Panel({
  title,
  note,
  body,
}: {
  title: string;
  note: string;
  body: string;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-8">
      <h3 className="type-label text-primary">{title}</h3>
      <p className="type-caption text-muted">{note}</p>
      <pre className="max-h-screen min-w-0 overflow-auto rounded-md border border-subtle bg-sunken p-16 type-caption text-secondary">
        {body}
      </pre>
    </div>
  );
}
