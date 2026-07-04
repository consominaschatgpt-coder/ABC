import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Contract, FormTemplate } from "../api/types";
import { useAuth } from "../auth/AuthContext";

export default function FormTemplatesPage() {
  const { user } = useAuth();
  const [templates, setTemplates] = useState<FormTemplate[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [name, setName] = useState("");
  const [contractId, setContractId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const canCreate = user?.role === "admin";
  const canSeeContracts = user?.role !== "coletor";

  async function loadTemplates() {
    const data = await api.get<FormTemplate[]>("/form-templates");
    setTemplates(data);
  }

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        await loadTemplates();
        if (canSeeContracts) {
          const contractsData = await api.get<Contract[]>("/contracts");
          setContracts(contractsData);
          if (contractsData.length > 0) setContractId(contractsData[0].id);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function contractName(id: string) {
    return contracts.find((c) => c.id === id)?.name ?? id;
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/form-templates", {
        name,
        contract_id: contractId,
        fields: [],
      });
      setName("");
      await loadTemplates();
    } catch {
      setError("Não foi possível criar o modelo de formulário");
    }
  }

  if (loading) return <p>Carregando...</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Modelos de formulário (RDA)</h1>
      </div>

      {canCreate && (
        <form className="card form-row" onSubmit={handleCreate}>
          <label>
            Nome do modelo
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
          <button type="submit">Criar (rascunho vazio)</button>
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
          {templates.map((t) => (
            <tr key={t.id}>
              <td>{t.name}</td>
              <td>{canSeeContracts ? contractName(t.contract_id) : t.contract_id}</td>
              <td>
                <Link to={`/form-templates/${t.id}`}>Abrir</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
