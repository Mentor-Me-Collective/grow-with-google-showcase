import { useEffect, useMemo, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import type { Appliance, BaselineProfile, Region } from "./types";
import { fetchAppliances, fetchBaselineProfiles, fetchRegions } from "./lib/api";
import {
  buildBreakdown,
  buildProfileHours,
  energyScore,
  formatCurrency,
  monthlyCarbonLbs,
  topEnergyHogs,
  totalKwh,
  type HoursByCategory,
} from "./lib/calculations";
import { applyTheme, getStoredTheme, type ThemePreference } from "./lib/theme";
import { applyTextSize, getStoredTextSize, type TextSizePreference } from "./lib/textSize";
import { speak, stopSpeaking } from "./lib/readAloud";
import { TopBar } from "./components/TopBar";
import { Footer } from "./components/Footer";
import { PrintableReport } from "./components/PrintableReport";
import { AccessibilityPanel } from "./components/AccessibilityPanel";
import type { EnergyContext, NewApplianceInput } from "./context";

let customApplianceSeq = 0;

interface EnergyData {
  catalog: Appliance[];
  baselineProfiles: BaselineProfile[];
  regions: Region[];
}

export function Layout() {
  const [data, setData] = useState<EnergyData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchAppliances(), fetchBaselineProfiles(), fetchRegions()])
      .then(([catalog, baselineProfiles, regions]) => {
        if (!cancelled) setData({ catalog, baselineProfiles, regions });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : "Failed to load energy data.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loadError) {
    return (
      <div className="loading-state">
        <p>Couldn&rsquo;t reach the Tenant Power Tracker backend.</p>
        <p className="loading-state-detail">{loadError}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="loading-state">
        <p>Loading your energy data&hellip;</p>
      </div>
    );
  }

  return (
    <LayoutReady catalog={data.catalog} baselineProfiles={data.baselineProfiles} regions={data.regions} />
  );
}

interface LayoutReadyProps {
  catalog: Appliance[];
  baselineProfiles: BaselineProfile[];
  regions: Region[];
}

function LayoutReady({ catalog, baselineProfiles, regions }: LayoutReadyProps) {
  const { pathname } = useLocation();
  const [theme, setTheme] = useState<ThemePreference>(() => getStoredTheme());
  const [textSize, setTextSize] = useState<TextSizePreference>(() => getStoredTextSize());
  const [a11yOpen, setA11yOpen] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const initialBaselineProfile =
    baselineProfiles.find((profile) => profile.id === "1-bed-apartment") ?? baselineProfiles[0];
  const [baselineId, setBaselineId] = useState(initialBaselineProfile.id);
  const [regionId, setRegionId] = useState(regions[0].id);
  const [appliances, setAppliances] = useState<Appliance[]>(catalog);
  const [hours, setHours] = useState<HoursByCategory>(() =>
    buildProfileHours(catalog, initialBaselineProfile),
  );

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    applyTextSize(textSize);
  }, [textSize]);

  useEffect(() => {
    stopSpeaking();
    setIsReading(false);
  }, [pathname]);

  useEffect(() => {
    return () => stopSpeaking();
  }, []);

  const baselineProfile =
    baselineProfiles.find((profile) => profile.id === baselineId) ?? baselineProfiles[0];
  const region = regions.find((candidate) => candidate.id === regionId) ?? regions[0];

  const defaultBreakdown = useMemo(
    () => buildBreakdown(buildProfileHours(appliances, baselineProfile), appliances, region.ratePerKwh),
    [appliances, baselineProfile, region.ratePerKwh],
  );
  const userBreakdown = useMemo(
    () => buildBreakdown(hours, appliances, region.ratePerKwh),
    [hours, appliances, region.ratePerKwh],
  );

  const defaultCost = defaultBreakdown.reduce((sum, item) => sum + item.cost, 0);
  const userCost = userBreakdown.reduce((sum, item) => sum + item.cost, 0);
  const defaultKwh = totalKwh(defaultBreakdown);
  const userKwh = totalKwh(userBreakdown);
  const defaultCarbonLbs = monthlyCarbonLbs(defaultKwh, region.carbonLbsPerKwh);
  const carbonLbs = monthlyCarbonLbs(userKwh, region.carbonLbsPerKwh);
  const score = energyScore(userKwh, defaultKwh);
  const hogs = topEnergyHogs(userBreakdown, 3);
  const removableIds = new Set(appliances.map((appliance) => appliance.id));
  const removedBuiltins = catalog.filter((appliance) => !removableIds.has(appliance.id));

  function formatCost(value: number): string {
    return formatCurrency(value, region.currency, region.locale);
  }

  function handleHoursChange(id: string, value: number) {
    setHours((prev) => ({ ...prev, [id]: value }));
  }

  /** Switching home size resets the sliders to that profile's typical hours, so the change is actually visible. */
  function handleBaselineChange(id: string) {
    setBaselineId(id);
    const profile = baselineProfiles.find((candidate) => candidate.id === id) ?? baselineProfiles[0];
    setHours(buildProfileHours(appliances, profile));
  }

  /** Adds a removed built-in appliance back with its real wattage/tip, no retyping needed. */
  function handleReAddAppliance(id: string) {
    const original = catalog.find((appliance) => appliance.id === id);
    if (!original) return;
    setAppliances((prev) => [...prev, original]);
    setHours((prev) => ({ ...prev, [id]: baselineProfile.hoursByAppliance[id] ?? original.defaultHours }));
  }

  function handleAddAppliance(input: NewApplianceInput) {
    customApplianceSeq += 1;
    const id = `custom-${customApplianceSeq}`;
    const appliance: Appliance = {
      id,
      label: input.label,
      watts: input.watts,
      defaultHours: 1,
      minHours: 0,
      maxHours: 24,
      tip: "Consider cutting its hours or unplugging it when idle, every hour off is a direct saving.",
    };
    setAppliances((prev) => [...prev, appliance]);
    setHours((prev) => ({ ...prev, [id]: 1 }));
  }

  function handleRemoveAppliance(id: string) {
    setAppliances((prev) => prev.filter((appliance) => appliance.id !== id));
    setHours((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  }

  function handleUpdateWatts(id: string, watts: number) {
    setAppliances((prev) =>
      prev.map((appliance) => (appliance.id === id ? { ...appliance, watts } : appliance)),
    );
  }

  function handleUpdateQuantity(id: string, quantity: number) {
    setAppliances((prev) =>
      prev.map((appliance) => (appliance.id === id ? { ...appliance, quantity } : appliance)),
    );
  }

  /** Empties the list entirely. Removed built-ins remain available as one-tap re-add chips. */
  function handleClearAll() {
    setAppliances([]);
    setHours({});
  }

  function handleReadAloud() {
    const text = document.querySelector<HTMLElement>(".page-content")?.innerText ?? "";
    setIsReading(true);
    speak(text, () => setIsReading(false));
  }

  function handleStopReading() {
    stopSpeaking();
    setIsReading(false);
  }

  const context: EnergyContext = {
    hours,
    onHoursChange: handleHoursChange,
    baselineProfile,
    region,
    formatCost,
    defaultBreakdown,
    userBreakdown,
    defaultCost,
    userCost,
    defaultKwh,
    userKwh,
    defaultCarbonLbs,
    carbonLbs,
    score,
    hogs,
    appliances,
    onAddAppliance: handleAddAppliance,
    onRemoveAppliance: handleRemoveAppliance,
    onUpdateWatts: handleUpdateWatts,
    onUpdateQuantity: handleUpdateQuantity,
    onClearAll: handleClearAll,
    removedBuiltins,
    onReAddAppliance: handleReAddAppliance,
  };

  return (
    <div className="app-shell">
      <div className="a11y-zoom-scope">
        <TopBar
          baselineId={baselineId}
          onBaselineChange={handleBaselineChange}
          baselineProfiles={baselineProfiles}
          regionId={regionId}
          onRegionChange={setRegionId}
          regions={regions}
          theme={theme}
          onThemeChange={setTheme}
          textSize={textSize}
          onTextSizeChange={setTextSize}
          isReading={isReading}
          onReadAloud={handleReadAloud}
          onStopReading={handleStopReading}
          a11yOpen={a11yOpen}
          onA11yOpenChange={setA11yOpen}
        />
        <main className="page-content">
          <Outlet context={context} />
        </main>
        <Footer />
        <PrintableReport
          score={score}
          baselineLabel={baselineProfile.label}
          regionLabel={region.label}
          formatCost={formatCost}
          userCost={userCost}
          userKwh={userKwh}
          carbonLbs={carbonLbs}
          userBreakdown={userBreakdown}
          hogs={hogs}
        />
      </div>
      <AccessibilityPanel
        open={a11yOpen}
        onClose={() => setA11yOpen(false)}
        theme={theme}
        onThemeChange={setTheme}
        textSize={textSize}
        onTextSizeChange={setTextSize}
        isReading={isReading}
        onReadAloud={handleReadAloud}
        onStopReading={handleStopReading}
      />
    </div>
  );
}
