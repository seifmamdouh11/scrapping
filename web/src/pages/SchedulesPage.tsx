import { useState, useEffect } from "react";
import { Calendar, Plus, Power, Clock } from "lucide-react";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/schedules")
      .then(res => res.json())
      .then(data => setSchedules(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const toggleSchedule = async (id: number, enabled: boolean) => {
    try {
      await fetch(`/api/schedules/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled })
      });
      setSchedules(schedules.map(s => s.id === id ? { ...s, enabled } : s));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="animate-in fade-in duration-500">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold mb-2">Scheduled Scrapes</h1>
          <p className="text-gray-500 dark:text-gray-400">Automate your job scraping tasks with recurring schedules.</p>
        </div>
        <button className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl font-medium transition-colors flex items-center gap-2 shadow-lg shadow-brand-500/30">
          <Plus size={18} /> New Schedule
        </button>
      </header>

      {loading ? (
        <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full" /></div>
      ) : schedules.length === 0 ? (
        <div className="text-center py-20 text-gray-500 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800">
          <Calendar className="mx-auto mb-4 opacity-50" size={48} />
          <p className="text-lg">No schedules configured.</p>
          <p className="text-sm mt-1">Create a schedule to automate scraping.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {schedules.map(schedule => (
            <div key={schedule.id} className={`p-6 bg-white dark:bg-gray-900 border rounded-2xl shadow-sm transition-colors ${schedule.enabled ? 'border-brand-200 dark:border-brand-900/30 ring-1 ring-brand-500/20' : 'border-gray-200 dark:border-gray-800 opacity-75'}`}>
              <div className="flex justify-between items-start mb-4">
                <h3 className="font-semibold text-lg">{schedule.name}</h3>
                <button 
                  onClick={() => toggleSchedule(schedule.id, !schedule.enabled)}
                  className={`p-2 rounded-full transition-colors ${schedule.enabled ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}
                  title={schedule.enabled ? 'Disable Schedule' : 'Enable Schedule'}
                >
                  <Power size={18} />
                </button>
              </div>
              
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-4 bg-gray-50 dark:bg-gray-800 p-2.5 rounded-lg">
                <Clock size={16} className="text-brand-500" />
                <span className="font-mono">{schedule.cron_expression}</span>
              </div>

              <div className="text-xs text-gray-500 space-y-1">
                <p>Next run: <span className="font-medium text-gray-900 dark:text-gray-100">{new Date(schedule.next_run_at).toLocaleString()}</span></p>
                {schedule.last_run_at && (
                  <p>Last run: {new Date(schedule.last_run_at).toLocaleString()}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
