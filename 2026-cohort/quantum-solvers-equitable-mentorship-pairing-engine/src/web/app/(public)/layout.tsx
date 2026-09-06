/**
 * No session, no width, no chrome. The frame only.
 *
 * Width and header live in the pages, because they differ: landing and apply
 * carry the 72px header and lay out full bleed under it, while signin, verify
 * and invite are a bare 720 column. Putting the column here would force the
 * header inside it, which is not what a header is.
 *
 * Architecture 7 records the split.
 */
export default function PublicLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-full flex-1 flex-col bg-page">{children}</div>
  );
}
