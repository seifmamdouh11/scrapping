import { useState, useEffect } from "react";
import { Search, Filter, Download, ExternalLink, MapPin, Building, ChevronLeft, ChevronRight, X } from "lucide-react";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  
  // Filters
  const [q, setQ] = useState("");
  const [source, setSource] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const limit = 25;

  const [selectedJob, setSelectedJob] = useState<any>(null);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        skip: ((page - 1) * limit).toString(),
        limit: limit.toString(),
      });
      if (q) params.append("q", q);
      if (source) params.append("source", source);
      if (category) params.append("category", category);
      
      const res = await fetch(`/api/jobs?${params.toString()}`);
      const data = await res.json();
      setJobs(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchJobs();
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [q, source, category, page]);

  const handleExport = (format: 'csv' | 'json') => {
    const params = new URLSearchParams();
    if (q) params.append("q", q);
    if (source) params.append("source", source);
    if (category) params.append("category", category);
    
    window.open(`/api/exports/${format}?${params.toString()}`, '_blank');
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="animate-in fade-in duration-500 flex flex-col h-[calc(100vh-2rem)] md:h-[calc(100vh-4rem)]">
      <header className="mb-6 shrink-0 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-1">Scraped Jobs</h1>
          <p className="text-gray-500 dark:text-gray-400">Browse, filter, and export {total} collected jobs.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => handleExport('csv')} className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-2">
            <Download size={16} /> CSV
          </button>
          <button onClick={() => handleExport('json')} className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-2">
            <Download size={16} /> JSON
          </button>
        </div>
      </header>

      {/* Filters */}
      <div className="mb-6 shrink-0 grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm">
        <div className="relative md:col-span-2">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search titles, companies, descriptions..." 
            value={q}
            onChange={e => { setQ(e.target.value); setPage(1); }}
            className="w-full bg-gray-50 dark:bg-gray-800 border-none rounded-xl pl-10 pr-4 py-2.5 focus:ring-2 focus:ring-brand-500 outline-none"
          />
        </div>
        <select 
          value={source}
          onChange={e => { setSource(e.target.value); setPage(1); }}
          className="bg-gray-50 dark:bg-gray-800 border-none rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-brand-500 outline-none"
        >
          <option value="">All Sources</option>
          <option value="linkedin">LinkedIn</option>
          <option value="wuzzuf">Wuzzuf</option>
        </select>
        <input 
          type="text" 
          placeholder="Filter Category" 
          value={category}
          onChange={e => { setCategory(e.target.value); setPage(1); }}
          className="bg-gray-50 dark:bg-gray-800 border-none rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-brand-500 outline-none"
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden flex gap-6 relative">
        {/* Job List / Table */}
        <div className={`flex-1 overflow-y-auto ${selectedJob ? 'hidden lg:block lg:w-1/2 shrink-0' : 'w-full'}`}>
          {loading ? (
            <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full" /></div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-20 text-gray-500">
              <Filter className="mx-auto mb-4 opacity-50" size={48} />
              <p className="text-lg">No jobs match your filters.</p>
            </div>
          ) : (
            <div className="space-y-3 pb-4">
              {jobs.map(job => (
                <div 
                  key={job.id} 
                  onClick={() => setSelectedJob(job)}
                  className={`p-4 bg-white dark:bg-gray-900 border rounded-2xl cursor-pointer transition-all hover:shadow-md ${selectedJob?.id === job.id ? 'border-brand-500 ring-1 ring-brand-500' : 'border-gray-200 dark:border-gray-800'}`}
                >
                  <div className="flex justify-between items-start gap-4 mb-2">
                    <h3 className="font-semibold text-lg line-clamp-1">{job.title}</h3>
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${job.source === 'linkedin' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'}`}>
                      {job.source}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-600 dark:text-gray-400 mb-3">
                    <span className="flex items-center gap-1"><Building size={14} /> {job.company}</span>
                    <span className="flex items-center gap-1"><MapPin size={14} /> {job.location || 'Remote'}</span>
                  </div>
                  <p className="text-sm text-gray-500 line-clamp-2">{job.description}</p>
                </div>
              ))}
            </div>
          )}
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="sticky bottom-0 bg-white/90 dark:bg-gray-950/90 backdrop-blur-md py-4 border-t border-gray-200 dark:border-gray-800 flex justify-between items-center px-2 mt-4 rounded-b-2xl">
              <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
              ><ChevronLeft size={20} /></button>
              <span className="text-sm font-medium">Page {page} of {totalPages}</span>
              <button 
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
              ><ChevronRight size={20} /></button>
            </div>
          )}
        </div>

        {/* Job Details Drawer (Desktop) / Modal (Mobile handled by CSS classes above) */}
        {selectedJob && (
          <div className="absolute inset-0 lg:static lg:w-1/2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl flex flex-col shadow-xl lg:shadow-none z-10 animate-in slide-in-from-right lg:slide-in-from-bottom-0">
            <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center sticky top-0 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md z-10 rounded-t-2xl">
              <h2 className="font-bold text-lg">Job Details</h2>
              <button onClick={() => setSelectedJob(null)} className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1">
              <h1 className="text-2xl font-bold mb-2">{selectedJob.title}</h1>
              <div className="flex items-center gap-2 mb-6">
                <span className="font-medium text-brand-600 dark:text-brand-400">{selectedJob.company}</span>
                <span className="text-gray-300 dark:text-gray-600">•</span>
                <span className="text-gray-500">{selectedJob.location}</span>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                  <p className="text-xs text-gray-500 mb-1">Category</p>
                  <p className="font-medium">{selectedJob.category || 'N/A'}</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                  <p className="text-xs text-gray-500 mb-1">Type</p>
                  <p className="font-medium">{selectedJob.type || 'N/A'}</p>
                </div>
              </div>

              <div className="prose prose-sm dark:prose-invert max-w-none mb-8">
                <h3 className="text-lg font-semibold mb-3">Description</h3>
                <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
                  {selectedJob.description}
                </div>
              </div>
            </div>
            
            <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 rounded-b-2xl shrink-0">
              <a 
                href={selectedJob.applyLink} 
                target="_blank" 
                rel="noreferrer"
                className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-xl font-medium flex justify-center items-center gap-2 transition-colors"
              >
                Apply Now <ExternalLink size={16} />
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
