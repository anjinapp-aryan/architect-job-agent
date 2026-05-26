import Link from "next/link";
import { api, Job } from "@/lib/api";

export default async function JobsPage() {
  let jobs: Job[] = [];
  let error: string | null = null;
  try {
    jobs = await api<Job[]>("/api/jobs?limit=200");
  } catch (e: any) {
    error = e?.message ?? "Failed to load jobs";
  }

  if (error) return <p className="text-red-600">{error}</p>;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Jobs ({jobs.length})</h2>
      <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 dark:bg-slate-900">
            <tr>
              <th className="text-left p-3">Title</th>
              <th className="text-left p-3">Company</th>
              <th className="text-left p-3">Country</th>
              <th className="text-left p-3">Source</th>
              <th className="text-right p-3">Score</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {jobs.map(j => (
              <tr key={j.id} className="border-t border-slate-200 dark:border-slate-800">
                <td className="p-3">
                  <Link href={`/jobs/${j.id}`} className="hover:underline">
                    {j.title}
                  </Link>
                </td>
                <td className="p-3">{j.company_name}</td>
                <td className="p-3">{j.country ?? "—"}</td>
                <td className="p-3">{j.source}</td>
                <td className="p-3 text-right tabular-nums">
                  {j.match_score != null ? j.match_score : "—"}
                </td>
                <td className="p-3 text-right">
                  {j.url && (
                    <a href={j.url} target="_blank" rel="noopener noreferrer"
                       className="text-indigo-600 hover:underline">Open</a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
