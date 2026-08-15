import { AccountHeader } from "@/components/shell/account-header";
import { requireSession } from "@/lib/auth/guard";

/** Account scope: resolves the session only. There is no programme here. */
export default async function AccountLayout({ children }: LayoutProps<"/">) {
  const session = await requireSession();

  return (
    <div className="flex min-h-full flex-1 flex-col bg-page">
      <AccountHeader session={session} />
      <main className="mx-auto w-full max-w-participant flex-1 px-16 py-32">
        {children}
      </main>
    </div>
  );
}
