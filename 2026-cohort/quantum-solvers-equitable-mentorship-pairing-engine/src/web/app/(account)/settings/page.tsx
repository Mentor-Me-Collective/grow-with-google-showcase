import { serverApi } from "@/lib/api/server";
import { requireSession } from "@/lib/auth/guard";
import { SettingsForm } from "./settings-form";

export const metadata = { title: "Settings" };

export default async function SettingsPage() {
  await requireSession();

  const { data: settings, error } = await serverApi.GET("/account/settings");

  return (
    <div className="flex flex-col gap-24">
      <div className="flex flex-col gap-8">
        <h1 className="type-heading-l text-primary">Settings</h1>
        <p className="type-body-m text-secondary">
          Your account, and how much it is allowed to email you. These apply
          across every programme you belong to.
        </p>
      </div>

      {error || !settings ? (
        <div
          role="alert"
          className="rounded-md border border-danger bg-surface p-24 type-body-m text-secondary"
        >
          Your settings did not load, so nothing is shown rather than a form
          that might save the wrong thing over them. Reload to try again.
        </div>
      ) : (
        <SettingsForm settings={settings} />
      )}
    </div>
  );
}
