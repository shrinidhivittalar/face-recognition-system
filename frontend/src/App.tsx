import { Link, Route, Routes } from "react-router-dom";
import { Home } from "./pages/Home";
import { Enroll } from "./pages/Enroll";
import { Identify } from "./pages/Identify";
import { Admin } from "./pages/Admin";

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand">
          Face Recognition ID
        </Link>
        <nav>
          <Link to="/enroll">Enroll</Link>
          <Link to="/identify">Identify</Link>
          <Link to="/admin">Admin</Link>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/enroll" element={<Enroll />} />
          <Route path="/identify" element={<Identify />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
