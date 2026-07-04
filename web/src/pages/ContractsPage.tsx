import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Contract, Organization } from "../api/types";
import { useAuth } from "../auth/AuthContext";

export default function ContractsPage() {
  const { user } = useAuth();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [name, setName] = useState("");
  const [organizationId, setOrganizationId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const canCreate = user?.role === "admin";

  async function loadContracts() {
    const data = await api.get<Contract[]>("/contracts");
    setContracts(data);
  }

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        await loadContracts();
        if (canCreate) {
          const orgs = await api.get<Organization[]>("/organizations");
          setOrganizations(orgs);
          if (orgs.length > 0) setOrganizationId(orgs[0].id);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/contracts", { name, organization_id: organizationId });
      setName("");
      await loadContracts();
    } catch {
      setError("Não foi possível criar o contrato");
    }
  }

  if (loading) return <p>Carregando...</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Contratos</h1>
      </div>

      {canCreate && (
        <form className="card form-row" onSubmit={handleCreate}>
          <label>
            Nome do contrato
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Organização
            <select value={organizationId} onChange={(e) => setOrganizationId(e.target.value)}>
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))}
            </select>
          </label>
          <button type="submit">Criar</button>
        </form>
      )}
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>ID</th>
          </tr>
        </thead>
        <tbody>
          {contracts.map((c) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td className="muted">{c.id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
