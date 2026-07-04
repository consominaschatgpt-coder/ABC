import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type {
  Contract,
  FormTemplateWithCurrentVersion,
  Rda,
  RdaStatus,
  Team,
} from "../api/types";
import { useAuth } from "../auth/AuthContext";

const STATUS_OPTIONS: { value: RdaStatus | ""; label: string }[] = [
  { value: "", label: "Todos os status" },
  { value: "rascunho", label: "Rascunho" },
  { value: "enviado", label: "Enviado" },
  { value: "em_revisao", label: "Em revisão" },
  { value: "aprovado", label: "Aprovado" },
  { value: "reprovado", label: "Reprovado" },
];

export default function RdasPage() {
  const { user } = useAuth();
  const [rdas, setRdas] = useState<Rda[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [myTeams, setMyTeams] = useState<Team[]>([]);
  const [statusFilter, setStatusFilter] = useState<RdaStatus | "">("");
  const [loading, setLoading] = useState(true);

  const canSeeAllTeams = user?.role !== "coletor";

  async function loadRdas() {
    const data = await api.get<Rda[]>("/rdas", {
      status_filter: statusFilter || undefined,
    });
    setRdas(data);
  }

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        await loadRdas();
        if (canSeeAllTeams) {
          const [contractsData, teamsData] = await Promise.all([
            api.get<Contract[]>("/contracts"),
            api.get<Team[]>("/teams"),
          ]);
          setContracts(contractsData);
          setTeams(teamsData);
        } else {
          const myTeamsData = await api.get<Team[]>("/users/me/teams");
          setMyTeams(myTeamsData);
          const uniqueContractIds = [...new Set(myTeamsData.map((t) => t.contract_id))];
          const contractsData = await Promise.all(
            uniqueContractIds.map((cid) => api.get<Contract>(`/contracts/${cid}`)),
          );
          setContracts(contractsData);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  function contractName(id: string) {
    return contracts.find((c) => c.id === id)?.name ?? id;
  }

  function teamName(id: string) {
    const allTeams = canSeeAllTeams ? teams : myTeams;
    return allTeams.find((t) => t.id === id)?.name ?? id;
  }

  if (loading) return <p>Carregando...</p>;

  return (
    <div>
      <div className="page-header">
        <h1>RDAs</h1>
      </div>

      {user?.role === "coletor" && (
        <NewRdaForm myTeams={myTeams} onCreated={loadRdas} />
      )}

      <div className="form-row card">
        <label>
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as RdaStatus | "")}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <table>
        <thead>
          <tr>
            <th>Contrato</th>
            <th>Equipe</th>
            <th>Status</th>
            <th>Enviado em</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rdas.map((r) => (
            <tr key={r.id}>
              <td>{contractName(r.contract_id)}</td>
              <td>{teamName(r.team_id)}</td>
              <td>
                <span className={`badge ${r.status}`}>{r.status}</span>
              </td>
              <td className="muted">
                {r.submitted_at ? new Date(r.submitted_at).toLocaleString("pt-BR") : "—"}
              </td>
              <td>
                <Link to={`/rdas/${r.id}`}>Abrir</Link>
              </td>
            </tr>
          ))}
          {rdas.length === 0 && (
            <tr>
              <td colSpan={5} className="muted">
                Nenhum RDA encontrado.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function NewRdaForm({ myTeams, onCreated }: { myTeams: Team[]; onCreated: () => void }) {
  const [teamId, setTeamId] = useState("");
  const [template, setTemplate] = useState<FormTemplateWithCurrentVersion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (myTeams.length > 0 && !teamId) setTeamId(myTeams[0].id);
  }, [myTeams, teamId]);

  useEffect(() => {
    async function loadTemplate() {
      setTemplate(null);
      const team = myTeams.find((t) => t.id === teamId);
      if (!team) return;
      const templates = await api.get<FormTemplateWithCurrentVersion[]>("/form-templates", {
        contract_id: team.contract_id,
      });
      if (templates.length === 0) return;
      const full = await api.get<FormTemplateWithCurrentVersion>(
        `/form-templates/${templates[0].id}`,
      );
      setTemplate(full);
    }
    if (teamId) loadTemplate();
  }, [teamId, myTeams]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const team = myTeams.find((t) => t.id === teamId);
    if (!team || !template?.current_version) return;
    setCreating(true);
    try {
      await api.post("/rdas", {
        contract_id: team.contract_id,
        team_id: team.id,
        form_template_version_id: template.current_version.id,
        answers: {},
      });
      onCreated();
    } catch {
      setError("Não foi possível criar o RDA");
    } finally {
      setCreating(false);
    }
  }

  if (myTeams.length === 0) {
    return <p className="muted">Você ainda não está vinculado a nenhuma equipe.</p>;
  }

  return (
    <form className="card form-row" onSubmit={handleCreate}>
      <label>
        Equipe
        <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
          {myTeams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      </label>
      {template && !template.current_version && (
        <p className="muted">Nenhum formulário publicado para esse contrato ainda.</p>
      )}
      <button type="submit" disabled={!template?.current_version || creating}>
        {creating ? "Criando..." : "Novo RDA"}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
