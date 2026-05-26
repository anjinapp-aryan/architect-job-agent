"use client";

import { useState } from "react";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SearchPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  async function trigger() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${BASE}/api/search/run`, { method: "POST" });
      if (!r.ok) throw new Error(`${r.status}`);
      setResult(await r.json());
    } catch (e: any) {
      setError(e?.message ?? "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Trigger search</h2>
      <p className="text-sm text-slate-500">
        Runs JobSpy across every (country × role) pair defined in your YAML
        configuration. New jobs are deduped by fingerprint.
      </p>
      <button
        onClick={trigger}
        disabled={loading}
        className="rounded-lg bg-indigo-600 text-white px-4 py-2 disabled:opacity-50"
      >
        {loading ? "Searching..." : "Run search"}
      </button>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      {result && (
        <pre className="text-xs bg-slate-100 dark:bg-slate-900 p-4 rounded-xl overflow-x-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
