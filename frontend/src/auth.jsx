import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, getToken, setToken, setUnauthorizedHandler } from "./api.js";

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(() => Boolean(getToken()));

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  // If any authenticated request comes back 401 (expired token), sign the user out.
  useEffect(() => {
    setUnauthorizedHandler(logout);
  }, [logout]);

  // Restore the session on page load.
  useEffect(() => {
    if (!getToken()) return undefined;
    let alive = true;
    api
      .me()
      .then((u) => alive && setUser(u))
      .catch(() => alive && logout())
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [logout]);

  const login = useCallback(async (identifier, password) => {
    const data = await api.login(identifier, password);
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const register = useCallback(
    async ({ username, email, password }) => {
      await api.register({ username, email, password });
      await login(username, password);
    },
    [login]
  );

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
