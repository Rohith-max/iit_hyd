import { create } from 'zustand';
import type { CreditCase, AgentEvent } from '../types';

interface CaseStore {
  cases: CreditCase[];
  activeCase: CreditCase | null;
  setCases: (cases: CreditCase[]) => void;
  setActiveCase: (c: CreditCase | null) => void;
  updateCaseStatus: (id: string, status: string) => void;
}

export const useCaseStore = create<CaseStore>((set) => ({
  cases: [],
  activeCase: null,
  setCases: (cases) => set({ cases }),
  setActiveCase: (c) => set({ activeCase: c }),
  updateCaseStatus: (id, status) =>
    set((s) => ({
      cases: s.cases.map((c) => (c.id === id ? { ...c, status } : c)),
      activeCase: s.activeCase?.id === id ? { ...s.activeCase, status } : s.activeCase,
    })),
}));

interface AgentStore {
  events: AgentEvent[];
  camSections: Record<string, string>;
  currentAgent: string;
  isComplete: boolean;
  addEvent: (e: AgentEvent) => void;
  appendCAM: (section: string, delta: string) => void;
  setCurrentAgent: (a: string) => void;
  setComplete: (v: boolean) => void;
  reset: () => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  events: [],
  camSections: {},
  currentAgent: '',
  isComplete: false,
  addEvent: (e) => set((s) => ({ events: [...s.events, e] })),
  appendCAM: (section, delta) =>
    set((s) => ({
      camSections: {
        ...s.camSections,
        [section]: (s.camSections[section] || '') + delta,
      },
    })),
  setCurrentAgent: (a) => set({ currentAgent: a }),
  setComplete: (v) => set({ isComplete: v }),
  reset: () => set({ events: [], camSections: {}, currentAgent: '', isComplete: false }),
}));
