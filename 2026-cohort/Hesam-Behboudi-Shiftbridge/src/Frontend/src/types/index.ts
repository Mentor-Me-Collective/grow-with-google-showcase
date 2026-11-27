export interface Worker {
  id: string;
  name: string;
  role: 'Senior RN' | 'Charge Nurse' | 'RN' | 'LPN' | 'Support Specialist';
  department: string;
  maxHours: number;
  currentHours: number;
  avatar: string;
}

export type DayOfWeek = 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday';

export interface ShiftInfo {
  id: string;
  type: 'regular' | 'conflict' | 'updated' | 'off';
  start_time: string;
  length: number;
  note?: string;
  updatedByAi?: boolean;
  conflict_reason?: string;
  worker_id:string;
  day:DayOfWeek;
}

export type ScheduleMap = Record<string, Record<DayOfWeek, ShiftInfo>>;


export interface Scenario {
  id: string;
  affectedWorkerId: string;
  affectedWorkerName: string;
  conflictDay: DayOfWeek;
  originalShift: string;
  reason: string;
  constraint: string;
  promptText: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  roleName?: string;
  text: string;
  timestamp: string;
  isPendingApproval?: boolean;
  proposalId?: 'opt_A' | 'opt_B';
  approvalState?: {
    workerApproved: boolean;
    managerApproved: boolean;
    applied: boolean;
  };
  proposal?:ProposalType;
}
export type ProposalType= {
      "id"?: string;
      "worker_id": string;
      "new_shift_data": {
        "shift_id": string;
        "project_id": string;
        "worker_id": string;
        "current_day": string;
        "current_start_time": string;
        "current_length": number;
        "proposed_day": string;
        "proposed_start_time": string;
        "proposed_length": number;
        "note": string;
      },
      "isManagerApproved": boolean;
      "isWorkerApproved": boolean;
    }

export const DAYS_OF_WEEK: DayOfWeek[] = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday'
];
