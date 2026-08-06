import { api } from './api';
import type {
  ActivationState,
  PitchDismissResult,
  ResetWorkspaceResult,
} from '../types/api';

export async function getActivationState(): Promise<ActivationState> {
  const { data } = await api.get<ActivationState>('/activation');
  return data;
}

export async function resetWorkspace(workspaceName: string): Promise<ResetWorkspaceResult> {
  const { data } = await api.post<ResetWorkspaceResult>('/activation/reset', {
    workspace_name: workspaceName,
  });
  return data;
}

export async function dismissPitch(level: 'p60'): Promise<PitchDismissResult> {
  const { data } = await api.post<PitchDismissResult>('/activation/pitch-dismiss', { level });
  return data;
}
