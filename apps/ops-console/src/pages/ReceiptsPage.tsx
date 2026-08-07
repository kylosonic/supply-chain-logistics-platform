import { useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';

import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useReceipts, useSubmitDispute, useWallet } from '../hooks/queries';
import type { Receipt } from '../types/api';

const UPLOAD_CONFIRMATION = 'Receipt received — verification typically takes ≤24 hours.';

function statusTone(status: Receipt['status']) {
  if (status === 'verified') return 'success';
  if (status === 'rejected') return 'danger';
  if (status === 'escalated') return 'warning';
  return 'neutral';
}

function ReceiptCard({ receipt, onDispute }: { receipt: Receipt; onDispute: (text: string) => void }) {
  const [disputeText, setDisputeText] = useState('');
  const [showDispute, setShowDispute] = useState(false);

  return (
    <article className="animate-fade-in rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge label={receipt.status} tone={statusTone(receipt.status)} />
            <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
              {receipt.reference_number ?? 'no reference extracted'}
            </span>
          </div>
          <h3 className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">
            {receipt.amount_etb ? `${receipt.amount_etb} ETB` : 'Amount pending extraction'}
          </h3>
          <p className="mt-1 text-sm text-slate-400">
            Invoice: {receipt.invoice_number ?? '—'} · Sender: {receipt.sender_name ?? '—'} · Bank:{' '}
            {receipt.bank_code ?? '—'}
          </p>
          <p className="mt-1 text-xs text-slate-500">{new Date(receipt.created_at).toLocaleString()}</p>
        </div>
      </div>

      {receipt.reversal_status ? (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <StatusBadge label={receipt.reversal_status} tone={receipt.reversal_status === 'reversed' ? 'danger' : 'neutral'} />
        </div>
      ) : null}

      {receipt.status === 'verified' && !receipt.reversal_status ? (
        <p className="mt-3 text-sm text-emerald-200">
          {receipt.invoice_number ? `Invoice #${receipt.invoice_number} paid. Your workspace is unlocked.` : 'Receipt verified.'}
        </p>
      ) : null}

      {receipt.reversal_status === 'reversed' ? (
        <div className="mt-3 rounded-[16px] border border-rose-500/30 bg-rose-950/20 p-3">
          <p className="text-sm text-rose-100">
            This payment was reversed — the credited amount was restored to your invoice balance. See
            your notifications for the full message.
          </p>
        </div>
      ) : null}

      {receipt.status === 'rejected' && receipt.rejection_reason ? (
        <div className="mt-3 rounded-[16px] border border-rose-500/30 bg-rose-950/20 p-3">
          <p className="text-sm text-rose-100">{receipt.rejection_reason}</p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => {
                setShowDispute(false);
                document.getElementById('receipt-upload-input')?.click();
              }}
              className="inline-flex min-h-10 items-center justify-center rounded-full border border-slate-700 px-4 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
            >
              Re-upload
            </button>
            <button
              type="button"
              onClick={() => setShowDispute((v) => !v)}
              className="inline-flex min-h-10 items-center justify-center rounded-full border border-amber-500/30 px-4 text-xs font-semibold text-amber-200 transition hover:border-amber-400/50 hover:bg-amber-950/20"
            >
              Dispute this decision
            </button>
          </div>
          {showDispute ? (
            <div className="mt-3 space-y-2">
              <textarea
                value={disputeText}
                onChange={(event) => setDisputeText(event.target.value)}
                placeholder="Explain why you believe the rejection was wrong…"
                maxLength={1000}
                className="glow-ring min-h-24 w-full rounded-2xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-amber-400/50"
              />
              <button
                type="button"
                disabled={!disputeText.trim()}
                onClick={() => {
                  onDispute(disputeText.trim());
                  setShowDispute(false);
                }}
                className="inline-flex min-h-10 items-center justify-center rounded-full bg-amber-400 px-4 text-xs font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Submit dispute
              </button>
            </div>
          ) : null}
        </div>
      ) : null}

      {receipt.status === 'escalated' ? (
        <p className="mt-3 rounded-[16px] border border-amber-500/30 bg-amber-950/20 p-3 text-sm text-amber-100">
          Your receipt is under review. FreightPilot has a question about your recent receipt — please
          watch your notifications for the details.
        </p>
      ) : null}
    </article>
  );
}

export function ReceiptsPage() {
  const { data: receipts = [], refetch: refetchReceipts } = useReceipts();
  const { data: wallet } = useWallet();
  const disputeMutation = useSubmitDispute();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const { uploadReceipt } = await import('../services/receiptsApi');
      const result = await uploadReceipt(selectedFile);
      setStatusMessage(result.message || UPLOAD_CONFIRMATION);
      setSelectedFile(null);
      (event.target as HTMLFormElement).reset();
      await refetchReceipts();
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorMessage(detail ?? 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  }

  function onFileSelected(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  async function onDispute(receiptId: string, text: string) {
    setErrorMessage(null);
    try {
      await disputeMutation.mutateAsync({ id: receiptId, text });
      setStatusMessage('Dispute submitted — your receipt is now under review.');
    } catch {
      setErrorMessage('Failed to submit dispute.');
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Payments"
        title="Receipts and wallet"
        description="Upload bank-transfer receipts — no invoice selection needed; the system routes each receipt to your oldest open invoice. Verification typically takes ≤24 hours."
      />

      {statusMessage ? (
        <Panel className="border-sky-500/20 bg-sky-950/12">
          <p className="text-sm text-sky-100">{statusMessage}</p>
        </Panel>
      ) : null}
      {errorMessage ? (
        <Panel className="border-rose-500/20 bg-rose-950/12">
          <p className="text-sm text-rose-100">{errorMessage}</p>
        </Panel>
      ) : null}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <Panel
          eyebrow="Upload"
          title="Upload a transfer receipt"
          description="PNG, JPG, or PDF up to 5 MB. Keep the reference number and amount visible."
        >
          <form onSubmit={onUpload} className="grid gap-3">
            <input
              id="receipt-upload-input"
              type="file"
              accept=".png,.jpg,.jpeg,.pdf"
              onChange={onFileSelected}
              className="glow-ring min-h-12 w-full rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/50"
            />
            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="inline-flex min-h-12 items-center justify-center rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading ? 'Uploading…' : 'Upload receipt'}
            </button>
          </form>
          <p className="mt-3 text-xs text-slate-500">
            {selectedFile ? `${selectedFile.name} (${Math.round(selectedFile.size / 1024)} KB) selected` : 'No file selected.'}
          </p>
        </Panel>

        <Panel
          eyebrow="Wallet"
          title="Surplus credits"
          description="Overpayments within tolerance apply as credit to your next invoice automatically."
        >
          {wallet ? (
            <>
              <div className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Available balance</p>
                <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold text-slate-50">
                  {wallet.available_etb} ETB
                </p>
                <p className="mt-2 text-sm text-slate-400">
                  Wallet balance: +{wallet.available_etb} ETB applies to next invoice.
                </p>
              </div>
              {wallet.credits.length > 0 ? (
                <div className="mt-4 space-y-2">
                  {wallet.credits.slice(0, 6).map((credit) => (
                    <div
                      key={`${credit.created_at}-${credit.amount_etb}`}
                      className="flex items-center justify-between rounded-[16px] border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm"
                    >
                      <span className="text-slate-300">+{credit.amount_etb} ETB</span>
                      <span className="text-xs text-slate-500">
                        {credit.status}
                        {credit.applied_to_invoice_number ? ` → ${credit.applied_to_invoice_number}` : ''}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-500">No surplus credits yet.</p>
              )}
            </>
          ) : (
            <p className="text-sm text-slate-500">Wallet unavailable.</p>
          )}
        </Panel>
      </div>

      <Panel
        eyebrow="History"
        title="Your receipts"
        description="Rejections show the reason and let you re-upload or dispute the decision."
      >
        {receipts.length === 0 ? (
          <p className="text-sm text-slate-500">No receipts uploaded yet.</p>
        ) : (
          <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
            {receipts.map((receipt) => (
              <ReceiptCard
                key={receipt.id}
                receipt={receipt}
                onDispute={(text) => onDispute(receipt.id, text)}
              />
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
