import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Intake from './pages/Intake';
import LiveAnalysis from './pages/LiveAnalysis';
import Decision from './pages/Decision';
import CAMViewer from './pages/CAMViewer';
import Layout from './components/Layout';
import { useAuthStore } from './store/auth';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const location = useLocation();
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <>{children}</>;
}

export default function App() {
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage);
  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  return (
    <div className="noise">
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route element={<RequireAuth><Layout /></RequireAuth>}>
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
