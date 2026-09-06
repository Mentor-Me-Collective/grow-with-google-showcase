import type { components } from "@/lib/api/types";

type MergeCode = components["schemas"]["MergeCode"];

const CODE_PATTERN = /\{([^}]+)\}/g;

/**
 * Resolves codes with the samples the API supplies, so a preview performs the
 * same substitution the sender will rather than one the browser invented.
 *
 * An unknown code is left standing rather than blanked. Seeing {mentor.name}
 * survive the preview is how somebody learns it is not a real code; silently
 * removing it would hide the mistake until it reached an inbox.
 */
export function resolveMergeCodes(text: string, codes: MergeCode[]) {
  const samples = new Map(codes.map((c) => [c.code, c.sample]));
  return text.replace(
    CODE_PATTERN,
    (whole, code) => samples.get(String(code).trim()) ?? whole,
  );
}

/** Codes written in the text that are not on the allowed list. */
export function unknownMergeCodes(text: string, codes: MergeCode[]) {
  const allowed = new Set(codes.map((c) => c.code));
  const used = [...text.matchAll(CODE_PATTERN)].map((m) => m[1].trim());
  return [...new Set(used.filter((c) => !allowed.has(c)))];
}

/**
 * Inserts a code at the cursor rather than appending it. Somebody reaches for a
 * code mid-sentence, and appending would put it at the end of the message they
 * are in the middle of writing.
 */
export function insertAtCursor(
  textarea: HTMLTextAreaElement | null,
  current: string,
  code: string,
): { text: string; caret: number } {
  const token = `{${code}}`;
  if (!textarea) {
    return { text: `${current}${token}`, caret: current.length + token.length };
  }
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  return {
    text: current.slice(0, start) + token + current.slice(end),
    caret: start + token.length,
  };
}
