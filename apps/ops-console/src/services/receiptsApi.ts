import { api } from './api';
import type {
  LargeSurplusDecision,
  Receipt,
  ReceiptAuditEvent,
  ReceiptQueueItem,
  ReversalRead,
  TrustedPayerAction,
  Verdict,
  VerifiedReceiptAudit,
  WalletSummary,
} from '../types/api';

export type UploadReceiptResult = {
  message: string;
  receipt_id: string;
};

export async function uploadReceipt(file: File, mockExtraction?: object): Promise<UploadReceiptResult> {
  const form = new FormData();
  form.append('file', file);
  if (mockExtraction) {
    form.append('mock_extraction', JSON.stringify(mockExtraction));
  }
  const { data } = await api.post<UploadReceiptResult>('/receipts/upload', form);
  return data;
}

export async function listReceipts(): Promise<Receipt[]> {
  const { data } = await api.get<Receipt[]>('/receipts');
  return data;
}

export async function getWallet(): Promise<WalletSummary> {
  const { data } = await api.get<WalletSummary>('/receipts/wallet');
  return data;
}

export async function listReceiptQueue(): Promise<ReceiptQueueItem[]> {
  const { data } = await api.get<ReceiptQueueItem[]>('/receipts/queue');
  return data;
}

export async function getReceiptFileUrl(id: string): Promise<string> {
  const { data } = await api.get<Blob>(`/receipts/queue/${id}/file`, { responseType: 'blob' });
  return URL.createObjectURL(data);
}

export type RenderDecisionPayload = {
  verdict: Verdict;
  note?: string | null;
  admin_note?: string | null;
  trusted_payer_action?: TrustedPayerAction | null;
  large_surplus_decision?: LargeSurplusDecision | null;
  partial_credit_amount_etb?: string | null;
};

export async function renderDecision(id: string, payload: RenderDecisionPayload): Promise<Receipt> {
  const { data } = await api.post<Receipt>(`/receipts/${id}/decision`, payload);
  return data;
}

export async function submitDispute(id: string, text: string): Promise<Receipt> {
  const { data } = await api.post<Receipt>(`/receipts/${id}/dispute`, { text });
  return data;
}

export async function listVerifiedAudit(): Promise<VerifiedReceiptAudit[]> {
  const { data } = await api.get<VerifiedReceiptAudit[]>('/receipts/audit');
  return data;
}

export async function getReceiptAuditEvents(id: string): Promise<ReceiptAuditEvent[]> {
  const { data } = await api.get<ReceiptAuditEvent[]>(`/receipts/${id}/audit-events`);
  return data;
}

export async function undoReceipt(id: string, note?: string | null): Promise<ReversalRead> {
  const { data } = await api.post<ReversalRead>(`/receipts/${id}/undo`, { note: note ?? null });
  return data;
}

export async function reverseReceipt(id: string, reason: string): Promise<ReversalRead> {
  const { data } = await api.post<ReversalRead>(`/receipts/${id}/reverse`, { reason });
  return data;
}

export async function removeTrustedPayer(
  senderName: string,
  organizationId: string,
): Promise<{ removed: boolean }> {
  const { data } = await api.delete<{ removed: boolean }>(
    `/receipts/trusted-payers/${encodeURIComponent(senderName)}`,
    { params: { organization_id: organizationId } },
  );
  return data;
}
