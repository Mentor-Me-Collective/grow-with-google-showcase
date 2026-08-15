import { AdminSidebar } from "@/components/shell/admin-sidebar";
import { Forbidden } from "@/components/shell/forbidden";
import { requireCoordinator } from "@/lib/auth/guard";

/**
 * Desktop-first, per architecture 7: the sidebar is persistent and no drawer
 * is built for phones.
 */
export default async function AdminLayout({
  children,
  params,
}: LayoutProps<"/admin/o/[org]">) {
  const { org } = await params;
  const result = await requireCoordinator(org);

  if (!result.ok) {
    return (
      <Forbidden
        session={result.session}
        reason="You do not coordinate any programme in this organisation."
      />
    );
  }

  return (
    <div className="flex min-h-full flex-1 bg-page">
      <AdminSidebar
        session={result.session}
        programmes={result.programmes}
        current={result.programmes[0]}
      />
      {/* On paper the content is the page: no sidebar beside it, no gutter
          held open for one, and no horizontal scroll container. */}
      <main className="min-w-0 flex-1 overflow-x-auto px-32 py-32 print:overflow-visible print:p-0">
        <div className="mx-auto max-w-coordinator">{children}</div>
      </main>
    </div>
  );
}
