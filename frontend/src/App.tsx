import { Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Intake from './pages/Intake';
import LiveAnalysis from './pages/LiveAnalysis';
import Decision from './pages/Decision';
import CAMViewer from './pages/CAMViewer';
import Layout from './components/Layout';

export default function App() {
  return (
    <div className="noise">
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/intake" element={<Intake />} />
          <Route path="/cases/:caseId/live" element={<LiveAnalysis />} />
          <Route path="/cases/:caseId/decision" element={<Decision />} />
          <Route path="/cases/:caseId/cam" element={<CAMViewer />} />
        </Route>
      </Routes>
    </div>
  );
}
