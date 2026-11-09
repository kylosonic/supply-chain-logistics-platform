import { api } from './api';
import type { DecisionBrief } from '../types/api';

export async function getDecisionBrief(): Promise<DecisionBrief> {
  const { data } = await api.get<DecisionBrief>('/ops/decision-brief');
  return data;
}

