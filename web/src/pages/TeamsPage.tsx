import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Contract, Team } from "../api/types";
import { useAuth } from "../auth/AuthContext";

export default function TeamsPage() {
  const { user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [name, setName] = useState("");
  const [contractId, setContractId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const canCreate = user?.role === "admin";

  async function loadAll() {
    const [teamsData, contractsData] = await Promise.all([
      api.get<Team[]>("/teams"),
      api.get<Contract[]>("/contracts"),
    ]);
    setTeams(teamsData);
    setContracts(contractsData);
    if (contractsData.length > 0 && !contractId) setContractId(contractsData[0].id);
  }

  useEffect(() => {
    loadAll().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function contractName(contractId: string) {
    return contracts.find((c) => c.id === contractId)?.name ?? contractId;
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/teams", { name, contract_id: contractId });
      setName("");
      await loadAll();
    } catch {
      setError("Não foi possível criar a equipe");
    }
  }

  if (loading) return <p>Carregando...</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Equipes</h1>
      </div>

      {canCreate && (
        <form className="card form-row" onSubmit={handleCreate}>
          <label>
            Nome da equipe
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Contrato
            <select value={contractId} onChange={(e) => setContractId(e.target.value)}>
              {contracts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
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
            <th>Contrato</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {teams.map((t) => (
            <tr key={t.id}>
              <td>{t.name}</td>
              <td>{contractName(t.contract_id)}</td>
              <td>
                <Link to={`/teams/${t.id}`}>Membros</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
