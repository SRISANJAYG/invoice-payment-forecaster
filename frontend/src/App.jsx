import { useState } from 'react';

const API_BASE = 'http://localhost:5000';

const SEGMENTS = ['SMB', 'Enterprise', 'Startup', 'Government'];

const RISK_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 };

const RISK_ROW = {
  HIGH:   'bg-red-950/40 border-l-4 border-red-500',
  MEDIUM: 'bg-yellow-950/30 border-l-4 border-yellow-500',
  LOW:    'bg-emerald-950/30 border-l-4 border-emerald-600',
};

const RISK_BADGE = {
  HIGH:   'bg-red-500/20 text-red-400 ring-1 ring-red-500/40',
  MEDIUM: 'bg-yellow-500/20 text-yellow-400 ring-1 ring-yellow-500/40',
  LOW:    'bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40',
};

const defaultForm = {
  customer_segment: 'SMB',
  invoice_amount: '',
  customer_avg_past_delay: '',
};

export default function App() {
  const [form, setForm] = useState(defaultForm);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // ── Derived stats ──────────────────────────────────────────────────────────
  const highCount = invoices.filter((i) => i.risk_level === 'HIGH').length;
  const sorted = [...invoices].sort(
    (a, b) => RISK_ORDER[a.risk_level] - RISK_ORDER[b.risk_level]
  );

  const naiveTotal = invoices.reduce((sum, i) => sum + i.invoice_amount, 0);
  const avgDelay =
    invoices.length > 0
      ? invoices.reduce((sum, i) => sum + i.predicted_days_late, 0) / invoices.length
      : 0;

  // ── Handlers ───────────────────────────────────────────────────────────────
  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_segment: form.customer_segment,
          invoice_amount: parseFloat(form.invoice_amount),
          customer_avg_past_delay: parseFloat(form.customer_avg_past_delay),
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Server error ${res.status}`);
      }

      const { predicted_days_late, risk_level, reason } = await res.json();

      setInvoices((prev) => [
        ...prev,
        {
          id: Date.now(),
          customer_segment: form.customer_segment,
          invoice_amount: parseFloat(form.invoice_amount),
          customer_avg_past_delay: parseFloat(form.customer_avg_past_delay),
          predicted_days_late,
          risk_level,
          reason,
        },
      ]);

      setForm(defaultForm);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans">

      {/* ── Top bar ── */}
      <header className="border-b border-zinc-800 px-8 py-4 flex items-center gap-3">
        <span className="text-lg font-semibold tracking-tight text-white">
          Invoice Forecaster
        </span>
        <span className="text-xs text-zinc-500 font-mono bg-zinc-900 px-2 py-0.5 rounded">
          ML-powered
        </span>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 space-y-8">

        {/* ── Summary cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard label="Total Invoices" value={invoices.length} />
          <StatCard label="High Risk Count" value={highCount} accent="red" />

          {/* Forecast comparison card — spans full width on mobile, one col on lg */}
          <div className="col-span-2 lg:col-span-1 bg-zinc-900 border border-zinc-800 rounded-xl px-6 py-5">
            <p className="text-xs text-zinc-500 uppercase tracking-widest mb-3">
              Forecast Comparison
            </p>
            {invoices.length === 0 ? (
              <p className="text-sm text-zinc-600">Submit invoices to see forecast.</p>
            ) : (
              <div className="space-y-2">
                <div className="flex items-baseline justify-between">
                  <span className="text-xs text-zinc-500">Naive (on-time)</span>
                  <span className="text-lg font-semibold tabular-nums text-white">
                    ${naiveTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-xs text-zinc-500">Avg ML delay</span>
                  <span className="text-lg font-semibold tabular-nums text-yellow-400">
                    ~{avgDelay.toFixed(1)} days
                  </span>
                </div>
                <p className="text-[11px] text-zinc-500 leading-snug pt-1 border-t border-zinc-800">
                  Naive assumes&nbsp;
                  <span className="text-zinc-300 font-medium">
                    ${naiveTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                  &nbsp;arrives on time. Reality: expect&nbsp;
                  <span className="text-yellow-400 font-medium">
                    ~{avgDelay.toFixed(1)} days
                  </span>
                  &nbsp;average delay across your invoices.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ── Add invoice form ── */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest mb-5">
            New Invoice Prediction
          </h2>

          <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-4">

            {/* Customer Segment */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-zinc-400 font-medium">Customer Segment</label>
              <select
                name="customer_segment"
                value={form.customer_segment}
                onChange={handleChange}
                className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100
                           focus:outline-none focus:ring-2 focus:ring-zinc-500"
              >
                {SEGMENTS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Invoice Amount */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-zinc-400 font-medium">Invoice Amount ($)</label>
              <input
                type="number"
                name="invoice_amount"
                value={form.invoice_amount}
                onChange={handleChange}
                min="0"
                step="0.01"
                placeholder="e.g. 45000"
                required
                className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100
                           placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-500"
              />
            </div>

            {/* Avg Past Delay */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-zinc-400 font-medium">Avg Past Delay (days)</label>
              <input
                type="number"
                name="customer_avg_past_delay"
                value={form.customer_avg_past_delay}
                onChange={handleChange}
                min="0"
                step="0.1"
                placeholder="e.g. 8.5"
                required
                className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100
                           placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-500"
              />
            </div>

            {/* Submit — full width on mobile, right-aligned on sm+ */}
            <div className="sm:col-span-3 flex flex-col items-start gap-2">
              <button
                type="submit"
                disabled={loading}
                className="bg-white text-zinc-900 text-sm font-semibold px-5 py-2 rounded-lg
                           hover:bg-zinc-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Predicting…' : 'Run Forecast'}
              </button>

              {error && (
                <p className="text-red-400 text-xs mt-1">{error}</p>
              )}
            </div>
          </form>
        </section>

        {/* ── Results table ── */}
        {invoices.length > 0 && (
          <section className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-800">
              <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">
                Forecast Results
                <span className="ml-2 text-zinc-600 font-normal normal-case tracking-normal">
                  sorted by risk
                </span>
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-zinc-500 uppercase tracking-widest border-b border-zinc-800">
                    <th className="text-left px-6 py-3 font-medium">Segment</th>
                    <th className="text-right px-6 py-3 font-medium">Amount</th>
                    <th className="text-right px-6 py-3 font-medium">Avg Past Delay</th>
                    <th className="text-right px-6 py-3 font-medium">Predicted Days Late</th>
                    <th className="text-center px-6 py-3 font-medium">Risk Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60">
                  {sorted.map((inv) => (
                    <tr key={inv.id} className={`${RISK_ROW[inv.risk_level]} transition-colors`}>
                      <td className="px-6 py-3.5 font-medium text-zinc-200">
                        {inv.customer_segment}
                      </td>
                      <td className="px-6 py-3.5 text-right text-zinc-300 font-mono">
                        ${inv.invoice_amount.toLocaleString()}
                      </td>
                      <td className="px-6 py-3.5 text-right text-zinc-400 font-mono">
                        {inv.customer_avg_past_delay}d
                      </td>
                      <td className="px-6 py-3.5 text-right text-zinc-200 font-mono font-semibold">
                        {inv.predicted_days_late}
                      </td>
                      <td className="px-6 py-3.5 text-center">
                        <span className={`inline-block px-2.5 py-0.5 rounded text-xs font-semibold tracking-wide ${RISK_BADGE[inv.risk_level]}`}>
                          {inv.risk_level}
                        </span>
                        {inv.reason && (
                          <p className="mt-1.5 text-[11px] text-zinc-500 leading-snug max-w-[180px] mx-auto">
                            {inv.reason}
                          </p>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ── Empty state ── */}
        {invoices.length === 0 && (
          <div className="text-center py-16 text-zinc-600 text-sm">
            No forecasts yet. Submit an invoice above to get started.
          </div>
        )}

      </main>
    </div>
  );
}

// ── Sub-component ────────────────────────────────────────────────────────────
function StatCard({ label, value, accent }) {
  const valueColor =
    accent === 'red' && value > 0
      ? 'text-red-400'
      : 'text-white';

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl px-6 py-5">
      <p className="text-xs text-zinc-500 uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-3xl font-semibold tabular-nums ${valueColor}`}>{value}</p>
    </div>
  );
}
