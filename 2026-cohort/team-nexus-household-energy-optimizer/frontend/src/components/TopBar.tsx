import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Accessibility, Flame, Gauge, Menu, SlidersHorizontal, X } from "lucide-react";
import type { BaselineProfile, Region } from "../types";
import type { ThemePreference } from "../lib/theme";
import type { TextSizePreference } from "../lib/textSize";
import { AccessibilityControls } from "./AccessibilityControls";

const NAV_ITEMS = [
  { to: "/simulator", label: "Simulator", icon: SlidersHorizontal },
  { to: "/score", label: "Score", icon: Gauge },
  { to: "/hogs", label: "Energy Hogs", icon: Flame },
];

interface TopBarProps {
  baselineId: string;
  onBaselineChange: (id: string) => void;
  baselineProfiles: BaselineProfile[];
  regionId: string;
  onRegionChange: (id: string) => void;
  regions: Region[];
  theme: ThemePreference;
  onThemeChange: (value: ThemePreference) => void;
  textSize: TextSizePreference;
  onTextSizeChange: (value: TextSizePreference) => void;
  isReading: boolean;
  onReadAloud: () => void;
  onStopReading: () => void;
  a11yOpen: boolean;
  onA11yOpenChange: (open: boolean) => void;
}

export function TopBar({
  baselineId,
  onBaselineChange,
  baselineProfiles,
  regionId,
  onRegionChange,
  regions,
  theme,
  onThemeChange,
  textSize,
  onTextSizeChange,
  isReading,
  onReadAloud,
  onStopReading,
  a11yOpen,
  onA11yOpenChange,
}: TopBarProps) {
  const { pathname } = useLocation();
  const onHome = pathname === "/";
  const [menuOpen, setMenuOpen] = useState(false);

  const baselineSelect = (
    <select
      className="select select-compact"
      aria-label="Household profile"
      value={baselineId}
      onChange={(event) => onBaselineChange(event.target.value)}
    >
      {baselineProfiles.map((profile) => (
        <option key={profile.id} value={profile.id}>
          {profile.label}
        </option>
      ))}
    </select>
  );

  const regionSelect = (
    <select
      className="select select-compact"
      aria-label="Region (rate and grid mix)"
      value={regionId}
      onChange={(event) => onRegionChange(event.target.value)}
    >
      {regions.map((region) => (
        <option key={region.id} value={region.id}>
          {region.label}
        </option>
      ))}
    </select>
  );

  return (
    <header className="top-bar">
      <div className="top-bar-row">
        <NavLink to="/" className={onHome ? "brand active" : "brand"} onClick={() => setMenuOpen(false)}>
          <img src="/favicon.svg" alt="" className="brand-logo" width={20} height={19} />
          Tenant Power Tracker
        </NavLink>

        <nav className="nav-bar" aria-label="Primary">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
              >
                <Icon size={16} strokeWidth={1.75} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="top-bar-controls">
          {baselineSelect}
          {regionSelect}
          <button
            type="button"
            className="a11y-trigger"
            aria-label="Display and accessibility settings"
            aria-haspopup="dialog"
            aria-expanded={a11yOpen}
            onClick={() => onA11yOpenChange(true)}
          >
            <Accessibility size={18} strokeWidth={1.75} />
          </button>
        </div>

        <button
          type="button"
          className="menu-toggle"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X size={20} strokeWidth={1.75} /> : <Menu size={20} strokeWidth={1.75} />}
        </button>
      </div>

      {menuOpen && (
        <div className="mobile-menu">
          <nav className="mobile-nav" aria-label="Primary">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
                  onClick={() => setMenuOpen(false)}
                >
                  <Icon size={16} strokeWidth={1.75} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
          <div className="mobile-controls">
            {baselineSelect}
            {regionSelect}
          </div>
          <div className="mobile-a11y">
            <AccessibilityControls
              theme={theme}
              onThemeChange={onThemeChange}
              textSize={textSize}
              onTextSizeChange={onTextSizeChange}
              isReading={isReading}
              onReadAloud={onReadAloud}
              onStopReading={onStopReading}
            />
          </div>
        </div>
      )}
    </header>
  );
}
