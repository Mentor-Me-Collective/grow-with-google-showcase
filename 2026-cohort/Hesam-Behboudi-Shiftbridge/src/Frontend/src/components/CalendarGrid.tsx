import React, { useMemo, useState } from 'react';
import {
  Sparkles,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Briefcase,
} from 'lucide-react';
import type { Worker, DayOfWeek, ShiftInfo } from '../types';
import { DAYS_OF_WEEK } from '../types';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ROLE_OPTIONS = [
  'Senior RN',
  'Charge Nurse',
  'RN',
  'LPN',
  'Support Specialist',
] as const;

const ALL = 'ALL';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a fast lookup map: workerId -> day -> shift, plus per-worker totals. */
function buildScheduleIndex(schedule: ShiftInfo[]) {
  const byWorker = new Map<string, Map<DayOfWeek, ShiftInfo>>();

  for (const item of schedule) {
    let days = byWorker.get(item.worker_id);
    if (!days) {
      days = new Map();
      byWorker.set(item.worker_id, days);
    }
    days.set(item.day, item);
  }

  return byWorker;
}

function weeklyTotalHours(days: Map<DayOfWeek, ShiftInfo> | undefined): number {
  if (!days) return 0;
  let total = 0;
  for (const shift of days.values()) total += shift.length;
  return total;
}

function emptyShift(workerId: string, day: DayOfWeek): ShiftInfo {
  return {
    id: `${workerId}-${day}`,
    type: 'off',
    start_time: 'OFF',
    length: 0,
    worker_id: workerId,
    day,
  };
}

function hoursBadgeClass(total: number, max: number): string {
  if (total > max) return 'bg-rose-100 text-rose-800';
  if (total === max) return 'bg-slate-100 text-slate-800';
  return 'bg-indigo-50 text-indigo-700';
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const ShiftBadge: React.FC<{ shift: ShiftInfo; day: DayOfWeek }> = ({
  shift,
  day,
}) => {
  if (shift.type === 'off') {
    return (
      <div className="h-full w-full rounded-lg bg-slate-100/70 border border-slate-200/50 p-2 flex flex-col items-center justify-center text-slate-400 group-hover:bg-slate-200/60 transition-colors">
        <span className="text-[11px] font-semibold tracking-wide uppercase">
          OFF
        </span>
        {shift.note && (
          <span className="text-[9px] text-slate-400 text-center truncate max-w-full">
            {shift.note}
          </span>
        )}
      </div>
    );
  }

  if (shift.type === 'updated' || shift.updatedByAi) {
    return (
      <div className="h-full w-full rounded-lg bg-emerald-500/10 border-2 border-emerald-500 p-2 text-emerald-950 flex flex-col justify-between shadow-xs group-hover:bg-emerald-500/15 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-[9px] uppercase font-extrabold tracking-wider px-1.5 py-0.5 rounded bg-emerald-200 text-emerald-900 inline-flex items-center gap-0.5">
            <Sparkles className="w-2.5 h-2.5 text-emerald-700" />
            Updated via AI
          </span>
          <span className="text-[10px] font-bold text-emerald-800">
            {shift.length}h
          </span>
        </div>
        <div className="my-1">
          <div className="text-xs font-bold text-emerald-950">
            {shift.start_time}
          </div>
          {shift.note && (
            <div className="text-[10px] text-emerald-800 font-medium truncate">
              {shift.note}
            </div>
          )}
        </div>
        <div className="text-[9px] text-emerald-700 font-bold uppercase flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          Approved
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full rounded-lg bg-indigo-50/60 border border-indigo-100 hover:border-indigo-300 p-2 text-indigo-950 flex flex-col justify-between transition-all group-hover:shadow-xs">
      <div className="flex items-center justify-between text-[10px] text-indigo-700 font-medium">
        <span>{day.slice(0, 3)} Shift</span>
        <span className="font-semibold">{shift.length}h</span>
      </div>
      <div className="text-xs font-bold text-slate-800 my-0.5">
        {shift.start_time}
      </div>
      <div className="text-[10px] text-slate-500 truncate">Standard Roster</div>
    </div>
  );
};

const ManagerFilters: React.FC<{
  workers: Worker[];
  workerId: string;
  onWorkerIdChange: (id: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  role: string;
  onRoleChange: (role: string) => void;
}> = ({
  workers,
  workerId,
  onWorkerIdChange,
  searchQuery,
  onSearchChange,
  role,
  onRoleChange,
}) => (
  <div className="flex items-center gap-2.5 w-full lg:w-auto">
    <div className="relative">
      <select
        value={workerId}
        onChange={(e) => onWorkerIdChange(e.target.value)}
        data-testid="manager-worker-select"
        aria-label="Filter by Worker"
        className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
      >
        <option value={ALL}>All Workers ({workers.length})</option>
        {workers.map((w) => (
          <option key={w.id} value={w.id}>
            {w.name} ({w.role})
          </option>
        ))}
      </select>
    </div>

    <div className="relative flex-1 lg:w-44">
      <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        type="text"
        placeholder="Search worker..."
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      />
    </div>

    <div className="relative">
      <Filter className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
      <select
        value={role}
        onChange={(e) => onRoleChange(e.target.value)}
        aria-label="Filter by Role"
        className="pl-8 pr-6 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
      >
        <option value={ALL}>All Roles</option>
        {ROLE_OPTIONS.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
    </div>
  </div>
);

const ShiftDetailBar: React.FC<{
  detail: { worker: Worker; day: DayOfWeek; shift: ShiftInfo };
  onDismiss: () => void;
}> = ({ detail, onDismiss }) => (
  <div className="p-3 bg-white border-t border-slate-200 flex items-center justify-between text-xs text-slate-700">
    <div className="flex items-center gap-2">
      <Clock className="w-4 h-4 text-indigo-600" />
      <span>
        <strong>{detail.worker.name}</strong> on <strong>{detail.day}</strong>:{' '}
        {detail.shift.start_time} ({detail.shift.length} hrs)
      </span>
      {detail.shift.note && <span>{detail.shift.note}</span>}
    </div>
    <button
      onClick={onDismiss}
      className="text-slate-400 hover:text-slate-700 px-2 py-0.5 rounded text-xs cursor-pointer"
    >
      Dismiss
    </button>
  </div>
);

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface CalendarGridProps {
  workers?: Worker[];
  schedule: ShiftInfo[];
  selectedDay?: DayOfWeek;
  onSelectShift?: (worker: Worker, day: DayOfWeek, shift: ShiftInfo) => void;
  appliedProposalTitle?: string | null;
  currentUser?: Worker;
  currentRole?: 'worker' | 'manager';
}

type ActiveDetail = { worker: Worker; day: DayOfWeek; shift: ShiftInfo } | null;

export const CalendarGrid: React.FC<CalendarGridProps> = ({
  workers = [],
  schedule,
  appliedProposalTitle,
  currentUser,
  currentRole = 'worker',
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>(ALL);
  const [selectedWorkerId, setSelectedWorkerId] = useState<string>(ALL);
  const [activeShiftDetail, setActiveShiftDetail] = useState<ActiveDetail>(null);

  const isManager = currentRole === 'manager';

  // Build the index once per schedule change — O(n) instead of O(n × 7) per row.
  const scheduleIndex = useMemo(() => buildScheduleIndex(schedule), [schedule]);

  // Apply role/visibility scope + manager filters in a single memoized pass.
  const visibleWorkers = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    return workers.filter((worker) => {
      // Scope by role.
      if (!isManager) {
        if (currentUser && worker.id !== currentUser.id) return false;
      } else {
        // Managers don't see themselves in the roster.
        if (currentUser && worker.id === currentUser.id) return false;
        if (selectedWorkerId !== ALL && worker.id !== selectedWorkerId) {
          return false;
        }
      }

      // Manager-only search / role filters.
      if (isManager) {
        if (selectedRole !== ALL && worker.role !== selectedRole) return false;
        if (normalizedQuery) {
          const haystack =
            `${worker.name} ${worker.role} ${worker.department}`.toLowerCase();
          if (!haystack.includes(normalizedQuery)) return false;
        }
      }

      return true;
    });
  }, [workers, isManager, currentUser, selectedWorkerId, selectedRole, searchQuery]);

  const title = isManager ? 'Staff Schedule' : 'My Weekly Schedule';

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Top Banner / Controls */}
      <div className="p-4 bg-white border-b border-slate-200 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              {title}
            </h2>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
              {isManager
                ? `${visibleWorkers.length} Personnel`
                : 'Personal View'}
            </span>
            {appliedProposalTitle && (
              <span className="hidden sm:inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                {appliedProposalTitle}
              </span>
            )}
          </div>
        </div>

        {isManager && (
          <ManagerFilters
            workers={workers}
            workerId={selectedWorkerId}
            onWorkerIdChange={setSelectedWorkerId}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            role={selectedRole}
            onRoleChange={setSelectedRole}
          />
        )}
      </div>

      {/* Schedule Legend */}
      <div className="bg-slate-100/70 border-b border-slate-200 px-4 py-2 flex flex-wrap items-center gap-4 text-xs text-slate-600">
        <span className="font-semibold text-slate-700 flex items-center gap-1">
          <Briefcase className="w-3.5 h-3.5 text-slate-500" /> Shift Legend:
        </span>
      </div>

      {/* Grid Container */}
      <div className="flex-1 overflow-x-auto overflow-y-auto">
        <table className="w-full min-w-[960px] border-collapse bg-white text-left">
          <thead className="sticky top-0 bg-slate-100/95 backdrop-blur-xs z-10 border-b border-slate-200 text-slate-700">
            <tr>
              <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider w-64 border-r border-slate-200">
                Worker / Qualifications
              </th>
              {DAYS_OF_WEEK.map((day) => (
                <th
                  key={day}
                  className="py-3 px-2 text-center text-xs font-bold uppercase tracking-wider border-r border-slate-200 last:border-r-0"
                >
                  <div className="flex flex-col items-center">
                    <span>{day}</span>
                  </div>
                </th>
              ))}
              <th className="py-3 px-3 text-center text-xs font-bold uppercase tracking-wider w-20">
                Hours
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200 text-xs">
            {visibleWorkers.map((worker) => {
              const days = scheduleIndex.get(worker.id);
              const totalHours = weeklyTotalHours(days);

              return (
                <tr
                  key={worker.id}
                  className="hover:bg-slate-50/80 transition-colors group"
                >
                  {/* Worker Information Column */}
                  <td className="py-2.5 px-4 border-r border-slate-200 bg-white group-hover:bg-slate-50/80 sticky left-0 z-5">
                    <div className="flex items-center gap-3">
                      <img
                        src={worker.avatar}
                        alt={worker.name}
                        className="w-9 h-9 rounded-full object-cover border border-slate-200 flex-shrink-0"
                      />
                      <div className="min-w-0">
                        <div className="font-bold text-slate-900 truncate">
                          {worker.name}
                        </div>
                        <div className="text-[11px] text-slate-500 font-medium truncate">
                          {worker.role}
                        </div>
                        <div className="text-[10px] text-indigo-600 truncate">
                          {worker.department}
                        </div>
                      </div>
                    </div>
                  </td>

                  {DAYS_OF_WEEK.map((day) => {
                    const shift = days?.get(day) ?? emptyShift(worker.id, day);
                    return (
                      <td
                        key={day}
                        onClick={() =>
                          setActiveShiftDetail({ worker, day, shift })
                        }
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setActiveShiftDetail({ worker, day, shift });
                          }
                        }}
                        role="button"
                        tabIndex={0}
                        aria-label={`${worker.name}, ${day}: ${shift.start_time}, ${shift.length} hours`}
                        className="p-1.5 border-r border-slate-200 last:border-r-0 align-top h-20 min-w-[105px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-inset"
                      >
                        <ShiftBadge shift={shift} day={day} />
                      </td>
                    );
                  })}

                  {/* Weekly Total Hours */}
                  <td className="py-2.5 px-3 text-center border-l border-slate-100 font-bold">
                    <span
                      className={`inline-block px-2 py-1 rounded-md text-xs ${hoursBadgeClass(
                        totalHours,
                        worker.maxHours
                      )}`}
                    >
                      {totalHours}h / {worker.maxHours}h
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Selected Shift Detail Bar */}
      {activeShiftDetail && (
        <ShiftDetailBar
          detail={activeShiftDetail}
          onDismiss={() => setActiveShiftDetail(null)}
        />
      )}
    </div>
  );
};