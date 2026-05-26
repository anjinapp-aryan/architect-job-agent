import { api } from "@/lib/api";

type Dashboard = {
  total_jobs: number;
  jobs_by_country: Record<string, number>;
  jobs_by_role: Record<string, number>;
  high_scoring_jobs: number;
  minimum_match_score: number;
  application_pipeline: Record<string, number>;
  recent_searches: any[];
};

export default async function Page() {
  let data: Dashboard | null = null;
  let error: string | null = null;
  try {
    data = await api<Dashboard>("/api/dashboard");
  } catch (e: any) {
    error = e?.message ?? "Failed to load dashboard";
  }

  if (error || !data) {
    return <p className="text-red-600">Dashboard unavailable: {error}</p>;
  }

  return (
    <div className="space-y-8">
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Stat label="Total jobs" value={data.total_jobs} />
        <Stat label={`High-scoring (≥${data.minimum_match_score})`} value={data.high_scoring_jobs} />
        <Stat label="Applied" value={data.application_pipeline?.Applied ?? 0} />
      </section>

      <Section title="Jobs by country">
        <Bars data={data.jobs_by_country} />
      </Section>

      <Section title="Jobs by role">
        <Bars data={data.jobs_by_role} />
      </Section>

      <Section title="Application pipeline">
        <Bars data={data.application_pipeline} />
      </Section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-5">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-3xl font-semibold mt-1">{value}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-lg font-semibold mb-3">{title}</h2>
      {children}
    </section>
  );
}

function Bars({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return (
    <ul className="space-y-2">
      {entries.map(([k, v]) => (
        <li key={k} className="flex items-center gap-3">
          <div className="w-40 text-sm truncate">{k}</div>
          <div className="flex-1 h-3 bg-slate-200 dark:bg-slate-800 rounded">
            <div
              className="h-3 bg-indigo-500 rounded"
              style={{ width: `${(v / max) * 100}%` }}
            />
          </div>
          <div className="w-10 text-right text-sm tabular-nums">{v}</div>
        </li>
      ))}
    </ul>
  );
}
