import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import Poster from "../components/Poster.jsx";

// A fixed little poster stack, so the auth page carries the same visual language.
const DECOR = [
  { movie_id: 3, title: "Matinee", release_yr: 1971, language_name: "Hindi", age_rating: "U" },
  { movie_id: 6, title: "Interval", release_yr: 1984, language_name: "Telugu", age_rating: "U/A" },
  { movie_id: 1, title: "Encore", release_yr: 2003, language_name: "English", age_rating: "PG" },
];

export default function AuthPage({ mode }) {
  const isRegister = mode === "register";
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from || "/";

  const [identifier, setIdentifier] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={redirectTo} replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (isRegister && username.trim().length < 3) {
      setError("Username needs at least 3 characters.");
      return;
    }
    if (isRegister && password.length < 6) {
      setError("Password needs at least 6 characters.");
      return;
    }
    setBusy(true);
    try {
      if (isRegister) await register({ username: username.trim(), email: email.trim(), password });
      else await login(identifier.trim(), password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <div className="auth-art" aria-hidden="true">
        {DECOR.map((m) => (
          <Poster key={m.movie_id} movie={m} />
        ))}
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <h1>{isRegister ? "Make an account" : "Welcome back"}</h1>
        <p className="muted">
          {isRegister
            ? "Keep watchlists and post reviews."
            : "Log in to see your watchlists and reviews."}
        </p>

        {isRegister ? (
          <>
            <label className="field">
              <span>Username</span>
              <input
                className="input"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </label>
            <label className="field">
              <span>Email</span>
              <input
                className="input"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
          </>
        ) : (
          <label className="field">
            <span>Username or email</span>
            <input
              className="input"
              autoComplete="username"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
            />
          </label>
        )}

        <label className="field">
          <span>Password</span>
          <input
            className="input"
            type="password"
            autoComplete={isRegister ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        <button className="btn btn-ink btn-block" disabled={busy}>
          {busy ? "One moment…" : isRegister ? "Sign up" : "Log in"}
        </button>

        <p className="muted switch">
          {isRegister ? (
            <>
              Have an account?{" "}
              <Link to="/login" state={location.state}>
                Log in
              </Link>
            </>
          ) : (
            <>
              New here?{" "}
              <Link to="/register" state={location.state}>
                Make an account
              </Link>
            </>
          )}
        </p>
      </form>
    </div>
  );
}
