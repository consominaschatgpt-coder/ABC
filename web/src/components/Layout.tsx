import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../api/types";

interface NavItem {
  to: string;
  label: string;
  roles: Role[];
}

const NAV_ITEMS: NavItem[] = [
  { to: "/rdas", label: "RDAs", roles: ["admin", "gestor", "coordenador", "coletor"] },
  { to: "/form-templates", label: "Formulários", roles: ["admin", "gestor", "coordenador", "coletor"] },
  { to: "/contracts", label: "Contratos", roles: ["admin", "gestor", "coordenador"] },
  { to: "/teams", label: "Equipes", roles: ["admin", "gestor", "coordenador"] },
  { to: "/users", label: "Usuários", roles: ["admin", "gestor"] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  if (!user) return null;

  const visibleItems = NAV_ITEMS.filter((item) => item.roles.includes(user.role));

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand">RDA de Campo</div>
        <nav className="topbar-nav">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="topbar-user">
          <span>
            {user.name} <small>({user.role})</small>
          </span>
          <button onClick={logout}>Sair</button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
