"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { markApiReady } from "@/lib/api/ready";
import { mockingEnabled } from "@/lib/api/msw/enabled";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, refetchOnWindowFocus: false },
        },
      }),
  );

  useEffect(() => {
    if (!mockingEnabled) return;
    void import("@/lib/api/msw/start")
      .then(({ startWorkerOnce }) => startWorkerOnce())
      .finally(markApiReady);
  }, []);

  // Children render immediately: Server Components are intercepted in Node by
  // instrumentation.ts, and browser requests wait on apiReady inside the
  // client's own fetch. Nothing is withheld from the first paint.
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
