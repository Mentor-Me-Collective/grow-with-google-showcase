import { useState } from "react";
import { Eraser, Plus, Trash2 } from "lucide-react";
import type { Appliance } from "../types";
import type { HoursByCategory } from "../lib/calculations";
import type { NewApplianceInput } from "../context";
import { getApplianceIcon } from "./applianceIcons";

/** Appliances whose real-world usage is naturally weekly (loads/sessions), not a daily habit. */
const WEEKLY_DEFAULT_IDS = new Set(["washing-machine", "clothes-dryer", "dishwasher", "gaming-console"]);

interface UsageSimulatorProps {
  hours: HoursByCategory;
  onChange: (id: string, hours: number) => void;
  appliances: Appliance[];
  onAddAppliance: (input: NewApplianceInput) => void;
  onRemoveAppliance: (id: string) => void;
  onUpdateWatts: (id: string, watts: number) => void;
  onUpdateQuantity: (id: string, quantity: number) => void;
  onClearAll: () => void;
  removedBuiltins: Appliance[];
  onReAddAppliance: (id: string) => void;
}

interface ApplianceRowProps {
  appliance: Appliance;
  hours: number;
  onChange: (id: string, hours: number) => void;
  onRemove: (id: string) => void;
  onUpdateWatts: (id: string, watts: number) => void;
  onUpdateQuantity: (id: string, quantity: number) => void;
}

function ApplianceRow({ appliance, hours, onChange, onRemove, onUpdateWatts, onUpdateQuantity }: ApplianceRowProps) {
  const Icon = getApplianceIcon(appliance.id, appliance.category);
  const [wattsInput, setWattsInput] = useState(String(appliance.watts));
  const [qtyInput, setQtyInput] = useState(String(appliance.quantity ?? 1));
  const [unit, setUnit] = useState<"day" | "week">(() => (WEEKLY_DEFAULT_IDS.has(appliance.id) ? "week" : "day"));

  function commitWatts() {
    const parsed = Number(wattsInput);
    if (Number.isFinite(parsed) && parsed > 0) {
      const clamped = Math.min(10000, Math.max(1, Math.round(parsed)));
      onUpdateWatts(appliance.id, clamped);
      setWattsInput(String(clamped));
    } else {
      setWattsInput(String(appliance.watts));
    }
  }

  function commitQuantity() {
    const parsed = Number(qtyInput);
    if (Number.isFinite(parsed) && parsed > 0) {
      const clamped = Math.min(20, Math.max(1, Math.round(parsed)));
      onUpdateQuantity(appliance.id, clamped);
      setQtyInput(String(clamped));
    } else {
      setQtyInput(String(appliance.quantity ?? 1));
    }
  }

  /** In week mode the slider operates in whole hours/week, so onChange still hands the shared hours/day math its usual value. */
  const isWeek = unit === "week";
  const sliderMax = isWeek ? appliance.maxHours * 7 : appliance.maxHours;
  const sliderValue = isWeek ? Math.round(hours * 7) : hours;

  function handleSliderChange(value: number) {
    onChange(appliance.id, isWeek ? value / 7 : value);
  }

  function toggleUnit() {
    setUnit((prev) => (prev === "day" ? "week" : "day"));
  }

  return (
    <div className="slider-row">
      <div className="slider-row-head">
        <Icon className="slider-row-icon" size={18} strokeWidth={1.75} />
        <span className="slider-row-label">{appliance.label}</span>
        <span className="qty-field">
          <span className="qty-unit">&times;</span>
          <input
            type="number"
            className="qty-input"
            min={1}
            max={20}
            value={qtyInput}
            onChange={(event) => setQtyInput(event.target.value)}
            onBlur={commitQuantity}
            onKeyDown={(event) => {
              if (event.key === "Enter") event.currentTarget.blur();
            }}
            aria-label={`${appliance.label} quantity`}
          />
        </span>
        <span className="watts-field">
          <input
            type="number"
            className="watts-input"
            min={1}
            max={10000}
            value={wattsInput}
            onChange={(event) => setWattsInput(event.target.value)}
            onBlur={commitWatts}
            onKeyDown={(event) => {
              if (event.key === "Enter") event.currentTarget.blur();
            }}
            aria-label={`${appliance.label} wattage`}
          />
          <span className="watts-unit">W</span>
        </span>
        <button
          type="button"
          className="slider-row-value slider-row-value-toggle"
          onClick={toggleUnit}
          title={isWeek ? `≈ ${hours.toFixed(2)} hrs/day, click to switch to /day` : "Click to switch to /week"}
        >
          <span className="slider-row-value-text">
            {isWeek ? `${sliderValue} hrs/wk` : `${hours > 0 && hours < 1 ? hours.toFixed(2) : hours.toFixed(0)} hrs/day`}
          </span>
        </button>
        <button
          type="button"
          className="slider-row-remove"
          aria-label={`Remove ${appliance.label}`}
          onClick={() => onRemove(appliance.id)}
        >
          <Trash2 size={15} strokeWidth={1.75} />
        </button>
      </div>
      <input
        type="range"
        min={0}
        max={sliderMax}
        step={1}
        value={sliderValue}
        aria-label={`${appliance.label} hours per ${unit}`}
        onChange={(event) => handleSliderChange(Number(event.target.value))}
      />
    </div>
  );
}

export function UsageSimulator({
  hours,
  onChange,
  appliances,
  onAddAppliance,
  onRemoveAppliance,
  onUpdateWatts,
  onUpdateQuantity,
  onClearAll,
  removedBuiltins,
  onReAddAppliance,
}: UsageSimulatorProps) {
  const [newLabel, setNewLabel] = useState("");
  const [newWatts, setNewWatts] = useState("");

  const watts = Number(newWatts);
  const canAdd = newLabel.trim().length > 0 && watts > 0 && watts <= 10000;

  function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    if (!canAdd) return;
    onAddAppliance({ label: newLabel.trim(), watts });
    setNewLabel("");
    setNewWatts("");
  }

  function handleClearAll() {
    if (window.confirm("Remove every appliance? You can add them back individually anytime.")) {
      onClearAll();
    }
  }

  return (
    <div className="card">
      <div className="card-title-row">
        <div className="card-title">Usage simulator</div>
        {appliances.length > 0 && (
          <button type="button" className="btn btn-secondary btn-small" onClick={handleClearAll}>
            <Eraser size={13} strokeWidth={2} />
            Clear all
          </button>
        )}
      </div>
      <p className="card-subtitle">
        Drag each slider to match how much you actually run it, click the hours value to switch
        between per day and per week, and correct the wattage or quantity if yours differ. Remove
        anything you don't have.
      </p>
      {appliances.length === 0 && (
        <p className="muted-note">Nothing here yet, add an appliance below to get started.</p>
      )}
      {appliances.map((appliance) => (
        <ApplianceRow
          key={appliance.id}
          appliance={appliance}
          hours={hours[appliance.id] ?? appliance.defaultHours}
          onChange={onChange}
          onRemove={onRemoveAppliance}
          onUpdateWatts={onUpdateWatts}
          onUpdateQuantity={onUpdateQuantity}
        />
      ))}

      {removedBuiltins.length > 0 && (
        <div className="appliance-suggestions">
          <span className="appliance-suggestions-label">Add back:</span>
          {removedBuiltins.map((appliance) => (
            <button
              key={appliance.id}
              type="button"
              className="suggestion-chip"
              onClick={() => onReAddAppliance(appliance.id)}
            >
              <Plus size={13} strokeWidth={2} />
              {appliance.label}
            </button>
          ))}
        </div>
      )}

      <form className="add-appliance-form" onSubmit={handleAdd}>
        <div className="add-appliance-fields">
          <input
            type="text"
            className="input add-appliance-name"
            placeholder="Appliance name (e.g. Space heater)"
            maxLength={40}
            value={newLabel}
            onChange={(event) => setNewLabel(event.target.value)}
            aria-label="New appliance name"
          />
          <input
            type="number"
            className="input add-appliance-watts"
            placeholder="Watts"
            min={1}
            max={10000}
            value={newWatts}
            onChange={(event) => setNewWatts(event.target.value)}
            aria-label="New appliance wattage"
          />
        </div>
        <button type="submit" className="btn btn-secondary" disabled={!canAdd}>
          <Plus size={15} strokeWidth={2} />
          Add appliance
        </button>
      </form>
    </div>
  );
}
