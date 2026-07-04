import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Team, User } from "../api/types";
import { useAuth } from "../auth/AuthContext";

export default function TeamMembersPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<User[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const canManage = user?.role === "admin";

  async function loadMembers() {
    const [teamData, membersData] = await Promise.all([
      api.get<Team>(`/teams/${id}`),
      api.get<User[]>(`/teams/${id}/members`),
    ]);
    setTeam(teamData);
    setMembers(membersData);
  }

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        await loadMembers();
        if (canManage) {
          const users = await api.get<User[]>("/users");
          setAllUsers(users);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post(`/teams/${id}/members`, { user_id: selectedUserId });
      await loadMembers();
    } catch {
      setError("Não foi possível adicionar o usuário (talvez já esteja na equipe)");
    }
  }

  async function handleRemove(userId: string) {
    await api.delete(`/teams/${id}/members/${userId}`);
    await loadMembers();
  }

  if (loading || !team) return <p>Carregando...</p>;

  const availableUsers = allUsers.filter((u) => !members.some((m) => m.id === u.id));

  return (
    <div>
      <div className="page-header">
        <h1>Membros de {team.name}</h1>
        <Link to="/teams" className="muted">
          ← voltar para equipes
        </Link>
      </div>

      {canManage && (
        <form className="card form-row" onSubmit={handleAdd}>
          <label>
            Adicionar usuário
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              required
            >
              <option value="" disabled>
                Selecione...
              </option>
              {availableUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.role})
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={!selectedUserId}>
            Adicionar
          </button>
        </form>
      )}
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Email</th>
            <th>Papel</th>
            {canManage && <th></th>}
          </tr>
        </thead>
        <tbody>
          {members.map((m) => (
            <tr key={m.id}>
              <td>{m.name}</td>
              <td>{m.email}</td>
              <td>{m.role}</td>
              {canManage && (
                <td>
                  <button className="secondary" onClick={() => handleRemove(m.id)}>
                    Remover
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
