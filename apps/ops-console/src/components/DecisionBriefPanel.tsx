import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { getDecisionBrief } from '../services/insightsApi';
import type { DecisionBrief, DecisionEvidence } from '../types/api';
import { Panel } from './ui/Panel';
import { StatusBadge } from './ui/StatusBadge';

function tone(value: string): 'danger' | 'warning' | 'info' {
  if (value === 'critical' || value === 'high') return 'danger';
  if (value === 'medium') return 'warning';
  return 'info';
}

function Evidence({ rows }: { rows: DecisionEvidence[] }) {
  if (rows.length === 0) return null;
  return (
    <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
      {rows.map((row, index) => (
        <li key={`${row.record_type}:${row.record_id ?? row.label}:${index}`}>
          {row.label}
          {row.value !== null ? `: ${row.value}` : ''}
        </li>
      ))}
    </ul>
  );
}

export function DecisionBriefContent({
  brief,
  isLoading = false,
  error = null,
}: {
  brief?: DecisionBrief;
  isLoading?: boolean;
  error?: unknown;
}) {
  if (isLoading) {
    return (
      <Panel eyebrow="Decision brief" title="Reading the workspace">
        <p className="text-sm text-slate-400">Building a record-grounded brief…</p>
      </Panel>
    );
  }

  if (error) {
    return (
      <Panel eyebrow="Decision brief" title="Brief unavailable">
        <p className="text-sm text-rose-200">
          The brief could not be built from workspace records. No recommendation is being shown.
        </p>
      </Panel>
    );
  }

  if (!brief) return null;

  return (
    <Panel
      eyebrow="Grounded decision brief"
      title={brief.headline}
      description="Every statement below comes from a workspace record or a calculated count. Recommendations are advisory and require human action."
    >
      <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">What changed</h3>
            <ul className="mt-2 space-y-1.5 text-sm leading-6 text-slate-300">
              {brief.what_changed.map((item) => <li key={item}>• {item}</li>)}
            </ul>
          </section>

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">What is at risk</h3>
            <div className="mt-2 space-y-2">
              {brief.risks.length === 0 ? (
                <p className="text-sm text-emerald-300/80">No grounded operating risk is currently recorded.</p>
              ) : null}
              {brief.risks.map((risk) => (
                <article key={risk.kind} className="rounded-lg border border-slate-800/80 p-3">
                  <div className="flex items-center gap-2">
                    <StatusBadge label={risk.severity} tone={tone(risk.severity)} />
                    <span className="text-xs uppercase tracking-wide text-slate-500">{risk.kind}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-300">{risk.message}</p>
                  <Evidence rows={risk.evidence} />
                </article>
              ))}
            </div>
          </section>

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recommended next actions</h3>
            <div className="mt-2 space-y-2">
              {brief.actions.length === 0 ? (
                <p className="text-sm text-slate-500">No action is recommended from the current records.</p>
              ) : null}
              {brief.actions.map((action) => (
                <article key={`${action.priority}:${action.action}`} className="rounded-lg border border-slate-800/80 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-semibold text-slate-100">{action.action}</p>
                    <span className="rounded-full border border-slate-700 px-2 py-0.5 text-xs text-slate-400">
                      P{action.priority}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-400">{action.reason}</p>
                  <Evidence rows={action.evidence} />
                  {action.href ? (
                    <Link to={action.href} className="mt-2 inline-block text-xs font-semibold text-sky-300 underline-offset-4 hover:underline">
                      Review the record →
                    </Link>
                  ) : null}
                </article>
              ))}
            </div>
          </section>
        </div>

        <div className="space-y-4">
          <section>
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Cash risk radar</h3>
              <span className="text-xs text-slate-600">Rules-based</span>
            </div>
            <div className="mt-2 space-y-2">
              {brief.cash_risk.length === 0 ? (
                <p className="text-sm text-slate-500">No open driver cash exposure is recorded.</p>
              ) : null}
              {brief.cash_risk.map((row) => (
                <article key={row.driver_id ?? row.driver_name} className="rounded-lg border border-slate-800/80 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-100">{row.driver_name}</p>
                    <span className="text-sm font-semibold tabular-nums text-amber-200">{row.risk_score}/100</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">
                    {row.shortfall_etb} ETB shortfall · {row.outstanding_count} open stop(s)
                  </p>
                  <p className="mt-1 text-xs text-slate-500">{row.factors.join(' · ')}</p>
                </article>
              ))}
            </div>
          </section>

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Exception triage</h3>
            <div className="mt-2 space-y-2">
              {brief.triage.length === 0 ? (
                <p className="text-sm text-slate-500">No open exception needs triage.</p>
              ) : null}
              {brief.triage.map((row) => (
                <article key={row.alert_id} className="rounded-lg border border-slate-800/80 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={row.severity} tone={tone(row.severity)} />
                    <p className="text-sm font-semibold text-slate-100">{row.title}</p>
                    <span className="ml-auto text-xs tabular-nums text-slate-500">P{row.priority}</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">{row.age_hours}h open</p>
                  <p className="mt-1 text-sm text-slate-300">{row.suggested_action}</p>
                  <Evidence rows={row.evidence} />
                </article>
              ))}
            </div>
          </section>
        </div>
      </div>
      <p className="mt-4 border-t border-slate-800/80 pt-3 text-xs text-slate-500">
        Source: {brief.generated_by} · generated {new Date(brief.generated_at).toLocaleString()}
      </p>
    </Panel>
  );
}

export function DecisionBriefPanel() {
  const query = useQuery({
    queryKey: ['ops', 'decision-brief'],
    queryFn: getDecisionBrief,
    staleTime: 30_000,
  });

  return <DecisionBriefContent brief={query.data} isLoading={query.isLoading} error={query.error} />;
}
