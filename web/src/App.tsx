import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import ContractsPage from "./pages/ContractsPage";
import TeamsPage from "./pages/TeamsPage";
import TeamMembersPage from "./pages/TeamMembersPage";
import UsersPage from "./pages/UsersPage";
import FormTemplatesPage from "./pages/FormTemplatesPage";
import FormTemplateDetailPage from "./pages/FormTemplateDetailPage";
import RdasPage from "./pages/RdasPage";
import RdaDetailPage from "./pages/RdaDetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Navigate to="/rdas" replace />} />
            <Route path="/rdas" element={<RdasPage />} />
            <Route path="/rdas/:id" element={<RdaDetailPage />} />
            <Route path="/form-templates" element={<FormTemplatesPage />} />
            <Route path="/form-templates/:id" element={<FormTemplateDetailPage />} />
            <Route
              path="/contracts"
              element={
                <ProtectedRoute roles={["admin", "gestor", "coordenador"]}>
                  <ContractsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teams"
              element={
                <ProtectedRoute roles={["admin", "gestor", "coordenador"]}>
                  <TeamsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teams/:id"
              element={
                <ProtectedRoute roles={["admin", "gestor", "coordenador"]}>
                  <TeamMembersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute roles={["admin", "gestor"]}>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
