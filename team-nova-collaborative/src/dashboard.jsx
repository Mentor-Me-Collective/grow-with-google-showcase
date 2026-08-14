import React, { useState, useMemo } from "react";
import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";
import {
  FileText,
  Bell,
  Wallet,
  FolderOpen,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  Upload,
  Search,
  LayoutDashboard,
  Receipt,
  Milestone as MilestoneIcon,
  Settings,
  TrendingUp,
} from "lucide-react";

/* ---------------------------------------------------------
   TOKENS
   Ink/teal ledger palette — deliberately not the AI-default
   cream+terracotta or black+acid-green combos. The idea:
   a freelancer's "official record" should feel like a
   trustworthy paper ledger rendered digitally — hence the
   monospace figures for every amount and date, paired with
   a plain, quiet sans for interface chrome.
--------------------------------------------------------- */
const INK = "#0B2B2C";
const TEAL = "#0F6B72";
const TEAL_DEEP = "#0A4F54";
const MINT = "#17B890";
const AMBER = "#C98A12";
const CORAL = "#C24435";
const BG = "#F4F7F6";
const CARD = "#FFFFFF";
const MUTED = "#5F7370";
const BORDER = "#E1E9E7";
const BORDER_SOFT = "#EDF2F1";

const fontSans =
  "'IBM Plex Sans', -apple-system, 'Segoe UI', sans-serif";
const fontMono = "'IBM Plex Mono', 'SFMono-Regular', monospace";

/* ---------------------------------------------------------
   SAMPLE DATA
--------------------------------------------------------- */
const invoices = [
  { id: "INV-0142", client: "Zenith Retail Co.", project: "Brand refresh — Phase 2", amount: 185000, due: "Aug 14", status: "overdue", daysLate: 6 },
  { id: "INV-0139", client: "Amara & Co.", project: "Landing page build", amount: 96000, due: "Aug 09", status: "overdue", daysLate: 11 },
  { id: "INV-0146", client: "Lekki Foodhall", project: "Social content — July", amount: 64000, due: "Aug 18", status: "pending" },
  { id: "INV-0147", client: "Studio Ninefive", project: "Logo + brand kit", amount: 220000, due: "Aug 22", status: "pending" },
  { id: "INV-0144", client: "Chuka Adeyemi", project: "Portfolio site", amount: 140000, due: "Aug 03", status: "paid" },
  { id: "INV-0141", client: "Bolaji Interiors", project: "Product shoot retouching", amount: 58000, due: "Jul 29", status: "paid" },
];

const milestones = [
  { title: "Wireframes approved", project: "Zenith Retail Co.", date: "Aug 05", done: true },
  { title: "First draft delivered", project: "Studio Ninefive", date: "Aug 12", done: true },
  { title: "Client revision round", project: "Amara & Co.", date: "Aug 16", done: false },
  { title: "Final assets handoff", project: "Lekki Foodhall", date: "Aug 24", done: false },
];

const activity = [
  { text: "Invoice INV-0142 marked overdue", time: "2h ago", tone: "danger" },
  { text: "Contract v3 uploaded for Amara & Co.", time: "5h ago", tone: "neutral" },
  { text: "Payment received — INV-0144", time: "1d ago", tone: "success" },
  { text: "Reminder sent to Lekki Foodhall", time: "2d ago", tone: "neutral" },
];

const naira = (n) => "₦" + n.toLocaleString("en-NG");

const STATUS_META = {
  overdue: { label: "Overdue", color: CORAL, bg: "#FBEAE7" },
  pending: { label: "Pending", color: AMBER, bg: "#FBF1DE" },
  paid: { label: "Paid", color: MINT, bg: "#E4F6F0" },
};

/* ---------------------------------------------------------
   SIGNATURE ELEMENT: Payment Health ring
   Directly visualizes this user's on-time payment rate
   against the team's own research baseline (Freelancers
   Union: 62% of freelancers report nonpayment at least
   once → implying a national on-time baseline near ~40%).
   This is the North Star KPI, rendered per-user.
--------------------------------------------------------- */
function PaymentHealthRing({ value, baseline }) {
  const data = [{ name: "health", value, fill: MINT }];
  return (
    <div className="relative flex flex-col items-center justify-center">
      <div style={{ width: 190, height: 190 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="72%"
            outerRadius="100%"
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              angleAxisId={0}
              tick={false}
            />
            <RadialBar
              background={{ fill: BORDER_SOFT }}
              dataKey="value"
              cornerRadius={20}
              angleAxisId={0}
            />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
      <div
        className="absolute flex flex-col items-center justify-center"
        style={{ top: "38%" }}
      >
        <span
          style={{ fontFamily: fontMono, color: INK, fontSize: 34, fontWeight: 600, lineHeight: 1 }}
        >
          {value}%
        </span>
        <span style={{ fontFamily: fontSans, color: MUTED, fontSize: 11, marginTop: 6 }}>
          on-time this month
        </span>
      </div>
      <div className="mt-3 flex items-center gap-1.5" style={{ fontFamily: fontSans }}>
        <span
          className="inline-block rounded-full"
          style={{ width: 6, height: 6, background: BORDER }}
        />
        <span style={{ fontSize: 11, color: MUTED }}>
          Nigeria baseline (industry avg.):{" "}
          <span style={{ fontFamily: fontMono, color: INK }}>{baseline}%</span>
        </span>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, accent }) {
  return (
    <div
      className="flex-1 min-w-[150px] rounded-xl p-4"
      style={{ background: CARD, border: `1px solid ${BORDER}` }}
    >
      <div className="flex items-center justify-between mb-3">
        <div
          className="flex items-center justify-center rounded-lg"
          style={{ width: 30, height: 30, background: accent + "1A" }}
        >
          <Icon size={15} color={accent} strokeWidth={2.2} />
        </div>
      </div>
      <div style={{ fontFamily: fontMono, fontSize: 21, fontWeight: 600, color: INK }}>
        {value}
      </div>
      <div style={{ fontFamily: fontSans, fontSize: 12, color: MUTED, marginTop: 2 }}>
        {label}
      </div>
      {sub && (
        <div style={{ fontFamily: fontSans, fontSize: 11, color: accent, marginTop: 6 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function InvoiceRow({ inv }) {
  const meta = STATUS_META[inv.status];
  return (
    <div
      className="flex items-center justify-between py-3 px-3.5 rounded-lg"
      style={{ borderBottom: `1px solid ${BORDER_SOFT}` }}
    >
      <div className="flex flex-col">
        <span style={{ fontFamily: fontSans, fontSize: 13.5, color: INK, fontWeight: 500 }}>
          {inv.client}
        </span>
        <span style={{ fontFamily: fontSans, fontSize: 11.5, color: MUTED, marginTop: 1 }}>
          {inv.project}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <div style={{ fontFamily: fontMono, fontSize: 13.5, color: INK, fontWeight: 600 }}>
            {naira(inv.amount)}
          </div>
          <div style={{ fontFamily: fontMono, fontSize: 10.5, color: MUTED, marginTop: 1 }}>
            due {inv.due}
          </div>
        </div>
        <span
          className="px-2 py-1 rounded-full whitespace-nowrap"
          style={{
            fontFamily: fontSans,
            fontSize: 10.5,
            fontWeight: 600,
            color: meta.color,
            background: meta.bg,
          }}
        >
          {inv.status === "overdue" ? `${inv.daysLate}d late` : meta.label}
        </span>
      </div>
    </div>
  );
}

const NAV = [
  { icon: LayoutDashboard, label: "Dashboard", active: true },
  { icon: FolderOpen, label: "Contracts" },
  { icon: Receipt, label: "Invoices" },
  { icon: MilestoneIcon, label: "Milestones" },
  { icon: Settings, label: "Settings" },
];

export default function Dashboard() {
  const [tab, setTab] = useState("all");

  const filtered = useMemo(() => {
    if (tab === "all") return invoices;
    return invoices.filter((i) => i.status === tab);
  }, [tab]);

  const totalOutstanding = invoices
    .filter((i) => i.status !== "paid")
    .reduce((s, i) => s + i.amount, 0);
  const overdueCount = invoices.filter((i) => i.status === "overdue").length;
  const paidThisMonth = invoices
    .filter((i) => i.status === "paid")
    .reduce((s, i) => s + i.amount, 0);

  return (
    <div
      style={{ background: BG, minHeight: "100vh", fontFamily: fontSans }}
      className="flex"
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
        * { box-sizing: border-box; }
      `}</style>

      {/* Sidebar */}
      <aside
        className="hidden md:flex flex-col justify-between shrink-0"
        style={{ width: 220, background: INK, minHeight: "100vh" }}
      >
        <div>
          <div className="px-5 pt-6 pb-8">
            <div
              className="rounded-md inline-flex items-center justify-center mb-1"
              style={{ width: 8, height: 8, background: MINT }}
            />
            <div style={{ fontFamily: fontSans, fontWeight: 600, fontSize: 15, color: "#fff", marginTop: 8 }}>
              Nova Collaborative
            </div>
            <div style={{ fontFamily: fontMono, fontSize: 10.5, color: "#7FA3A0", marginTop: 2, letterSpacing: 0.5 }}>
              CONTRACT SAFETY TRACKER
            </div>
          </div>
          <nav className="flex flex-col gap-0.5 px-3">
            {NAV.map((item) => (
              <button
                key={item.label}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors"
                style={{
                  background: item.active ? "rgba(23,184,144,0.14)" : "transparent",
                  color: item.active ? MINT : "#9FB8B5",
                }}
              >
                <item.icon size={16} strokeWidth={2} />
                <span style={{ fontFamily: fontSans, fontSize: 13.5, fontWeight: 500 }}>
                  {item.label}
                </span>
              </button>
            ))}
          </nav>
        </div>
        <div className="px-5 pb-6">
          <div
            className="rounded-lg p-3.5"
            style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle size={13} color={AMBER} />
              <span style={{ fontFamily: fontSans, fontSize: 11.5, fontWeight: 600, color: "#fff" }}>
                2 invoices overdue
              </span>
            </div>
            <p style={{ fontFamily: fontSans, fontSize: 11, color: "#9FB8B5", lineHeight: 1.5, margin: 0 }}>
              Send a reminder before they age past 14 days.
            </p>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 min-w-0">
        {/* Topbar */}
        <div
          className="flex items-center justify-between px-5 md:px-8 py-4 sticky top-0 z-10"
          style={{ background: BG, borderBottom: `1px solid ${BORDER}` }}
        >
          <div>
            <h1 style={{ fontFamily: fontSans, fontSize: 18, fontWeight: 600, color: INK, margin: 0 }}>
              Good afternoon, Chinazo
            </h1>
            <p style={{ fontFamily: fontSans, fontSize: 12.5, color: MUTED, margin: 0, marginTop: 2 }}>
              Here's where your contracts and payments stand today.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              className="hidden sm:flex items-center gap-2 rounded-lg px-3 py-2"
              style={{ background: CARD, border: `1px solid ${BORDER}` }}
            >
              <Search size={14} color={MUTED} />
              <span style={{ fontFamily: fontSans, fontSize: 12.5, color: MUTED }}>Search</span>
            </button>
            <button
              className="relative flex items-center justify-center rounded-lg"
              style={{ width: 36, height: 36, background: CARD, border: `1px solid ${BORDER}` }}
            >
              <Bell size={15} color={MUTED} />
              <span
                className="absolute rounded-full"
                style={{ width: 7, height: 7, background: CORAL, top: 7, right: 8 }}
              />
            </button>
            <button
              className="flex items-center gap-2 rounded-lg px-3.5 py-2"
              style={{ background: TEAL, color: "#fff" }}
            >
              <Upload size={14} />
              <span style={{ fontFamily: fontSans, fontSize: 12.5, fontWeight: 600 }}>
                Upload contract
              </span>
            </button>
          </div>
        </div>

        <div className="px-5 md:px-8 py-6 flex flex-col gap-6">
          {/* Stat row */}
          <div className="flex flex-wrap gap-3.5">
            <StatCard icon={Wallet} label="Total outstanding" value={naira(totalOutstanding)} accent={TEAL} sub="across 4 invoices" />
            <StatCard icon={AlertTriangle} label="Overdue" value={overdueCount} accent={CORAL} sub="oldest: 11 days late" />
            <StatCard icon={CheckCircle2} label="Paid this month" value={naira(paidThisMonth)} accent={MINT} sub="2 invoices settled" />
            <StatCard icon={FolderOpen} label="Active contracts" value="6" accent={TEAL_DEEP} sub="1 pending signature" />
          </div>

          {/* Health + Invoices */}
          <div className="grid gap-5" style={{ gridTemplateColumns: "minmax(260px, 320px) 1fr" }}>
            {/* Payment Health card — signature element */}
            <div
              className="rounded-xl p-5 flex flex-col items-center"
              style={{ background: CARD, border: `1px solid ${BORDER}` }}
            >
              <div className="flex items-center gap-2 self-start mb-1">
                <TrendingUp size={14} color={TEAL} />
                <span style={{ fontFamily: fontSans, fontSize: 12.5, fontWeight: 600, color: INK }}>
                  Payment health
                </span>
              </div>
              <p style={{ fontFamily: fontSans, fontSize: 11, color: MUTED, alignSelf: "flex-start", marginTop: 0, marginBottom: 14 }}>
                Your on-time rate vs. the researched baseline
              </p>
              <PaymentHealthRing value={78} baseline={40} />
              <div
                className="mt-5 w-full rounded-lg px-3 py-2.5"
                style={{ background: "#E4F6F0" }}
              >
                <p style={{ fontFamily: fontSans, fontSize: 11, color: TEAL_DEEP, margin: 0, lineHeight: 1.5 }}>
                  <strong>38 pts above baseline.</strong> Consistent invoicing and
                  reminders are keeping late payments below the industry norm.
                </p>
              </div>
            </div>

            {/* Invoices */}
            <div
              className="rounded-xl p-5"
              style={{ background: CARD, border: `1px solid ${BORDER}` }}
            >
              <div className="flex items-center justify-between mb-3">
                <span style={{ fontFamily: fontSans, fontSize: 13.5, fontWeight: 600, color: INK }}>
                  Invoices
                </span>
                <button className="flex items-center gap-1" style={{ color: TEAL }}>
                  <span style={{ fontFamily: fontSans, fontSize: 12, fontWeight: 600 }}>View all</span>
                  <ChevronRight size={13} />
                </button>
              </div>
              <div className="flex gap-1.5 mb-3">
                {["all", "overdue", "pending", "paid"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className="px-3 py-1.5 rounded-full capitalize"
                    style={{
                      fontFamily: fontSans,
                      fontSize: 11.5,
                      fontWeight: 600,
                      background: tab === t ? INK : BORDER_SOFT,
                      color: tab === t ? "#fff" : MUTED,
                    }}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <div>
                {filtered.map((inv) => (
                  <InvoiceRow key={inv.id} inv={inv} />
                ))}
              </div>
            </div>
          </div>

          {/* Milestones + Activity */}
          <div className="grid gap-5" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div
              className="rounded-xl p-5"
              style={{ background: CARD, border: `1px solid ${BORDER}` }}
            >
              <div className="flex items-center gap-2 mb-4">
                <MilestoneIcon size={14} color={TEAL} />
                <span style={{ fontFamily: fontSans, fontSize: 13.5, fontWeight: 600, color: INK }}>
                  Upcoming milestones
                </span>
              </div>
              <div className="flex flex-col gap-3.5">
                {milestones.map((m, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div
                      className="rounded-full flex items-center justify-center shrink-0 mt-0.5"
                      style={{
                        width: 16,
                        height: 16,
                        background: m.done ? MINT : "transparent",
                        border: m.done ? "none" : `1.5px solid ${BORDER}`,
                      }}
                    >
                      {m.done && <CheckCircle2 size={16} color={MINT} strokeWidth={2.4} />}
                    </div>
                    <div className="flex-1">
                      <div
                        style={{
                          fontFamily: fontSans,
                          fontSize: 12.5,
                          color: m.done ? MUTED : INK,
                          fontWeight: 500,
                          textDecoration: m.done ? "line-through" : "none",
                        }}
                      >
                        {m.title}
                      </div>
                      <div style={{ fontFamily: fontSans, fontSize: 11, color: MUTED, marginTop: 1 }}>
                        {m.project}
                      </div>
                    </div>
                    <span style={{ fontFamily: fontMono, fontSize: 10.5, color: MUTED }}>
                      {m.date}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div
              className="rounded-xl p-5"
              style={{ background: CARD, border: `1px solid ${BORDER}` }}
            >
              <div className="flex items-center gap-2 mb-4">
                <Clock size={14} color={TEAL} />
                <span style={{ fontFamily: fontSans, fontSize: 13.5, fontWeight: 600, color: INK }}>
                  Recent activity
                </span>
              </div>
              <div className="flex flex-col gap-3.5">
                {activity.map((a, i) => {
                  const dot =
                    a.tone === "danger" ? CORAL : a.tone === "success" ? MINT : BORDER;
                  return (
                    <div key={i} className="flex items-start gap-3">
                      <span
                        className="rounded-full mt-1.5 shrink-0"
                        style={{ width: 6, height: 6, background: dot }}
                      />
                      <div className="flex-1">
                        <div style={{ fontFamily: fontSans, fontSize: 12.5, color: INK }}>
                          {a.text}
                        </div>
                      </div>
                      <span style={{ fontFamily: fontMono, fontSize: 10.5, color: MUTED, whiteSpace: "nowrap" }}>
                        {a.time}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
