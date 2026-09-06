import { PublicMain } from "@/components/shell/public-shell";
import { VerifyToken } from "./verify-token";

export const metadata = { title: "Signing you in" };

export default async function VerifyPage(
  props: PageProps<"/verify/[token]">,
) {
  const { token } = await props.params;

  return (
    <PublicMain className="flex flex-col gap-24">
      <VerifyToken token={token} />
    </PublicMain>
  );
}
