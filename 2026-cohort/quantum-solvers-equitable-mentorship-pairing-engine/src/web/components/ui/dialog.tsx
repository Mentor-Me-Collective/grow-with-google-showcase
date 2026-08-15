"use client";

import { useEffect, useRef } from "react";
import { Button, type ButtonVariant } from "./button";

/**
 * Architecture 7 lists this once, for irreversible actions, with the counts
 * spelled out. Section 11 requires focus to be trapped and returned.
 *
 * Built on the native dialog rather than a div with role="dialog": showModal()
 * gives the focus trap, the top layer, the inert background and the Escape key
 * from the platform. All four are things a hand-rolled modal gets subtly wrong,
 * and the browser also restores focus to the element that opened it on close.
 */
export function ConfirmDialog({
  open,
  title,
  /** Spell out what will happen, with the counts. Not "Are you sure?". */
  body,
  confirmLabel,
  cancelLabel = "Cancel",
  confirmVariant = "primary",
  busy = false,
  busyLabel,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  body: React.ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  confirmVariant?: ButtonVariant;
  busy?: boolean;
  busyLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby="confirm-title"
      // Escape fires cancel; the parent owns `open`, so it must hear about it
      // or the dialog closes while the state still says it is open.
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onCancel();
      }}
      className={[
        "m-auto w-full max-w-public rounded-lg border border-subtle bg-surface p-32",
        "text-primary shadow-overlay",
        "backdrop:bg-inverse backdrop:opacity-50",
      ].join(" ")}
    >
      <div className="flex flex-col gap-16">
        <h2 id="confirm-title" className="type-heading-m text-primary">
          {title}
        </h2>

        <div className="type-body-m text-secondary">{body}</div>

        <div className="flex flex-wrap justify-end gap-12 pt-8">
          <Button variant="ghost" onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </Button>
          <Button
            variant={confirmVariant}
            onClick={onConfirm}
            loading={busy}
            loadingLabel={busyLabel ?? confirmLabel}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </dialog>
  );
}
