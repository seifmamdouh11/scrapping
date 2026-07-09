import { useState, useEffect } from "react";
import { Play, Loader2, CheckCircle, AlertCircle, Clock } from "lucide-react";

export default function ScrapePage() {
  const [categories, setCategories] = useState<any[]>([]);
  const [selectedParent, setSelectedParent] = useState("");
  const [selectedSub, setSelectedSub] = useState<string[]>([]);
  
  const [keyword, setKeyword] = useState("");
  const [location, setLocation] = useState("Egypt");
  const [pages, setPages] = useState(1);
  const [platforms, setPlatforms] = useState({ linkedin: true, wuzzuf: true });
  
  const [isScraping, setIsScraping] = useState(false);
  const [progress, setProgress] = useState<any>(null);
  const [scrapeRunId, setScrapeRunId] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/categories")
      .then(res => res.json())
      .then(data => setCategories(data))
      .catch(console.error);
  }, []);

  useEffect(() => {
    let interval: any;
    if (isScraping && scrapeRunId) {
      interval = setInterval(() => {
        fetch(`/api/scrapes/${scrapeRunId}`)
          .then(res => res.json())
          .then(data => {
            setProgress(data.progress);
            if (data.status === "completed" || data.status === "failed") {
              setIsScraping(false);
              clearInterval(interval);
            }
          })
          .catch(console.error);
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isScraping, scrapeRunId]);

  const handleStartScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedParent) return;

    setIsScraping(true);
    setProgress({ status: "Starting..." });

    try {
      const res = await fetch("/api/scrapes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          config: {
            parent: selectedParent,
            categories: selectedSub,
            keyword,
            location,
            pages,
            platforms: Object.keys(platforms).filter(k => platforms[k as keyof typeof platforms])
          }
        })
      });
      const data = await res.json();
      setScrapeRunId(data.id);
    } catch (error) {
      console.error(error);
      setIsScraping(false);
      setProgress({ error: "Failed to start scrape" });
    }
  };

  const parentOptions = categories || [];
  const selectedParentObj = parentOptions.find(p => p.name === selectedParent);
  const subOptions = selectedParentObj ? selectedParentObj.children : [];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">New Scrape Task</h1>
        <p className="text-gray-500 dark:text-gray-400">Configure and launch a new job scraping session across multiple platforms.</p>
      </header>

      <div className="grid lg:grid-cols-3 gap-8">
        <form onSubmit={handleStartScrape} className="lg:col-span-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
          <div className="space-y-6">
            {/* Category Selection */}
            <div>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                1. Select Categories
              </h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">Industry (Parent)</label>
                  <select 
                    required
                    disabled={isScraping}
                    value={selectedParent}
                    onChange={(e) => {
                      setSelectedParent(e.target.value);
                      setSelectedSub([]);
                    }}
                    className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                  >
                    <option value="">Select Industry...</option>
                    {parentOptions.map(p => (
                      <option key={p.id} value={p.name}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Subcategories (Optional)</label>
                  <div className="h-40 overflow-y-auto bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-2 space-y-1">
                    {!selectedParent ? (
                      <p className="text-sm text-gray-400 p-2 text-center mt-8">Select an industry first</p>
                    ) : (
                      subOptions.map((sub: any) => (
                        <label key={sub.id} className="flex items-center gap-2 p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg cursor-pointer">
                          <input 
                            type="checkbox"
                            disabled={isScraping}
                            checked={selectedSub.includes(sub.name)}
                            onChange={(e) => {
                              if (e.target.checked) setSelectedSub([...selectedSub, sub.name]);
                              else setSelectedSub(selectedSub.filter(s => s !== sub.name));
                            }}
                            className="rounded text-brand-600 focus:ring-brand-500 w-4 h-4"
                          />
                          <span className="text-sm">{sub.name}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>

            <hr className="border-gray-200 dark:border-gray-800" />

            {/* Target Configuration */}
            <div>
              <h2 className="text-lg font-semibold mb-4">2. Target Configuration</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">Keyword Override</label>
                  <input 
                    type="text"
                    disabled={isScraping}
                    value={keyword}
                    onChange={e => setKeyword(e.target.value)}
                    placeholder="e.g. React Developer"
                    className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Location</label>
                  <input 
                    type="text"
                    disabled={isScraping}
                    value={location}
                    onChange={e => setLocation(e.target.value)}
                    placeholder="e.g. Egypt, Remote"
                    className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Pages per Platform</label>
                  <input 
                    type="number"
                    min="1" max="100"
                    disabled={isScraping}
                    value={pages}
                    onChange={e => setPages(parseInt(e.target.value))}
                    className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Platforms</label>
                  <div className="flex gap-4 mt-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={platforms.linkedin} disabled={isScraping} onChange={e => setPlatforms({...platforms, linkedin: e.target.checked})} className="rounded text-brand-600 focus:ring-brand-500 w-4 h-4" />
                      <span>LinkedIn</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={platforms.wuzzuf} disabled={isScraping} onChange={e => setPlatforms({...platforms, wuzzuf: e.target.checked})} className="rounded text-brand-600 focus:ring-brand-500 w-4 h-4" />
                      <span>Wuzzuf</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4">
              <button 
                type="submit" 
                disabled={isScraping || !selectedParent}
                className="w-full sm:w-auto px-8 py-3 bg-brand-600 hover:bg-brand-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white rounded-xl font-medium transition-colors flex items-center justify-center gap-2 shadow-lg shadow-brand-500/30"
              >
                {isScraping ? (
                  <><Loader2 size={18} className="animate-spin" /> Scraping...</>
                ) : (
                  <><Play size={18} /> Start Scrape</>
                )}
              </button>
            </div>
          </div>
        </form>

        {/* Live Progress Panel */}
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm h-fit sticky top-6">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
            Live Progress
          </h3>
          
          {!progress ? (
            <div className="text-center py-12 text-gray-400">
              <Clock className="mx-auto mb-2 opacity-50" size={32} />
              <p className="text-sm">No active scrape task.<br/>Start a scrape to see progress.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl text-sm">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Status</span>
                  <span className="capitalize font-medium text-brand-600 dark:text-brand-400">{progress.status || (isScraping ? 'Running' : 'Finished')}</span>
                </div>
                {progress.current_category && (
                  <div className="mt-2">
                    <span className="text-gray-500 text-xs">Current Target:</span>
                    <p className="font-medium truncate">{progress.current_category}</p>
                  </div>
                )}
                {progress.jobs_found !== undefined && (
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-gray-500 text-xs">Jobs Found:</span>
                    <span className="font-bold text-lg">{progress.jobs_found}</span>
                  </div>
                )}
                {progress.error && (
                  <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-xs flex gap-2 items-start">
                    <AlertCircle size={14} className="shrink-0 mt-0.5" />
                    <p>{progress.error}</p>
                  </div>
                )}
              </div>
              
              {!isScraping && progress && !progress.error && (
                <div className="p-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-xl text-sm flex items-center gap-2">
                  <CheckCircle size={16} />
                  <span>Scrape completed successfully!</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
