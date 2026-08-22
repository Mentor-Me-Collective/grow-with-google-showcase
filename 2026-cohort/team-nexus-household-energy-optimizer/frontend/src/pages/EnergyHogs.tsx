import { useOutletContext } from "react-router-dom";
import { Award, Calculator, Globe, Lightbulb, PiggyBank, Wrench } from "lucide-react";
import type { EnergyContext } from "../context";
import { TopHogsCard } from "../components/TopHogsCard";

const RESOURCES = [
  {
    icon: Award,
    title: "ENERGY STAR product finder",
    body: "Compare energy-efficient appliances before you replace your biggest draw.",
    href: "https://www.energystar.gov/",
  },
  {
    icon: Wrench,
    title: "DOE Energy Saver guide",
    body: "Practical, room-by-room tips from the U.S. Department of Energy.",
    href: "https://www.energy.gov/energysaver",
  },
  {
    icon: PiggyBank,
    title: "DSIRE incentive database",
    body: "Look up rebates and incentives for efficiency upgrades in your area.",
    href: "https://www.dsireusa.org/",
  },
  {
    icon: Lightbulb,
    title: "Energy Saving Trust",
    body: "Independent, UK-based energy saving advice that applies well beyond the UK.",
    href: "https://energysavingtrust.org.uk/",
  },
  {
    icon: Globe,
    title: "International Energy Agency",
    body: "Global energy data and policy context if you're comparing across countries.",
    href: "https://www.iea.org/",
  },
  {
    icon: Calculator,
    title: "Rewiring America",
    body: "A nonprofit calculator for what electrifying appliances could save you long-term.",
    href: "https://www.rewiringamerica.org/",
  },
];

function hogsSubtitle(count: number): string {
  if (count === 1) return "Your biggest monthly draw in your current scenario, with a tailored tip.";
  if (count === 2) return "Your two biggest monthly draws in your current scenario, with a tailored tip for each.";
  if (count >= 3) return "Your top 3 biggest monthly draws in your current scenario, with a tailored tip for each.";
  return "See what's driving your bill the most, with a tailored tip for each appliance.";
}

export function EnergyHogs() {
  const { hogs, formatCost } = useOutletContext<EnergyContext>();

  return (
    <div className="page">
      <div className="page-header">
        <h1>Top energy hogs</h1>
        <p className="page-subtitle">{hogsSubtitle(hogs.length)}</p>
      </div>
      <TopHogsCard hogs={hogs} formatCost={formatCost} />

      <div className="section-label">Helpful resources</div>
      <p className="section-intro">
        A few reputable places to go deeper once you know what to target.
      </p>
      <div className="resources-grid">
        {RESOURCES.map((resource) => {
          const Icon = resource.icon;
          return (
            <a
              href={resource.href}
              target="_blank"
              rel="noreferrer"
              className="card step-card"
              key={resource.title}
            >
              <div className="step-top">
                <span className="step-icon">
                  <Icon size={20} strokeWidth={1.75} />
                </span>
              </div>
              <div className="step-title">{resource.title}</div>
              <p className="step-body">{resource.body}</p>
            </a>
          );
        })}
      </div>
    </div>
  );
}
