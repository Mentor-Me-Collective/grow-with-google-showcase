export function isReadAloudSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

/** Reads the given text aloud, canceling anything already speaking first. */
export function speak(text: string, onEnd?: () => void): void {
  if (!isReadAloudSupported() || !text.trim()) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  if (onEnd) {
    utterance.onend = onEnd;
    utterance.onerror = onEnd;
  }
  window.speechSynthesis.speak(utterance);
}

export function stopSpeaking(): void {
  if (!isReadAloudSupported()) return;
  window.speechSynthesis.cancel();
}

export function isSpeaking(): boolean {
  return isReadAloudSupported() && window.speechSynthesis.speaking;
}
