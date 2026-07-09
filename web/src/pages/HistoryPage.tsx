import { useState, useEffect } from "react";
import { Clock, CheckCircle, XCircle, Loader2, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function HistoryPage() {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("/api/scrapes")
      .then(res => res.json())
      .then(data => setRuns(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="animate-in fade-in duration-500">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Scrape History</h1>
        <p className="text-gray-500 dark:text-gray-400">View past scrape runs, their status, and jobs found.</p>
      </header>

      {loading ? (
        <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full" /></div>
      ) : runs.length === 0 ? (
        <div className="text-center py-20 text-gray-500 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800">
          <Clock className="mx-auto mb-4 opacity-50" size={48} />
          <p className="text-lg">No scrape history found.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-800">
                  <th className="py-4 px-6 font-semibold text-sm text-gray-600 dark:text-gray-400">Status</th>
                  <th className="py-4 px-6 font-semibold text-sm text-gray-600 dark:text-gray-400">Started At</th>
                  <th className="py-4 px-6 font-semibold text-sm text-gray-600 dark:text-gray-400">Jobs Found</th>
                  <th className="py-4 px-6 font-semibold text-sm text-gray-600 dark:text-gray-400">Config</th>
                  <th className="py-4 px-6 text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                {runs.map(run => (
                  <tr key={run.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        {run.status === 'completed' && <CheckCircle size={16} className="text-green-500" />}
                        {run.status === 'failed' && <XCircle size={16} className="text-red-500" />}
                        {run.status === 'running' && <Loader2 size={16} className="text-brand-500 animate-spin" />}
                        {run.status === 'queued' && <Clock size={16} className="text-gray-500" />}
                        <span className="capitalize font-medium">{run.status}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-gray-600 dark:text-gray-400">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-6 font-medium">
                      {run.progress?.jobs_found || 0}
                    </td>
                    <td className="py-4 px-6">
                      <div className="text-xs text-gray-500 truncate max-w-[200px]">
                        {run.config ? JSON.stringify(run.config) : '-'}
                      </div>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <button 
                        onClick={() => navigate(`/jobs?scrape_run_id=${run.id}`)}
                        className="p-2 text-brand-600 hover:bg-brand-50 rounded-lg transition-colors inline-flex items-center gap-1 text-sm font-medium"
                      >
                        View Jobs <ArrowRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
