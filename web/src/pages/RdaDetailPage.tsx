import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { FieldDefinition, FormTemplateVersion, Rda, RdaAuditLog } from "../api/types";
import { useAuth } from "../auth/AuthContext";

export default function RdaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [rda, setRda] = useState<Rda | null>(null);
  const [version, setVersion] = useState<FormTemplateVersion | null>(null);
  const [auditLog, setAuditLog] = useState<RdaAuditLog[]>([]);
  const [answersDraft, setAnswersDraft] = useState<Record<string, string>>({});
  const [comment, setComment] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadAll() {
    const rdaData = await api.get<Rda>(`/rdas/${id}`);
    const [versionData, auditData] = await Promise.all([
      api.get<FormTemplateVersion>(`/form-template-versions/${rdaData.form_template_version_id}`),
      api.get<RdaAuditLog[]>(`/rdas/${id}/audit-log`),
    ]);
    setRda(rdaData);
    setVersion(versionData);
    setAuditLog(auditData);
    setAnswersDraft(stringifyAnswers(rdaData.answers, versionData.fields));
  }

  useEffect(() => {
    loadAll().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loading || !rda || !version || !user) return <p>Carregando...</p>;

  const isOwner = rda.submitted_by_id === user.id;
  const canEditAsColetor =
    user.role === "coletor" && isOwner && ["rascunho", "reprovado"].includes(rda.status);
  const canEditAsReviewer =
    (user.role === "admin" || user.role === "coordenador") &&
    ["enviado", "em_revisao"].includes(rda.status);
  const canEdit = canEditAsColetor || canEditAsReviewer;
  const canSubmit = user.role === "coletor" && isOwner && ["rascunho", "reprovado"].includes(rda.status);
  const canReview =
    (user.role === "admin" || user.role === "coordenador") &&
    ["enviado", "em_revisao"].includes(rda.status);
  const canStartReview = canReview && rda.status === "enviado";

  function isFieldActive(field: FieldDefinition, values: Record<string, string>): boolean {
    if (!field.condition) return true;
    return values[field.condition.field] === field.condition.equals;
  }

  function parseAnswerValue(field: FieldDefinition, raw: string): unknown {
    if (field.type === "numero") return raw === "" ? null : Number(raw);
    if (field.type === "selecao_multipla") {
      return raw
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
    }
    return raw;
  }

  async function saveAnswers() {
    setError(null);
    try {
      const changed: Record<string, unknown> = {};
      for (const field of version!.fields) {
        const raw = answersDraft[field.key] ?? "";
        // so envia campos que o usuario efetivamente preencheu, ou que ja
        // tinham valor antes (para permitir limpar um campo de fato)
        if (raw === "" && (rda!.answers[field.key] === undefined || rda!.answers[field.key] === null)) {
          continue;
        }
        changed[field.key] = parseAnswerValue(field, raw);
      }
      await api.patch(`/rdas/${id}/answers`, { answers: changed, comment: comment || undefined });
      setComment("");
      await loadAll();
    } catch (err) {
      const detail = (err as { detail?: unknown }).detail;
      setError(Array.isArray(detail) ? detail.join("; ") : "Não foi possível salvar as respostas");
    }
  }

  async function handleSubmit() {
    setError(null);
    try {
      await api.post(`/rdas/${id}/submit`);
      await loadAll();
    } catch (err) {
      const detail = (err as { detail?: unknown }).detail;
      setError(Array.isArray(detail) ? detail.join("; ") : "Não foi possível enviar o RDA");
    }
  }

  async function handleStartReview() {
    await api.post(`/rdas/${id}/start-review`);
    await loadAll();
  }

  async function handleApprove() {
    setError(null);
    try {
      await api.post(`/rdas/${id}/approve`, { comment: comment || undefined });
      setComment("");
      await loadAll();
    } catch {
      setError("Não foi possível aprovar");
    }
  }

  async function handleReject() {
    setError(null);
    if (!rejectReason.trim()) {
      setError("Informe o motivo da reprovação");
      return;
    }
    try {
      await api.post(`/rdas/${id}/reject`, { reason: rejectReason });
      setRejectReason("");
      await loadAll();
    } catch {
      setError("Não foi possível reprovar");
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>
          RDA <span className={`badge ${rda.status}`}>{rda.status}</span>
        </h1>
        <Link to="/rdas" className="muted">
          ← voltar
        </Link>
      </div>

      <div className="card">
        <h2>Respostas</h2>
        <div className="form-grid">
          {version.fields
            .filter((f) => !canEdit || isFieldActive(f, answersDraft))
            .map((field) => (
              <label key={field.key}>
                {field.label}
                {field.required && " *"}
                {canEdit ? (
                  <AnswerInput
                    field={field}
                    value={answersDraft[field.key] ?? ""}
                    onChange={(v) => setAnswersDraft((prev) => ({ ...prev, [field.key]: v }))}
                  />
                ) : (
                  <p>{formatAnswer(rda.answers[field.key])}</p>
                )}
              </label>
            ))}
        </div>
        {canEdit && (
          <div className="form-grid" style={{ marginTop: 12 }}>
            <label>
              Comentário da edição (opcional)
              <input value={comment} onChange={(e) => setComment(e.target.value)} />
            </label>
            <div className="form-row">
              <button onClick={saveAnswers}>Salvar respostas</button>
              {canSubmit && <button onClick={handleSubmit}>Enviar RDA</button>}
            </div>
          </div>
        )}
        {error && <p className="error">{error}</p>}
      </div>

      {canReview && (
        <div className="card">
          <h2>Revisão</h2>
          <div className="form-row">
            {canStartReview && <button onClick={handleStartReview}>Iniciar revisão</button>}
            <button onClick={handleApprove}>Aprovar</button>
          </div>
          <div className="form-row" style={{ marginTop: 12 }}>
            <label>
              Motivo da reprovação
              <input value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} />
            </label>
            <button className="danger" onClick={handleReject}>
              Reprovar
            </button>
          </div>
        </div>
      )}

      {rda.original_answers && (
        <div className="card">
          <h2>Dado original coletado em campo</h2>
          <table>
            <tbody>
              {Object.entries(rda.original_answers).map(([key, value]) => (
                <tr key={key}>
                  <td>{version.fields.find((f) => f.key === key)?.label ?? key}</td>
                  <td>{formatAnswer(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="card">
        <h2>Trilha de auditoria</h2>
        {auditLog.map((entry) => (
          <div key={entry.id} className="audit-entry">
            <strong>{entry.action}</strong>{" "}
            <span className="muted">{new Date(entry.created_at).toLocaleString("pt-BR")}</span>
            {entry.comment && <p>{entry.comment}</p>}
            {entry.field_changes && (
              <ul>
                {entry.field_changes.map((c) => (
                  <li key={c.field}>
                    <strong>{c.field}</strong>: {formatAnswer(c.old_value)} →{" "}
                    {formatAnswer(c.new_value)}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function AnswerInput({
  field,
  value,
  onChange,
}: {
  field: FieldDefinition;
  value: string;
  onChange: (v: string) => void;
}) {
  if (field.type === "selecao_unica") {
    return (
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Selecione...</option>
        {(field.options ?? []).map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    );
  }
  if (field.type === "numero") {
    return <input type="number" value={value} onChange={(e) => onChange(e.target.value)} />;
  }
  if (field.type === "data_hora") {
    return <input type="datetime-local" value={value} onChange={(e) => onChange(e.target.value)} />;
  }
  return <input value={value} onChange={(e) => onChange(e.target.value)} />;
}

function formatAnswer(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function stringifyAnswers(
  answers: Record<string, unknown>,
  fields: FieldDefinition[],
): Record<string, string> {
  const result: Record<string, string> = {};
  for (const field of fields) {
    const value = answers[field.key];
    result[field.key] = Array.isArray(value) ? value.join(", ") : value != null ? String(value) : "";
  }
  return result;
}
