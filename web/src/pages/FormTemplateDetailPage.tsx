import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type {
  FieldDefinition,
  FieldType,
  FormTemplateVersion,
  FormTemplateWithCurrentVersion,
} from "../api/types";
import { useAuth } from "../auth/AuthContext";

const FIELD_TYPES: { value: FieldType; label: string }[] = [
  { value: "texto", label: "Texto" },
  { value: "numero", label: "Número" },
  { value: "data_hora", label: "Data/hora" },
  { value: "selecao_unica", label: "Seleção única" },
  { value: "selecao_multipla", label: "Seleção múltipla" },
  { value: "foto", label: "Foto" },
  { value: "assinatura", label: "Assinatura" },
  { value: "localizacao", label: "Localização (GPS)" },
];

const SELECTION_TYPES: FieldType[] = ["selecao_unica", "selecao_multipla"];

interface DraftField {
  key: string;
  label: string;
  type: FieldType;
  required: boolean;
  optionsText: string;
  conditionField: string;
  conditionEquals: string;
}

function emptyDraftField(): DraftField {
  return {
    key: "",
    label: "",
    type: "texto",
    required: false,
    optionsText: "",
    conditionField: "",
    conditionEquals: "",
  };
}

function toFieldDefinition(draft: DraftField): FieldDefinition {
  return {
    key: draft.key.trim(),
    label: draft.label.trim(),
    type: draft.type,
    required: draft.required,
    order: 0,
    options: SELECTION_TYPES.includes(draft.type)
      ? draft.optionsText
          .split(",")
          .map((o) => o.trim())
          .filter(Boolean)
      : null,
    condition: draft.conditionField
      ? { field: draft.conditionField, equals: draft.conditionEquals }
      : null,
  };
}

export default function FormTemplateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [template, setTemplate] = useState<FormTemplateWithCurrentVersion | null>(null);
  const [versions, setVersions] = useState<FormTemplateVersion[]>([]);
  const [draftFields, setDraftFields] = useState<DraftField[]>([emptyDraftField()]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const canEdit = user?.role === "admin";

  async function loadAll() {
    const [templateData, versionsData] = await Promise.all([
      api.get<FormTemplateWithCurrentVersion>(`/form-templates/${id}`),
      api.get<FormTemplateVersion[]>(`/form-templates/${id}/versions`),
    ]);
    setTemplate(templateData);
    setVersions(versionsData);
  }

  useEffect(() => {
    loadAll().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function updateDraftField(index: number, patch: Partial<DraftField>) {
    setDraftFields((prev) => prev.map((f, i) => (i === index ? { ...f, ...patch } : f)));
  }

  function addDraftField() {
    setDraftFields((prev) => [...prev, emptyDraftField()]);
  }

  function removeDraftField(index: number) {
    setDraftFields((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleCreateVersion(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const fields = draftFields.map(toFieldDefinition);
      await api.post(`/form-templates/${id}/versions`, { fields });
      setDraftFields([emptyDraftField()]);
      await loadAll();
    } catch (err) {
      const detail = (err as { detail?: unknown }).detail;
      setError(Array.isArray(detail) ? detail.join("; ") : "Não foi possível salvar a versão");
    }
  }

  async function handlePublish(versionId: string) {
    await api.post(`/form-templates/${id}/versions/${versionId}/publish`);
    await loadAll();
  }

  if (loading || !template) return <p>Carregando...</p>;

  return (
    <div>
      <div className="page-header">
        <h1>{template.name}</h1>
        <Link to="/form-templates" className="muted">
          ← voltar
        </Link>
      </div>

      <div className="card">
        <h2>Versão atual publicada</h2>
        {template.current_version ? (
          <FieldList fields={template.current_version.fields} />
        ) : (
          <p className="muted">Nenhuma versão publicada ainda.</p>
        )}
      </div>

      <div className="card">
        <h2>Histórico de versões</h2>
        <table>
          <thead>
            <tr>
              <th>Versão</th>
              <th>Status</th>
              <th>Campos</th>
              {canEdit && <th></th>}
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.id}>
                <td>v{v.version_number}</td>
                <td>{v.is_published ? "Publicada" : "Rascunho"}</td>
                <td>{v.fields.length}</td>
                {canEdit && (
                  <td>
                    {!v.is_published && (
                      <button onClick={() => handlePublish(v.id)}>Publicar</button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {canEdit && (
        <div className="card">
          <h2>Nova versão</h2>
          <form className="form-grid" onSubmit={handleCreateVersion}>
            {draftFields.map((field, index) => (
              <div key={index} className="field-row">
                <div className="form-row">
                  <label>
                    Chave (key)
                    <input
                      value={field.key}
                      onChange={(e) => updateDraftField(index, { key: e.target.value })}
                      placeholder="ex: tipo_supressao"
                      required
                    />
                  </label>
                  <label>
                    Rótulo
                    <input
                      value={field.label}
                      onChange={(e) => updateDraftField(index, { label: e.target.value })}
                      placeholder="ex: Tipo de supressão"
                      required
                    />
                  </label>
                  <label>
                    Tipo
                    <select
                      value={field.type}
                      onChange={(e) =>
                        updateDraftField(index, { type: e.target.value as FieldType })
                      }
                    >
                      {FIELD_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={field.required}
                      onChange={(e) => updateDraftField(index, { required: e.target.checked })}
                    />
                    Obrigatório
                  </label>
                </div>
                {SELECTION_TYPES.includes(field.type) && (
                  <label>
                    Opções (separadas por vírgula)
                    <input
                      value={field.optionsText}
                      onChange={(e) => updateDraftField(index, { optionsText: e.target.value })}
                      placeholder="ex: Fauna, Flora, Biota aquática"
                    />
                  </label>
                )}
                <div className="form-row">
                  <label>
                    Só aparece se o campo (opcional)
                    <input
                      value={field.conditionField}
                      onChange={(e) =>
                        updateDraftField(index, { conditionField: e.target.value })
                      }
                      placeholder="key de outro campo"
                    />
                  </label>
                  <label>
                    for igual a
                    <input
                      value={field.conditionEquals}
                      onChange={(e) =>
                        updateDraftField(index, { conditionEquals: e.target.value })
                      }
                      placeholder="valor"
                    />
                  </label>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => removeDraftField(index)}
                  >
                    Remover campo
                  </button>
                </div>
              </div>
            ))}
            <div className="form-row">
              <button type="button" className="secondary" onClick={addDraftField}>
                + Adicionar campo
              </button>
              <button type="submit">Salvar como nova versão (rascunho)</button>
            </div>
          </form>
          {error && <p className="error">{error}</p>}
        </div>
      )}
    </div>
  );
}

function FieldList({ fields }: { fields: FieldDefinition[] }) {
  if (fields.length === 0) return <p className="muted">Sem campos.</p>;
  return (
    <table>
      <thead>
        <tr>
          <th>Chave</th>
          <th>Rótulo</th>
          <th>Tipo</th>
          <th>Obrigatório</th>
          <th>Condição</th>
        </tr>
      </thead>
      <tbody>
        {fields.map((f) => (
          <tr key={f.key}>
            <td>{f.key}</td>
            <td>{f.label}</td>
            <td>{f.type}</td>
            <td>{f.required ? "Sim" : "Não"}</td>
            <td className="muted">
              {f.condition ? `${f.condition.field} = ${f.condition.equals}` : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
