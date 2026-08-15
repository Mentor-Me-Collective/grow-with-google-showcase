"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDownIcon, SignOutIcon } from "@/components/icon/icons";
import { api } from "@/lib/api/client";
import type { Session } from "@/lib/auth/guard";
import { useDropdown } from "./use-dropdown";

function initials(name: string) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function AvatarMenu({ account }: { account: Session["account"] }) {
  const { open, setOpen, close, triggerRef, panelRef } = useDropdown();
  const router = useRouter();

  const signOut = useMutation({
    mutationFn: async () => {
      // 204 only, so there is no error body to read — the status is the signal.
      const { response } = await api.POST("/auth/signout");
      if (!response.ok) throw new Error("Sign out failed");
    },
    onSuccess: () => {
      close(false);
      router.push("/signin");
      router.refresh();
    },
  });

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex min-h-48 items-center gap-8 rounded-md px-8 transition-colors duration-instant hover:bg-sunken"
      >
        <span className="sr-only">Account menu for {account.name}</span>
        <span
          aria-hidden="true"
          className="flex size-32 items-center justify-center rounded-full bg-inverse type-caption text-on-inverse"
        >
          {initials(account.name)}
        </span>
        <ChevronDownIcon className="size-16 text-muted" />
      </button>

      {open && (
        <div
          ref={panelRef}
          role="menu"
          aria-label="Account"
          className="absolute right-0 top-full z-10 mt-4 w-max min-w-full rounded-md border border-subtle bg-surface p-4 shadow-raised"
        >
          <div className="border-b border-subtle px-12 py-12">
            <p className="type-body-s text-primary">{account.name}</p>
            <p className="type-caption text-muted">{account.email}</p>
          </div>

          <Link
            role="menuitem"
            href="/settings"
            onClick={() => close(false)}
            className="flex min-h-48 items-center rounded-sm px-12 type-body-s text-primary transition-colors duration-instant hover:bg-sunken"
          >
            Settings
          </Link>
          <Link
            role="menuitem"
            href="/programs"
            onClick={() => close(false)}
            className="flex min-h-48 items-center rounded-sm px-12 type-body-s text-primary transition-colors duration-instant hover:bg-sunken"
          >
            My programmes
          </Link>

          <button
            role="menuitem"
            type="button"
            onClick={() => signOut.mutate()}
            disabled={signOut.isPending}
            className="flex min-h-48 w-full items-center gap-12 rounded-sm px-12 text-left type-body-s text-primary transition-colors duration-instant hover:bg-sunken"
          >
            <SignOutIcon className="size-16 text-muted" />
            {signOut.isPending ? "Signing out" : "Sign out"}
          </button>

          {signOut.isError && (
            <p role="alert" className="px-12 py-8 type-caption text-danger">
              Sign out did not complete.{" "}
              <button
                type="button"
                onClick={() => signOut.mutate()}
                className="underline"
              >
                Try again
              </button>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
