import { api } from './api';
import type {
  CashRiskRow,
  DecisionBrief,
  ExceptionTriageRow,
} from '../types/api';

export async function getDecisionBrief(): Promise<DecisionBrief> {
  const { data } = await api.get<DecisionBrief>('/ops/decision-brief');
  return data;
}

export async function getCashRisk(): Promise<CashRiskRow[]> {
  const { data } = await api.get<CashRiskRow[]>('/ops/cash-risk');
  return data;
}

export async function getExceptionTriage(): Promise<ExceptionTriageRow[]> {
  const { data } = await api.get<ExceptionTriageRow[]>('/ops/exception-triage');
  return data;
}
