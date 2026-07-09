import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import ScrapePage from "./pages/ScrapePage";
import JobsPage from "./pages/JobsPage";
import HistoryPage from "./pages/HistoryPage";
import SchedulesPage from "./pages/SchedulesPage";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<ScrapePage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/schedules" element={<SchedulesPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
