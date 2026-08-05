import { useState } from 'react';

import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useReceiptQueue } from '../hooks/queries';
import { getReceiptFileUrl, renderDecision } from '../services/receiptsApi';
import type { LargeSurplusDecision, ReceiptQueueItem, TrustedPayerAction, Verdict } from '../types/api';

const CASH_FLAG = 'Cash deposit — confirm with customer that this was their intended transfer.';
const LARGE_SURPLUS_FLAG = 'Large surplus — admin manual decision required';
const LOW_CONFIDENCE_HINT = 'low confidence — please manually verify';

function verdictTone(status: ReceiptQueueItem['status']) {
  if (status === 'escalated') return 'warning';
  return 'neutral';
}

type DetailProps = {
  item: ReceiptQueueItem;
  onRendered: () => void;
  onError: (message: string) => void;
};

function AdminDetail({ item, onRendered, onError }: DetailProps) {
  // Pre-fill ONLY when the service actually recommends verify (trusted payer
  // or wrong-bank-within-portfolio). CASH and new-sender receipts must NOT
  // pre-fill — the admin picks a verdict explicitly (NB-12.3 suppression).
  const [verdict, setVerdict] = useState<Verdict | null>(item.recommended_verdict);
  const [note, setNote] = useState('');
  const [adminNote, setAdminNote] = useState('');
  const [trustedPayerAction, setTrustedPayerAction] = useState<TrustedPayerAction>('verified_once');
  const [surplusDecision, setSurplusDecision] = useState<LargeSurplusDecision>('credit_forward');
  const [partialAmount, setPartialAmount] = useState('');
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const fieldRows: Array<[string, string | null, number]> = [
    ['sender_name', item.extracted_fields['sender_name'] ?? null, item.confidence['sender_name'] ?? 0],
    ['sender_account_number', item.extracted_fields['sender_account_number'] ?? null, item.confidence['sender_account_number'] ?? 0],
    ['receiver_account_number', item.extracted_fields['receiver_account_number'] ?? null, item.confidence['receiver_account_number'] ?? 0],
    ['receiver_name', item.extracted_fields['receiver_name'] ?? null, item.confidence['receiver_name'] ?? 0],
    ['transfer_amount', item.extracted_fields['transfer_amount'] ?? null, item.confidence['transfer_amount'] ?? 0],
    ['transfer_date', item.extracted_fields['transfer_date'] ?? null, item.confidence['transfer_date'] ?? 0],
    ['reference_number', item.extracted_fields['reference_number'] ?? null, item.confidence['reference_number'] ?? 0],
    ['bank_identifier', item.extracted_fields['bank_identifier'] ?? null, item.confidence['bank_identifier'] ?? 0],
  ];

  async function onPreview() {
    if (!fileUrl) {
      try {
        setFileUrl(await getReceiptFileUrl(item.id));
      } catch {
        onError('Unable to load receipt file.');
      }
    }
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!verdict) return;
    setBusy(true);
    try {
      await renderDecision(item.id, {
        verdict,
        note: verdict === 'escalate' ? note : null,
        admin_note: adminNote || null,
        trusted_payer_action: verdict === 'verify' ? trustedPayerAction : null,
        large_surplus_decision: verdict === 'verify' && item.is_large_surplus ? surplusDecision : null,
        partial_credit_amount_etb:
          verdict === 'verify' && item.is_large_surplus && surplusDecision === 'partial_ignore'
            ? partialAmount
            : null,
      });
      onRendered();
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError(detail ?? 'Failed to render verdict.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      {/* Flags */}
      <div className="flex flex-wrap gap-2">
        {item.is_new_sender ? (
          <span className="inline-flex items-center rounded-full border border-rose-500/50 bg-rose-950/40 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-200">
            NEW SENDER
          </span>
        ) : null}
        {item.is_cash_sender ? (
          <span className="inline-flex items-center rounded-full border border-amber-500/40 bg-amber-950/30 px-3 py-1.5 text-[11px] font-semibold text-amber-100">
            {CASH_FLAG}
          </span>
        ) : null}
        {item.is_wrong_bank_within_portfolio ? (
          <span className="inline-flex items-center rounded-full border border-sky-500/30 bg-sky-950/30 px-3 py-1.5 text-[11px] font-semibold text-sky-200">
            Wrong-bank-within-portfolio — pre-filled Verify
          </span>
        ) : null}
        {item.is_large_surplus ? (
          <span className="inline-flex items-center rounded-full border border-amber-500/40 bg-amber-950/30 px-3 py-1.5 text-[11px] font-semibold text-amber-100">
            {LARGE_SURPLUS_FLAG} ({item.surplus_etb ?? '0'} ETB)
          </span>
        ) : null}
        {item.has_zero_confidence ? (
          <span className="inline-flex items-center rounded-full border border-slate-600 bg-slate-900 px-3 py-1.5 text-[11px] font-semibold text-slate-200">
            {item.zero_confidence_warning}
          </span>
        ) : null}
        {item.low_confidence_fields.map((field) => (
          <span key={field} className="inline-flex items-center rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-[11px] font-semibold text-slate-300">
            {field} {LOW_CONFIDENCE_HINT}
          </span>
        ))}
        {item.dispute_text ? (
          <span className="inline-flex items-center rounded-full border border-amber-500/40 bg-amber-950/30 px-3 py-1.5 text-[11px] font-semibold text-amber-100">
            Customer disputes rejection: {item.dispute_text}
          </span>
        ) : null}
      </div>

      {/* Extracted fields with confidence bars */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {fieldRows.map(([label, value, confidence]) => (
          <div key={label} className="rounded-[16px] border border-slate-800 bg-slate-900/70 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</span>
              <span className="text-xs text-slate-400">{Math.round(confidence * 100)}%</span>
            </div>
            <p className="mt-1 break-all font-mono text-sm text-slate-100">{value ?? '—'}</p>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
              <div
                className={`h-full rounded-full ${confidence < 0.6 ? 'bg-amber-400' : 'bg-teal-300'}`}
                style={{ width: `${Math.round(confidence * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* File preview */}
      <div className="rounded-[16px] border border-slate-800 bg-slate-900/70 p-3">
        <button
          type="button"
          onClick={onPreview}
          className="rounded-full border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500"
        >
          {fileUrl ? 'Preview loaded' : 'Preview receipt file'}
        </button>
        {fileUrl ? (
          <div className="mt-3">
            {item.content_type === 'application/pdf' ? (
              <iframe title="receipt-preview" src={fileUrl} className="h-72 w-full rounded-[16px] border border-slate-800 bg-slate-950" />
            ) : (
              <img src={fileUrl} alt="receipt preview" className="max-h-72 rounded-[16px] border border-slate-800 bg-slate-950" />
            )}
          </div>
        ) : null}
      </div>

      {/* Verdict actions */}
      <div className="grid gap-3">
        <label className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Verdict</label>
        <div className="flex flex-wrap gap-2">
          {(['verify', 'reject_wrong_bank', 'reject_duplicate', 'reject_illegible', 'escalate'] as Verdict[]).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setVerdict(v)}
              className={`rounded-full border px-3 py-2 text-xs font-semibold transition ${
                verdict === v
                  ? 'border-sky-400/50 bg-sky-500/15 text-slate-50'
                  : 'border-slate-700 text-slate-300 hover:border-slate-500'
              }`}
            >
              {v === 'verify' ? 'Verify' : v.replace('_', ' ')}
            </button>
          ))}
        </div>

        {verdict === 'verify' && item.is_large_surplus ? (
          <div className="rounded-[16px] border border-amber-500/30 bg-amber-950/20 p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-200">{LARGE_SURPLUS_FLAG}</p>
            <div className="mt-2 grid gap-3 md:grid-cols-3">
              {(['credit_forward', 'credit_backward', 'partial_ignore'] as LargeSurplusDecision[]).map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setSurplusDecision(d)}
                  className={`rounded-full border px-3 py-2 text-xs font-semibold transition ${
                    surplusDecision === d
                      ? 'border-amber-400/50 bg-amber-500/15 text-slate-50'
                      : 'border-slate-700 text-slate-300 hover:border-slate-500'
                  }`}
                >
                  {d.replace('_', ' ')}
                </button>
              ))}
            </div>
            {surplusDecision === 'partial_ignore' ? (
              <input
                value={partialAmount}
                onChange={(event) => setPartialAmount(event.target.value)}
                placeholder="Partial credit amount (ETB)"
                className="glow-ring mt-3 min-h-10 w-full rounded-xl border border-slate-700 bg-slate-950/80 px-3 text-sm text-slate-100 outline-none transition focus:border-amber-400/50"
              />
            ) : null}
          </div>
        ) : null}

        {verdict === 'verify' ? (
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Trusted payer</label>
            <select
              value={trustedPayerAction}
              onChange={(event) => setTrustedPayerAction(event.target.value as TrustedPayerAction)}
              className="glow-ring min-h-10 rounded-xl border border-slate-700 bg-slate-950/80 px-3 text-sm text-slate-100 outline-none"
            >
              <option value="verified_once">Verify, do not add</option>
              <option value="added">Verify + add to trusted-payer list</option>
            </select>
          </div>
        ) : null}

        {verdict === 'escalate' ? (
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Escalation question shown to the customer (required)"
            className="glow-ring min-h-24 w-full rounded-2xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-amber-400/50"
          />
        ) : null}

        <input
          value={adminNote}
          onChange={(event) => setAdminNote(event.target.value)}
          placeholder="Admin note (optional)"
          maxLength={512}
          className="glow-ring min-h-10 w-full rounded-xl border border-slate-700 bg-slate-950/80 px-3 text-sm text-slate-100 outline-none transition focus:border-sky-400/50"
        />

        <button
          type="submit"
          disabled={busy || !verdict || (verdict === 'escalate' && !note.trim())}
          className="inline-flex min-h-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? 'Rendering…' : 'Render decision'}
        </button>
      </div>
    </form>
  );
}

export function AdminReceiptsPage() {
  const { data: queue = [], refetch } = useReceiptQueue();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selected = queue.find((item) => item.id === selectedId) ?? null;

  async function onRendered() {
    setMessage('Decision rendered.');
    setError(null);
    setSelectedId(null);
    await refetch();
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Verification queue"
        title="Receipt verdicts"
        description="Review pending and escalated receipts, then render one of exactly five verdicts. Credits apply only on Verify — pessimistic unlock."
      />

      {message ? (
        <Panel className="border-sky-500/20 bg-sky-950/12">
          <p className="text-sm text-sky-100">{message}</p>
        </Panel>
      ) : null}
      {error ? (
        <Panel className="border-rose-500/20 bg-rose-950/12">
          <p className="text-sm text-rose-100">{error}</p>
        </Panel>
      ) : null}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel eyebrow="Queue" title="Pending and escalated" description="Oldest first — receipts from every workspace.">
          {queue.length === 0 ? (
            <p className="text-sm text-slate-500">No receipts awaiting a verdict.</p>
          ) : (
            <div className="grid gap-2">
              {queue.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setSelectedId(item.id);
                    setError(null);
                    setMessage(null);
                  }}
                  className={`rounded-[18px] border p-3 text-left transition ${
                    selectedId === item.id
                      ? 'border-sky-400/40 bg-sky-500/10'
                      : 'border-slate-800 bg-slate-900/70 hover:border-slate-600'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge label={item.status} tone={verdictTone(item.status)} />
                      {item.is_new_sender ? (
                        <span className="rounded-full border border-rose-500/50 bg-rose-950/40 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-rose-200">
                          NEW SENDER
                        </span>
                      ) : null}
                      {item.is_cash_sender ? (
                        <span className="rounded-full border border-amber-500/40 bg-amber-950/30 px-2 py-0.5 text-[10px] font-semibold text-amber-100">
                          CASH
                        </span>
                      ) : null}
                    </div>
                    <span className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</span>
                  </div>
                  <p className="mt-2 font-['Space_Grotesk'] text-sm font-semibold text-slate-50">
                    {item.organization_name} · {item.extracted_fields['reference_number'] ?? 'no ref'}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    {item.extracted_fields['transfer_amount'] ?? '—'} ETB · invoice{' '}
                    {item.invoice_number ?? '—'} · {item.extracted_fields['sender_name'] ?? 'no sender'}
                  </p>
                  {item.dispute_text ? (
                    <p className="mt-1 text-xs text-amber-200/90">Dispute: {item.dispute_text}</p>
                  ) : null}
                </button>
              ))}
            </div>
          )}
        </Panel>

        {selected ? (
          <Panel
            eyebrow="Detail"
            title={`Receipt ${selected.extracted_fields['reference_number'] ?? selected.id}`}
            description={`${selected.organization_name} · invoice ${selected.invoice_number ?? '—'} · designated ${selected.designated_bank_code ?? '—'}`}
          >
            <AdminDetail key={selected.id} item={selected} onRendered={onRendered} onError={setError} />
          </Panel>
        ) : (
          <Panel eyebrow="Detail" title="Select a receipt" description="Choose a queue item to review its extraction and render a verdict.">
            <p className="text-sm text-slate-500">No receipt selected.</p>
          </Panel>
        )}
      </div>
    </div>
  );
}
