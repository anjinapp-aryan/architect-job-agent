import { api, Application } from "@/lib/api";

export default async function ApplicationsPage() {
  const apps = await api<Application[]>("/api/applications");
  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Applications ({apps.length})</h2>
      <table className="w-full text-sm border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
        <thead className="bg-slate-100 dark:bg-slate-900">
          <tr>
            <th className="text-left p-3">Job</th>
            <th className="text-left p-3">Status</th>
            <th className="text-left p-3">Notes</th>
            <th className="text-left p-3">Updated</th>
          </tr>
        </thead>
        <tbody>
          {apps.map(a => (
            <tr key={a.id} className="border-t border-slate-200 dark:border-slate-800">
              <td className="p-3">#{a.job_id}</td>
              <td className="p-3">{a.status}</td>
              <td className="p-3">{a.notes ?? "—"}</td>
              <td className="p-3">{new Date(a.updated_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
