"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import type { components } from "@/lib/api/types";
import { api } from "@/lib/api/client";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { WeaveMark } from "@/components/brand/weave-mark";
import { controlClasses } from "@/components/ui/input";

type S = components["schemas"];

const dayLabel = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(iso));

const timeLabel = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }).format(new Date(iso));

const sameDay = (a: string, b: string) => a.slice(0, 10) === b.slice(0, 10);

/**
 * The centre column. Messages in body-l, which section 5.3 names for exactly
 * this: long-form reading and strand messages.
 *
 * No bubbles. Own messages sit right, the partner's sit left with an avatar,
 * and the alignment plus the name under each is what separates them — so the
 * thread reads as writing rather than as chat.
 */
export function Conversation({
  strandId,
  title,
  privacyLine,
  writeTo,
  me,
  initialMessages,
  partner,
  createdAt,
  ended,
}: {
  strandId: string;
  title: string;
  privacyLine: string;
  writeTo: string;
  me: string;
  initialMessages: S["Message"][];
  partner: S["StrandMember"] | undefined;
  createdAt: string;
  ended: boolean;
}) {
  const [messages, setMessages] = useState(initialMessages);
  const [body, setBody] = useState("");
  const [failed, setFailed] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);

  const send = useMutation({
    mutationFn: async (text: string) => {
      const { data, error } = await api.POST("/strands/{strandId}/messages", {
        params: { path: { strandId } },
        body: { body: text, clientToken: crypto.randomUUID() },
      });
      if (error || !data) throw new Error("send failed");
      return data;
    },
    onSuccess: (message) => {
      setMessages((prev) => [...prev, message]);
      setBody("");
      setFailed(false);
    },
    onError: () => setFailed(true),
  });

  // Newest last, so the thread opens at the bottom the way it was left.
  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  return (
    <div className="flex h-thread flex-col overflow-hidden rounded-lg border border-subtle bg-surface">
      <div className="flex items-center justify-between gap-16 border-b border-subtle px-24 py-16">
        <h2 className="min-w-0 truncate type-heading-s text-primary">{title}</h2>
        <p className="shrink-0 type-caption text-muted">{privacyLine}</p>
      </div>

      <div ref={threadRef} className="flex flex-1 flex-col gap-24 overflow-auto p-24">
        {messages.length === 0 ? (
          <Unwritten partner={partner} createdAt={createdAt} />
        ) : (
          messages.map((message, i) => (
            <Row
              key={message.id}
              message={message}
              mine={message.author.participationId === me}
              showDay={i === 0 || !sameDay(messages[i - 1].sentAt, message.sentAt)}
            />
          ))
        )}
      </div>

      <div className="border-t border-subtle px-24 py-16">
        {ended ? (
          <p className="type-body-s text-muted">
            This strand has ended. The thread stays here to read.
          </p>
        ) : (
          <form
            className="flex items-end gap-12"
            onSubmit={(e) => {
              e.preventDefault();
              const text = body.trim();
              if (text.length > 0) send.mutate(text);
            }}
          >
            <label htmlFor="strand-message" className="sr-only">
              Write to {writeTo}
            </label>
            <input
              id="strand-message"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder={`Write to ${writeTo}`}
              aria-invalid={failed || undefined}
              aria-describedby={failed ? "strand-message-error" : undefined}
              className={`h-field ${controlClasses(failed)}`}
            />
            <Button
              type="submit"
              className="h-field"
              disabled={body.trim().length === 0}
              loading={send.isPending}
              loadingLabel="Sending"
            >
              Send
            </Button>
          </form>
        )}

        {failed && (
          <p id="strand-message-error" role="alert" className="pt-8 type-caption text-danger">
            That did not send. Your words are still in the box — press Send again.
          </p>
        )}
      </div>
    </div>
  );
}

function Row({
  message,
  mine,
  showDay,
}: {
  message: S["Message"];
  mine: boolean;
  showDay: boolean;
}) {
  return (
    <>
      {showDay && (
        <p className="flex justify-center type-caption text-muted">
          {dayLabel(message.sentAt)}
        </p>
      )}
      <div className={`flex gap-12 ${mine ? "flex-row-reverse" : ""}`}>
        <Avatar
          name={message.author.name}
          participationId={message.author.participationId}
          size={32}
        />
        <div className={`flex min-w-0 flex-col gap-4 ${mine ? "items-end" : ""}`}>
          <p className={`type-body-l text-primary ${mine ? "text-right" : ""}`}>
            {message.body}
          </p>
          <p className="type-caption text-muted">
            {mine ? "You" : message.author.name.split(" ")[0]} ·{" "}
            {timeLabel(message.sentAt)}
            {message.deliveryState === "sent" && " · Sending"}
          </p>
        </div>
      </div>
    </>
  );
}

/**
 * A matched strand nobody has written in yet. Not "no messages" — the point of
 * the screen is that somebody is waiting on the other end, so the empty state
 * says who, and offers the one line that starts it.
 */
function Unwritten({
  partner,
  createdAt,
}: {
  partner: S["StrandMember"] | undefined;
  createdAt: string;
}) {
  const name = partner?.name.split(" ")[0] ?? "They";
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-24 px-16 text-center">
      <span className="text-default">
        <WeaveMark size={48} mono id="unwritten-mark" title={null} />
      </span>
      <div className="flex max-w-public flex-col gap-8">
        <p className="type-heading-m text-primary">Nobody has written yet</p>
        <p className="type-body-m text-secondary">
          {name} was matched with you on {dayLabel(createdAt)}. One line is enough
          to start.
        </p>
      </div>
    </div>
  );
}
