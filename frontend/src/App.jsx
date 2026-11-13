import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import Navbar from "./components/Navbar.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import Catalog from "./pages/Catalog.jsx";
import MovieDetail from "./pages/MovieDetail.jsx";
import Profile from "./pages/Profile.jsx";
import TopRated from "./pages/TopRated.jsx";
import WatchlistDetail from "./pages/WatchlistDetail.jsx";
import Watchlists from "./pages/Watchlists.jsx";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <p className="notice">Checking your account…</p>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

export default function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Navbar />
      <main id="main" className="page">
        <Routes>
          <Route path="/" element={<Catalog />} />
          <Route path="/movies/:id" element={<MovieDetail />} />
          <Route path="/top-rated" element={<TopRated />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route
            path="/profile"
            element={
              <RequireAuth>
                <Profile />
              </RequireAuth>
            }
          />
          <Route
            path="/watchlists"
            element={
              <RequireAuth>
                <Watchlists />
              </RequireAuth>
            }
          />
          <Route
            path="/watchlists/:id"
            element={
              <RequireAuth>
                <WatchlistDetail />
              </RequireAuth>
            }
          />
          <Route
            path="*"
            element={
              <p className="notice">
                There's no page here. <Link to="/">Go to films</Link>
              </p>
            }
          />
        </Routes>
      </main>
    </>
  );
}
