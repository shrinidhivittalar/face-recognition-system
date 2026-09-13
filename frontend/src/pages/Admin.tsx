import { useCallback, useEffect, useState } from "react";
import { deleteIdentity, listIdentities } from "../api/client";
import type { IdentityOut } from "../types";
import { StatusPanel } from "../components/StatusPanel";

export function Admin() {
  const [identities, setIdentities] = useState<IdentityOut[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await listIdentities();
      setIdentities(data);
      setErrorMessage(null);
    } catch {
      setErrorMessage("Could not load identities. Is the backend running?");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = useCallback(
    async (id: string) => {
      await deleteIdentity(id);
      load();
    },
    [load]
  );

  return (
    <div className="page page-admin">
      <h1>Manage Identities</h1>
      <p className="hint">
        No authentication is enforced on this demo view. Do not expose this page publicly
        without adding authorization.
      </p>

      {errorMessage && <StatusPanel variant="error" title="Unavailable" message={errorMessage} />}

      {identities && identities.length === 0 && (
        <StatusPanel variant="idle" title="No identities enrolled yet" />
      )}

      {identities && identities.length > 0 && (
        <table className="identity-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Samples</th>
              <th>Enrolled</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {identities.map((identity) => (
              <tr key={identity.id}>
                <td>{identity.display_name}</td>
                <td>{identity.sample_count}</td>
                <td>{new Date(identity.created_at).toLocaleDateString()}</td>
                <td>
                  <button className="btn btn-text" onClick={() => handleDelete(identity.id)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
