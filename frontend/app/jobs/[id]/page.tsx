import { api } from "@/lib/api";

type JobDetail = {
  id: number;
  title: string;
  company_name: string;
  country?: string;
  location?: string;
  url?: string;
  description?: string;
  match_score?: number;
  scoring_breakdown?: Record<string, number>;
  strengths?: string[];
  gaps?: string[];
  recommendation?: string;
};

export default async function JobPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const job = await api<JobDetail>(`/api/jobs/${id}`);

  return (
    <article className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold">{job.title}</h2>
        <p className="text-slate-500">
          {job.company_name} · {job.location ?? job.country ?? ""}
        </p>
        {job.url && (
          <a href={job.url} target="_blank" rel="noopener noreferrer"
             className="text-indigo-600 hover:underline text-sm">View original posting →</a>
        )}
      </header>

      {job.match_score != null && (
        <section className="rounded-xl border border-slate-200 dark:border-slate-800 p-5">
          <div className="flex items-baseline justify-between">
            <h3 className="font-medium">Match score</h3>
            <div className="text-3xl font-semibold">{job.match_score}</div>
          </div>
          {job.scoring_breakdown && (
            <ul className="mt-3 grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
              {Object.entries(job.scoring_breakdown).map(([k, v]) => (
                <li key={k} className="rounded bg-slate-100 dark:bg-slate-900 p-2">
                  <div className="text-slate-500 text-xs capitalize">{k}</div>
                  <div className="font-semibold">{v}</div>
                </li>
              ))}
            </ul>
          )}
          {job.recommendation && <p className="mt-3 text-sm">{job.recommendation}</p>}
        </section>
      )}

      {job.description && (
        <section>
          <h3 className="font-medium mb-2">Description</h3>
          <pre className="whitespace-pre-wrap text-sm leading-6">{job.description}</pre>
        </section>
      )}
    </article>
  );
}
