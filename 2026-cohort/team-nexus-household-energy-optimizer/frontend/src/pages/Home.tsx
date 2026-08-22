import { Link, useOutletContext } from "react-router-dom";
import {
  DollarSign,
  Flame,
  Gauge,
  Leaf,
  PlugZap,
  SlidersHorizontal,
  TrendingDown,
  Zap,
} from "lucide-react";
import type { EnergyContext } from "../context";
import { buildDelta, formatKwh } from "../lib/calculations";
import { EnergyScoreCard } from "../components/EnergyScoreCard";
import { StatTile } from "../components/StatTile";

const STEPS = [
  {
    to: "/simulator",
    num: "01",
    icon: SlidersHorizontal,
    title: "Simulate your usage",
    body: "Drag sliders for 11 built-in appliances, fridge, AC, washer, TV, and more, or add your own to match your real routine.",
  },
  {
    to: "/score",
    num: "02",
    icon: Gauge,
    title: "See your score",
    body: "Get a Personalized Energy Score against a household baseline, plus your cost, usage, and carbon footprint.",
  },
  {
    to: "/hogs",
    num: "03",
    icon: Flame,
    title: "Fix your energy hogs",
    body: "See your three biggest draws and a tailored tip to cut each one down.",
  },
];

const BENEFITS = [
  {
    icon: DollarSign,
    title: "Cut your bill",
    body: "See exactly which appliances cost you the most, and what changing them actually saves, before you commit to anything.",
  },
  {
    icon: PlugZap,
    title: "No hardware required",
    body: "No smart meters or smart plugs to buy or install. Just enter your usage and get real numbers back.",
  },
  {
    icon: TrendingDown,
    title: "Catch it before you owe it",
    body: "Your score and cost update live as you adjust, so you catch a costly habit before the bill arrives, not after.",
  },
];

export function Home() {
  const {
    score,
    baselineProfile,
    formatCost,
    userCost,
    defaultCost,
    userKwh,
    defaultKwh,
    carbonLbs,
    defaultCarbonLbs,
  } = useOutletContext<EnergyContext>();

  return (
    <div className="page">
      <section className="hero">
        <img src="/favicon.svg" alt="" className="hero-logo" width={44} height={42} />
        <h1 className="hero-title">Know exactly where your energy dollars go.</h1>
        <p className="hero-subtitle">
          Tenant Power Tracker estimates your monthly energy footprint from appliance usage,
          no smart meter required, and shows you where your money and carbon footprint are
          actually going.
        </p>
        <div className="hero-actions">
          <Link to="/simulator" className="btn btn-primary">
            <Zap size={16} strokeWidth={2} />
            Open the simulator
          </Link>
          <Link to="/score" className="btn btn-secondary">
            See your score
          </Link>
        </div>
      </section>

      <div className="section-label">Why it matters</div>
      <p className="section-intro">
        A Personalized Energy Score turns an abstract bill into something you can actually act
        on.
      </p>
      <div className="how-it-works">
        {BENEFITS.map((benefit) => {
          const Icon = benefit.icon;
          return (
            <div className="card step-card" key={benefit.title}>
              <div className="step-top">
                <span className="step-icon">
                  <Icon size={20} strokeWidth={1.75} />
                </span>
              </div>
              <div className="step-title">{benefit.title}</div>
              <p className="step-body">{benefit.body}</p>
            </div>
          );
        })}
      </div>

      <div className="narrative-card">
        <div className="narrative-eyebrow">Meet Alex</div>
        <p className="narrative-text">
          Alex lives alone in a one-bedroom apartment and was paying $142 a month without
          knowing why. Running the simulator, they found their window AC was cycling nearly 10
          hours a day, over half of their entire bill on its own. Dropping it to 6 hours and
          switching laundry to cold water brought their monthly cost down to $97, a $45
          difference, without changing anything about their day-to-day comfort. Their
          Personalized Energy Score went from 41 to 76 in the process, and it took less than
          five minutes of dragging sliders to find.
        </p>
      </div>

      <div className="section-label">How it works</div>
      <p className="section-intro">
        The same three steps that got Alex there, applied to your own usage.
      </p>
      <div className="how-it-works">
        {STEPS.map((step) => {
          const Icon = step.icon;
          return (
            <Link to={step.to} className="card step-card" key={step.to}>
              <div className="step-top">
                <span className="step-icon">
                  <Icon size={20} strokeWidth={1.75} />
                </span>
                <span className="step-num">{step.num}</span>
              </div>
              <div className="step-title">{step.title}</div>
              <p className="step-body">{step.body}</p>
            </Link>
          );
        })}
      </div>

      <div className="section-label">Your current snapshot</div>
      <p className="section-intro">
        Based on the default appliance schedule, your numbers, ready whenever you are.
      </p>
      <div className="stat-grid">
        <EnergyScoreCard score={score} baselineLabel={baselineProfile.label} />
        <StatTile
          icon={DollarSign}
          label="Monthly cost"
          value={formatCost(userCost)}
          delta={buildDelta(userCost, defaultCost, formatCost)}
        />
        <StatTile
          icon={Zap}
          label="Monthly usage"
          value={formatKwh(userKwh)}
          delta={buildDelta(userKwh, defaultKwh, formatKwh)}
        />
        <StatTile
          icon={Leaf}
          label="Carbon footprint"
          value={`${carbonLbs.toFixed(0)} lbs CO2`}
          delta={buildDelta(carbonLbs, defaultCarbonLbs, (v) => `${v.toFixed(0)} lbs`)}
        />
      </div>
    </div>
  );
}
