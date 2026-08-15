"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/input";
import { FairnessSummary } from "../../../runs/[runId]/fairness-summary";
import { saveRecipe, testRecipe } from "./actions";

type Recipe = Schemas["MatchingRecipe"];
type CriteriaField = Schemas["CriteriaField"];

const CONSTRAINTS: Record<
  Schemas["HardConstraintKind"],
  { label: string; help: string }
> = {
  role_compatible: {
    label: "A mentor must be paired with a mentee",
    help: "Off only for peer programmes where anyone can be paired with anyone.",
  },
  shared_skill: {
    label: "They must share at least one skill",
    help: "Keeps pairs on the same subject. Also the constraint most likely to leave people unmatched.",
  },
  same_timezone_band: {
    label: "They must be in overlapping time zones",
    help: "Makes meeting easier and shrinks the pool sharply across a continent.",
  },
  different_team: {
    label: "They must not be on the same team",
    help: "For workplace programmes, so nobody is mentored by their own manager.",
  },
};

export function CriteriaEditor({
  state,
  programId,
  formHref,
}: {
  state: Schemas["CriteriaEditorState"];
  programId: string;
  formHref: string;
}) {
  const router = useRouter();
  const [recipe, setRecipe] = useState<Recipe>(() =>
    structuredClone(state.recipe),
  );
  const [pending, startTransition] = useTransition();
  const [summary, setSummary] = useState<Schemas["FairnessSummary"] | null>(null);
  const [error, setError] = useState<string | undefined>();
  const [notice, setNotice] = useState<string | undefined>();

  const dirty = JSON.stringify(recipe) !== JSON.stringify(state.recipe);

  const payload: Schemas["MatchingRecipeSave"] = {
    name: recipe.name,
    hardConstraints: recipe.hardConstraints,
    weights: recipe.weights,
    fairness: recipe.fairness,
  };

  const weightFor = (fieldId: string) =>
    recipe.weights.find((w) => w.fieldId === fieldId);
  const priorityFor = (fieldId: string) =>
    recipe.fairness.priorityWeights.find((w) => w.fieldId === fieldId);

  const setWeight = (fieldId: string, patch: Partial<Schemas["FieldWeight"]>) =>
    setRecipe((current) => {
      const exists = current.weights.some((w) => w.fieldId === fieldId);
      return {
        ...current,
        weights: exists
          ? current.weights.map((w) =>
              w.fieldId === fieldId ? { ...w, ...patch } : w,
            )
          : [
              ...current.weights,
              { fieldId, weight: 0, direction: "similar", ...patch },
            ],
      };
    });

  const setPriority = (fieldId: string, weight: number) =>
    setRecipe((current) => {
      const exists = current.fairness.priorityWeights.some(
        (w) => w.fieldId === fieldId,
      );
      return {
        ...current,
        fairness: {
          ...current.fairness,
          priorityWeights: exists
            ? current.fairness.priorityWeights.map((w) =>
                w.fieldId === fieldId ? { ...w, weight } : w,
              )
            : [...current.fairness.priorityWeights, { fieldId, weight }],
        },
      };
    });

  const save = () =>
    startTransition(async () => {
      const result = await saveRecipe({ programId, recipe: payload });
      if (result.ok) {
        setRecipe(result.recipe);
        setError(undefined);
        setNotice(`Saved as version ${result.recipe.version}.`);
        router.refresh();
      } else {
        setError(result.message);
        setNotice(undefined);
      }
    });

  const test = () =>
    startTransition(async () => {
      const result = await testRecipe({ programId, recipe: payload });
      if (result.ok) {
        setSummary(result.summary);
        setError(undefined);
        setNotice(undefined);
      } else {
        setError(result.message);
        setSummary(null);
      }
    });

  return (
    <div className="flex flex-col gap-32">
      <Field
        label="Recipe name"
        value={recipe.name}
        mark="none"
        onChange={(e) => setRecipe((c) => ({ ...c, name: e.target.value }))}
        helper={
          recipe.updatedBy
            ? `Version ${recipe.version}, last changed by ${recipe.updatedBy}.`
            : `Version ${recipe.version}.`
        }
      />

      <section className="flex flex-col gap-16">
        <div className="flex flex-col gap-4">
          <h2 className="type-heading-m text-primary">Hard constraints</h2>
          <p className="type-body-s text-secondary">
            A pair failing any of these is never proposed, whatever it scores.
            Every one you switch on shrinks the pool, and a shrunken pool is
            what leaves people unmatched.
          </p>
        </div>

        <ul className="flex flex-col gap-12">
          {recipe.hardConstraints.map((constraint) => (
            <li key={constraint.kind}>
              <label className="flex items-start gap-12">
                <input
                  type="checkbox"
                  checked={constraint.enabled}
                  onChange={(e) =>
                    setRecipe((current) => ({
                      ...current,
                      hardConstraints: current.hardConstraints.map((c) =>
                        c.kind === constraint.kind
                          ? { ...c, enabled: e.target.checked }
                          : c,
                      ),
                    }))
                  }
                  className="mt-4 size-16 shrink-0 rounded-xs border border-default accent-[var(--action-primary-bg)] outline-focus outline-offset-2 focus-visible:outline-2"
                />
                <span className="flex flex-col gap-4">
                  <span className="type-body-m text-primary">
                    {CONSTRAINTS[constraint.kind].label}
                  </span>
                  <span className="type-caption text-muted">
                    {CONSTRAINTS[constraint.kind].help}
                  </span>
                </span>
              </label>
            </li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-16">
        <div className="flex flex-col gap-4">
          <h2 className="type-heading-m text-primary">What counts, and how much</h2>
          <p className="type-body-s text-secondary">
            Every question flagged for matching on the published form.{" "}
            <Link href={formHref} className="text-link underline">
              Flag more in the form
            </Link>
            .
          </p>
        </div>

        {state.matchingFields.length === 0 ? (
          <p className="rounded-md border border-subtle bg-sunken p-16 type-body-m text-secondary">
            No published question is flagged for matching, so there is nothing to
            weigh. Flag a question in the form builder and it appears here.
          </p>
        ) : (
          <ul className="flex flex-col gap-24">
            {state.matchingFields.map((field) => (
              <WeightRow
                key={field.fieldId}
                field={field}
                weight={weightFor(field.fieldId)}
                onChange={(patch) => setWeight(field.fieldId, patch)}
              />
            ))}
          </ul>
        )}
      </section>

      <section className="flex flex-col gap-16">
        <div className="flex flex-col gap-4">
          <h2 className="type-heading-m text-primary">Fairness</h2>
          <p className="type-body-s text-secondary">
            What stops a recipe matching six people perfectly and leaving thirty
            out.
          </p>
        </div>

        <div className="flex flex-wrap gap-24">
          <Field
            label="Coverage floor"
            type="number"
            min={0}
            max={100}
            numeric
            mark="none"
            value={Math.round(recipe.fairness.coverageFloor * 100)}
            onChange={(e) =>
              setRecipe((c) => ({
                ...c,
                fairness: {
                  ...c.fairness,
                  coverageFloor: Number(e.target.value) / 100,
                },
              }))
            }
            helper="The share of mentees a run should place before it is worth reviewing."
          />
          <Field
            label="Cap every mentor at"
            type="number"
            min={1}
            numeric
            mark="none"
            value={recipe.fairness.mentorCapacityCap ?? ""}
            onChange={(e) =>
              setRecipe((c) => ({
                ...c,
                fairness: {
                  ...c.fairness,
                  mentorCapacityCap:
                    e.target.value === "" ? null : Number(e.target.value),
                },
              }))
            }
            helper="A ceiling over what mentors set for themselves. Empty respects their own number."
          />
        </div>

        <div className="flex flex-col gap-16">
          <h3 className="type-label text-muted">
            Who gets matched first when mentors are scarce
          </h3>
          {state.equityFields.length === 0 ? (
            <p className="type-body-s text-secondary">
              No published question is flagged for priority, so everyone is
              treated the same when mentors run short.
            </p>
          ) : (
            <ul className="flex flex-col gap-16">
              {state.equityFields.map((field) => (
                <li key={field.fieldId} className="flex flex-col gap-8">
                  <Slider
                    id={`priority-${field.fieldId}`}
                    label={field.label}
                    role={field.role}
                    value={priorityFor(field.fieldId)?.weight ?? 0}
                    onChange={(v) => setPriority(field.fieldId, v)}
                  />
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {error && (
        <p role="alert" className="type-body-m text-danger">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="type-body-s text-secondary">
          {notice}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-16 border-t border-subtle pt-24">
        <Button
          size="lg"
          onClick={save}
          disabled={!dirty}
          loading={pending}
          loadingLabel="Saving the recipe"
        >
          Save
        </Button>
        <Button size="lg" variant="secondary" onClick={test} loading={pending} loadingLabel="Scoring the roster">
          Test on the current roster
        </Button>
        <p className="type-body-s text-muted" role="status">
          {dirty ? "Unsaved changes." : "No unsaved changes."}
        </p>
      </div>

      {summary && (
        <section className="flex flex-col gap-16">
          <div className="flex flex-col gap-4">
            <h2 className="type-heading-m text-primary">
              What this recipe would produce
            </h2>
            {/* 5.5: the test outputs the summary and never the pairs. Tuning
                weights while watching individual matches is how a cohort gets
                optimised for one person. */}
            <p className="type-body-s text-secondary">
              Nothing was drafted and nobody was told anything. Names are
              deliberately not shown: a recipe tuned until one particular pair
              appears is a recipe tuned for one person.
            </p>
          </div>
          <FairnessSummary summary={summary} />
        </section>
      )}
    </div>
  );
}

function WeightRow({
  field,
  weight,
  onChange,
}: {
  field: CriteriaField;
  weight: Schemas["FieldWeight"] | undefined;
  onChange: (patch: Partial<Schemas["FieldWeight"]>) => void;
}) {
  const value = weight?.weight ?? 0;

  return (
    <li className="flex flex-col gap-12">
      <Slider
        id={`weight-${field.fieldId}`}
        label={field.label}
        role={field.role}
        value={value}
        onChange={(v) => onChange({ weight: v })}
      />

      <fieldset className="flex flex-wrap items-center gap-16">
        <legend className="sr-only">Direction for {field.label}</legend>
        {(["similar", "complementary"] as const).map((direction) => (
          <label key={direction} className="flex items-center gap-8">
            <input
              type="radio"
              name={`direction-${field.fieldId}`}
              checked={(weight?.direction ?? "similar") === direction}
              onChange={() => onChange({ direction })}
              disabled={value === 0}
              className="size-16 accent-[var(--action-primary-bg)] outline-focus outline-offset-2 focus-visible:outline-2"
            />
            <span className="type-body-s text-secondary">
              {direction === "similar"
                ? "Reward similar answers"
                : "Reward different answers"}
            </span>
          </label>
        ))}
      </fieldset>
    </li>
  );
}

/**
 * The number is spelled out beside the slider, and it is the number that is
 * authoritative: a slider alone gives no way to say "40" to a colleague, and
 * colour and position cannot carry the value on their own.
 */
function Slider({
  id,
  label,
  role,
  value,
  onChange,
}: {
  id: string;
  label: string;
  role: Schemas["Role"];
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <div className="flex flex-col gap-8">
      <label htmlFor={id} className="flex flex-wrap items-baseline gap-8">
        <span className="type-body-m text-primary">{label}</span>
        <span className="type-caption text-muted">
          {role === "mentor" ? "Mentor form" : "Mentee form"}
        </span>
      </label>
      <div className="flex items-center gap-16">
        <input
          id={id}
          type="range"
          min={0}
          max={100}
          step={5}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="h-8 min-w-0 flex-1 accent-[var(--action-primary-bg)] outline-focus outline-offset-2 focus-visible:outline-2"
        />
        <span className="w-48 shrink-0 text-right type-data-m text-primary">
          {value}
        </span>
      </div>
      {value === 0 && (
        <p className="type-caption text-muted">
          Collected, but not scored.
        </p>
      )}
    </div>
  );
}
