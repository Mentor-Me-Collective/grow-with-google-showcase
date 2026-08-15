export async function register() {
  const { mockingEnabled } = await import("./lib/api/msw/enabled");
  if (!mockingEnabled) return;
  if (process.env.NEXT_RUNTIME !== "nodejs") return;

  const { server } = await import("./lib/api/msw/server");
  server.listen({ onUnhandledRequest: "bypass" });
}
