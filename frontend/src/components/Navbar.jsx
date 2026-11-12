import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="masthead">
      <Link to="/" className="wordmark" aria-label="CineTrack home">
        CineTrack
      </Link>
      <nav className="nav" aria-label="Main">
        <NavLink to="/" end>
          Films
        </NavLink>
        <NavLink to="/top-rated">Top rated</NavLink>
        {user && <NavLink to="/watchlists">Watchlists</NavLink>}
      </nav>
      <div className="account">
        {user ? (
          <>
            <span className="account-name">{user.username}</span>
            <button
              type="button"
              className="btn btn-text"
              onClick={() => {
                logout();
                navigate("/");
              }}
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn btn-text">
              Log in
            </Link>
            <Link to="/register" className="btn btn-ink">
              Sign up
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
