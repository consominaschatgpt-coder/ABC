import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Organization, Role, User } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const ROLES: Role[] = ["admin", "gestor", "coordenador", "coletor", "convidado"];

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("coletor");
  const [organizationId, setOrganizationId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const canCreate = currentUser?.role === "admin";

  async function loadUsers() {
    const data = await api.get<User[]>("/users");
    setUsers(data);
  }

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        await loadUsers();
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
      await api.post("/users", {
        name,
        email,
        password,
        role,
        organization_id: organizationId,
      });
      setName("");
      setEmail("");
      setPassword("");
      await loadUsers();
    } catch {
      setError("Não foi possível criar o usuário (email já cadastrado?)");
    }
  }

  if (loading) return <p>Carregando...</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Usuários</h1>
      </div>

      {canCreate && (
        <form className="card form-grid" onSubmit={handleCreate}>
          <div className="form-row">
            <label>
              Nome
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
          </div>
          <div className="form-row">
            <label>
              Papel
              <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
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
          </div>
        </form>
      )}
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Email</th>
            <th>Papel</th>
            <th>Ativo</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td>{u.email}</td>
              <td>{u.role}</td>
              <td>{u.is_active ? "Sim" : "Não"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
