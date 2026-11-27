import type { Worker, ScheduleMap, Scenario, ShiftInfo, ProposalType } from '../types';

const API_BASE = 'http://localhost:8000/data/';
const CHAT_BASE = 'http://localhost:8000/chat';
const AUTH_BASE = 'http://localhost:8000/auth';

export const api = {
  getToken() { return localStorage.getItem('jwt'); },
  login: async (credentials: { username: string; password: string }): Promise<{ access_token: string; }> => {
    const response = await fetch(`${AUTH_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    if (!response.ok) throw new Error('Login failed');
    return response.json();
  },

  getMe: async (token: string): Promise<Worker> => {
    const response = await fetch(`${AUTH_BASE}/me`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to get user');
    return response.json();
  },

  getWorkers: async (): Promise<Worker[]> => {
    try {
      const response = await fetch(`${API_BASE}workers`, {
        headers: { 'Authorization': `Bearer ${api.getToken()}` },
      });
      if (!response.ok) { }
      return response.json();
    } catch {
      return []
    }
  },

  getSchedule: async (): Promise<ShiftInfo[]> => {
    try {
      const response = await fetch(`${API_BASE}shifts`, {
        headers: { 'Authorization': `Bearer ${api.getToken()}` },
      });
      if (!response.ok) { }
      return response.json();
    } catch {
      return [];
    }
  },

  getScenario: async (): Promise<Scenario> => {
    return {} as Scenario;
  },

  getProposals: async (): Promise<ProposalType[]> => {
    try {
      const response = await fetch(`${API_BASE}proposals`, {
        headers: { 'Authorization': `Bearer ${api.getToken()}` },
      });
      if (!response.ok) return [];
      return response.json();
    } catch {
      return [];
    }
  },

  applyProposal: async (proposalId: string): Promise<ScheduleMap> => {
    const response = await fetch(`${API_BASE}proposals/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proposalId }),
    });
    if (!response.ok) throw new Error('Failed to apply proposal');
    return response.json();
  },

  async sendMessage(userMessage: string, history: any[] = []): Promise<{
    reply: string;
    tools_used: string[];
    updated_shift: any;
    "created_proposal": ProposalType
  }> {
    const response = await fetch(`${CHAT_BASE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${api.getToken()}`,
      },
      body: JSON.stringify({ message: userMessage, history }),
    });

    if (!response.ok) throw new Error('Failed to send message');
    return response.json();
  },

  approveProposal: async (proposalId: string): Promise<
  {
     proposal?:ProposalType
  deleted?: boolean,
    message: string,
    success: boolean,
    new_shift: ShiftInfo,
  }> => {
    const response = await fetch(`${API_BASE}approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${api.getToken()}`,
      },
      body: JSON.stringify({ proposal_id: proposalId }),
    });

    if (!response.ok) throw new Error('Failed to approve proposal');
    return response.json();
  }
};