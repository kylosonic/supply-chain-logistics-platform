export default function Loading() {
  return (
    <div className="section-shell flex min-h-[60vh] items-center justify-center py-24">
      <div className="glass-panel flex flex-col items-center gap-4 px-8 py-8 text-center">
        <div className="h-12 w-12 animate-spin rounded-full border border-white/10 border-t-cyan-300" />
        <div>
          <p className="kicker">FreightPilot</p>
          <p className="mt-3 font-display text-2xl text-white">Composing the launch sequence…</p>
        </div>
      </div>
    </div>
  );
}