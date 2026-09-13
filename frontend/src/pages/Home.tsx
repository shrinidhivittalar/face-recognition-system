import { Link } from "react-router-dom";

export function Home() {
  return (
    <div className="page page-home">
      <div className="hero">
        <h1>Face Recognition Identification System</h1>
        <p className="hero-subtitle">
          Enroll a person, then identify a new photo against everyone you&apos;ve enrolled.
          This is an identification prototype — not a high-assurance biometric
          authentication product.
        </p>
      </div>

      <div className="entry-cards">
        <Link to="/enroll" className="entry-card">
          <span className="entry-card-icon" aria-hidden="true">
            +
          </span>
          <h2>Enroll Person</h2>
          <p>Register a new identity with a face photo.</p>
        </Link>

        <Link to="/identify" className="entry-card">
          <span className="entry-card-icon" aria-hidden="true">
            ?
          </span>
          <h2>Identify Face</h2>
          <p>Check a photo against enrolled identities.</p>
        </Link>

        <Link to="/admin" className="entry-card entry-card-secondary">
          <span className="entry-card-icon" aria-hidden="true">
            ≡
          </span>
          <h2>Manage Identities</h2>
          <p>View and remove enrolled people.</p>
        </Link>
      </div>
    </div>
  );
}
