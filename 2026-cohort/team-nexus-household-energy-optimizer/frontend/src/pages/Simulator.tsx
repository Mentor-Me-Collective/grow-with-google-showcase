import { useEffect, useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import type { EnergyContext } from "../context";
import { UsageSimulator } from "../components/UsageSimulator";
import { SavingsChart } from "../components/SavingsChart";
import { ScoreSummaryBar } from "../components/ScoreSummaryBar";
import { MiniScoreCard } from "../components/MiniScoreCard";
import { StickyColumn } from "../components/StickyColumn";

export function Simulator() {
  const {
    hours,
    onHoursChange,
    defaultCost,
    userCost,
    score,
    baselineProfile,
    region,
    formatCost,
    appliances,
    onAddAppliance,
    onRemoveAppliance,
    onUpdateWatts,
    onUpdateQuantity,
    onClearAll,
    removedBuiltins,
    onReAddAppliance,
  } = useOutletContext<EnergyContext>();

  const scoreBannerRef = useRef<HTMLDivElement>(null);
  const [scoreBannerVisible, setScoreBannerVisible] = useState(true);

  useEffect(() => {
    const node = scoreBannerRef.current;
    if (!node) return;
    const observer = new IntersectionObserver(([entry]) => setScoreBannerVisible(entry.isIntersecting), {
      rootMargin: "-84px 0px 0px 0px", // account for the sticky top bar covering the same slice of viewport
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Usage simulator</h1>
        <p className="page-subtitle">
          Adjust how much you actually run each appliance, per day or per week, and watch your
          monthly cost update live. Rates and grid mix are based on {region.label}.
        </p>
      </div>

      <div ref={scoreBannerRef}>
        <ScoreSummaryBar score={score} baselineLabel={baselineProfile.label} />
      </div>

      <div className="main-grid">
        <UsageSimulator
          hours={hours}
          onChange={onHoursChange}
          appliances={appliances}
          onAddAppliance={onAddAppliance}
          onRemoveAppliance={onRemoveAppliance}
          onUpdateWatts={onUpdateWatts}
          onUpdateQuantity={onUpdateQuantity}
          onClearAll={onClearAll}
          removedBuiltins={removedBuiltins}
          onReAddAppliance={onReAddAppliance}
        />
        <StickyColumn watch={`${appliances.length}-${scoreBannerVisible}`}>
          <SavingsChart defaultCost={defaultCost} simulatedCost={userCost} formatCost={formatCost} />
          {!scoreBannerVisible && (
            <MiniScoreCard score={score} baselineLabel={baselineProfile.label} />
          )}
        </StickyColumn>
      </div>
    </div>
  );
}
