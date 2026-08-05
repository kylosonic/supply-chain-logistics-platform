import { api } from './api';
import type {
  LargeSurplusDecision,
  Receipt,
  ReceiptQueueItem,
  TrustedPayerAction,
  Verdict,
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

export async function getReceiptQueueItem(id: string): Promise<ReceiptQueueItem> {
  const { data } = await api.get<ReceiptQueueItem>(`/receipts/queue/${id}`);
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
