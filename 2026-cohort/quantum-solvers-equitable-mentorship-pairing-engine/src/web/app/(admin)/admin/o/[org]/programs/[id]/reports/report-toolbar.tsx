"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Schemas } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/input";

/**
 * The date range lives in the URL so a report view can be sent to somebody, and
 * printing is the browser's own dialogue rather than a generated PDF — the
 * print stylesheet is what makes the page a document, and a second rendering
 * path to PDF would be a second thing to keep true.
 */
export function ReportToolbar({
  report,
  basePath,
}: {
  report: Schemas["ProgramReport"];
  basePath: string;
}) {
  const router = useRouter();
  const [from, setFrom] = useState(report.from);
  const [to, setTo] = useState(report.to);

  const csv = () => {
    const rows: Array<[string, string, string]> = [
      ["Section", "Label", "Value"],
      ...report.coverageOverTime.map(
        (p) =>
          ["Coverage", p.date, String(p.value)] as [string, string, string],
      ),
      ...report.sessionsByWeek.map(
        (p) => ["Sessions", p.label, String(p.count)] as [string, string, string],
      ),
      ...report.milestoneCompletion.map(
        (m) =>
          ["Milestones", m.title, `${m.completed} of ${m.total}`] as [
            string,
            string,
            string,
          ],
      ),
      ...report.dropOff.map(
        (d) => ["Drop-off", d.stage, String(d.count)] as [string, string, string],
      ),
      ...report.qualityByBand.map(
        (b) =>
          ["Match quality", b.band, String(b.meanScore)] as [
            string,
            string,
            string,
          ],
      ),
    ];

    const escape = (v: string) =>
      /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
    const blob = new Blob([rows.map((r) => r.map(escape).join(",")).join("\n")], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report-${report.from}-to-${report.to}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-wrap items-end gap-16 print:hidden">
      <Field
        label="From"
        type="date"
        value={from}
        mark="none"
        onChange={(e) => setFrom(e.target.value)}
      />
      <Field
        label="To"
        type="date"
        value={to}
        mark="none"
        onChange={(e) => setTo(e.target.value)}
      />
      <Button
        variant="secondary"
        onClick={() => router.push(`${basePath}?from=${from}&to=${to}`)}
      >
        Apply range
      </Button>
      <Button variant="ghost" onClick={csv}>
        Export CSV
      </Button>
      <Button variant="ghost" onClick={() => window.print()}>
        Print or save as PDF
      </Button>
    </div>
  );
}
