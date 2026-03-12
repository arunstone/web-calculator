import { useEffect, useState } from "react";

const emptyCalc = { operand_a: "", operand_b: "", operation: "add" };
const emptyAuth = { username: "", email: "", password: "" };

async function api(path, options = {}, token) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [registerForm, setRegisterForm] = useState(emptyAuth);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [calcForm, setCalcForm] = useState(emptyCalc);
  const [history, setHistory] = useState([]);
  const [authMessage, setAuthMessage] = useState("");
  const [calcMessage, setCalcMessage] = useState("");

  async function loadProfile(currentToken = token) {
    if (!currentToken) {
      setUser(null);
      setHistory([]);
      return;
    }
    const me = await api("/api/auth/me", {}, currentToken);
    setUser(me);
    const items = await api("/api/calculations", {}, currentToken);
    setHistory(items);
  }

  useEffect(() => {
    loadProfile().catch(() => {
      localStorage.removeItem("token");
      setToken("");
      setUser(null);
    });
  }, []);

  useEffect(() => {
    if (!token) {
      return undefined;
    }

    const interval = setInterval(() => {
      loadProfile(token).catch(() => undefined);
    }, 3000);

    return () => clearInterval(interval);
  }, [token]);

  async function handleRegister(event) {
    event.preventDefault();
    setAuthMessage("");
    const response = await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(registerForm)
    });
    setAuthMessage(`Registered ${response.username}. You can now log in.`);
    setRegisterForm(emptyAuth);
  }

  async function handleLogin(event) {
    event.preventDefault();
    setAuthMessage("");
    const response = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(loginForm)
    });
    localStorage.setItem("token", response.access_token);
    setToken(response.access_token);
    await loadProfile(response.access_token);
    setLoginForm({ email: "", password: "" });
  }

  async function handleCalculation(event) {
    event.preventDefault();
    setCalcMessage("");
    const response = await api(
      "/api/calculate",
      {
        method: "POST",
        body: JSON.stringify({
          operand_a: Number(calcForm.operand_a),
          operand_b: Number(calcForm.operand_b),
          operation: calcForm.operation
        })
      },
      token
    );
    setCalcMessage(`Queued request #${response.request_id}`);
    setCalcForm(emptyCalc);
    await loadProfile(token);
  }

  function logout() {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
    setHistory([]);
  }

  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">React + FastAPI + Celery</p>
          <h1>Queued calculator with auth and request history</h1>
          <p className="lede">
            All browser traffic goes through Nginx. Calculations are queued in Redis,
            processed by Celery, and stored in Postgres.
          </p>
        </div>
        {user ? (
          <div className="status-card">
            <span>Signed in as</span>
            <strong>{user.username}</strong>
            <small>{user.email}</small>
            <button onClick={logout}>Log out</button>
          </div>
        ) : (
          <div className="status-card">
            <span>Session</span>
            <strong>Guest</strong>
            <small>Register or log in to use the calculator</small>
          </div>
        )}
      </section>

      {!user ? (
        <section className="grid two">
          <form className="panel" onSubmit={handleRegister}>
            <h2>Register</h2>
            <input
              placeholder="Username"
              value={registerForm.username}
              onChange={(event) => setRegisterForm({ ...registerForm, username: event.target.value })}
              required
            />
            <input
              placeholder="Email"
              type="email"
              value={registerForm.email}
              onChange={(event) => setRegisterForm({ ...registerForm, email: event.target.value })}
              required
            />
            <input
              placeholder="Password"
              type="password"
              value={registerForm.password}
              onChange={(event) => setRegisterForm({ ...registerForm, password: event.target.value })}
              required
            />
            <button type="submit">Create account</button>
          </form>

          <form className="panel" onSubmit={handleLogin}>
            <h2>Login</h2>
            <input
              placeholder="Email"
              type="email"
              value={loginForm.email}
              onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })}
              required
            />
            <input
              placeholder="Password"
              type="password"
              value={loginForm.password}
              onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
              required
            />
            <button type="submit">Sign in</button>
            <p className="message">{authMessage}</p>
          </form>
        </section>
      ) : (
        <section className="grid two">
          <form className="panel" onSubmit={handleCalculation}>
            <h2>Calculator</h2>
            <input
              placeholder="First number"
              type="number"
              step="any"
              value={calcForm.operand_a}
              onChange={(event) => setCalcForm({ ...calcForm, operand_a: event.target.value })}
              required
            />
            <select
              value={calcForm.operation}
              onChange={(event) => setCalcForm({ ...calcForm, operation: event.target.value })}
            >
              <option value="add">Add</option>
              <option value="subtract">Subtract</option>
              <option value="multiply">Multiply</option>
              <option value="divide">Divide</option>
            </select>
            <input
              placeholder="Second number"
              type="number"
              step="any"
              value={calcForm.operand_b}
              onChange={(event) => setCalcForm({ ...calcForm, operand_b: event.target.value })}
              required
            />
            <button type="submit">Queue calculation</button>
            <p className="message">{calcMessage}</p>
          </form>

          <div className="panel">
            <h2>Request history</h2>
            <div className="history">
              {history.length === 0 ? (
                <p className="empty">No calculations yet.</p>
              ) : (
                history.map((item) => (
                  <article key={item.id} className="history-item">
                    <div>
                      <strong>
                        #{item.id} {item.operation}
                      </strong>
                      <span>
                        {item.operand_a} and {item.operand_b}
                      </span>
                    </div>
                    <div className={`badge ${item.status}`}>{item.status}</div>
                    <div>
                      {item.result !== null ? (
                        <strong>Result: {item.result}</strong>
                      ) : (
                        <span>{item.error_message || "Waiting for worker"}</span>
                      )}
                    </div>
                  </article>
                ))
              )}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
