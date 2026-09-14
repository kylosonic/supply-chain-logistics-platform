import React, { useState } from 'react';
import { submitFeedback } from '../services/logisticsApi';

export function FeedbackForm() {
  const [category, setCategory] = useState('freight_invoice_reconciliation');
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('submitting');
    try {
      await submitFeedback({ category, message, user_email: email });
      setStatus('success');
      setMessage('');
    } catch {
      setStatus('error');
    }
  };

  return (
    <div className="fp-nested-surface p-5 w-full">
      <h3 className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50 mb-4">Beta Pilot Feedback</h3>
      {status === 'success' ? (
        <div className="text-emerald-400 p-4 border border-emerald-500/20 bg-emerald-950/12 rounded-lg text-sm">
          Thank you for your feedback! It helps us improve the platform.
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 mb-2">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="fp-input p-2"
            >
              <option value="freight_invoice_reconciliation">Freight Invoice Reconciliation</option>
              <option value="dock_management">Dock Management</option>
              <option value="route_optimization">Route Optimization</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 mb-2">Feedback Message</label>
            <textarea
              required
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Tell us what works well or what could be improved..."
              className="fp-input p-2"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 mb-2">Email (Optional)</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@logistics.co"
              className="fp-input p-2"
            />
          </div>
          {status === 'error' && <p className="text-rose-400 text-xs">Failed to submit feedback. Try again.</p>}
          <button
            type="submit"
            disabled={status === 'submitting'}
            className="glow-ring w-full inline-flex min-h-10 items-center justify-center rounded-lg border border-emerald-500/50 bg-emerald-600/10 px-4 text-sm font-semibold text-emerald-400 transition hover:bg-emerald-600/20 disabled:opacity-50"
          >
            {status === 'submitting' ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </form>
      )}
    </div>
  );
}
