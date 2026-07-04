export type Role = "admin" | "gestor" | "coordenador" | "coletor" | "convidado";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
  organization_id: string;
}

export interface Organization {
  id: string;
  name: string;
}

export interface Contract {
  id: string;
  name: string;
  organization_id: string;
}

export interface Team {
  id: string;
  name: string;
  contract_id: string;
}

export type FieldType =
  | "texto"
  | "numero"
  | "data_hora"
  | "selecao_unica"
  | "selecao_multipla"
  | "foto"
  | "assinatura"
  | "localizacao";

export interface FieldCondition {
  field: string;
  equals: string;
}

export interface FieldDefinition {
  key: string;
  label: string;
  type: FieldType;
  required: boolean;
  order: number;
  options: string[] | null;
  condition: FieldCondition | null;
}

export interface FormTemplate {
  id: string;
  contract_id: string;
  name: string;
  created_at: string;
}

export interface FormTemplateVersion {
  id: string;
  template_id: string;
  version_number: number;
  fields: FieldDefinition[];
  is_published: boolean;
  published_at: string | null;
  created_at: string;
}

export interface FormTemplateWithCurrentVersion extends FormTemplate {
  current_version: FormTemplateVersion | null;
}

export type RdaStatus = "rascunho" | "enviado" | "em_revisao" | "aprovado" | "reprovado";

export interface Rda {
  id: string;
  contract_id: string;
  team_id: string;
  form_template_version_id: string;
  submitted_by_id: string;
  status: RdaStatus;
  original_answers: Record<string, unknown> | null;
  answers: Record<string, unknown>;
  submitted_at: string | null;
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  review_comment: string | null;
  created_at: string;
  updated_at: string;
}

export type RdaAuditAction =
  | "criado"
  | "editado"
  | "enviado"
  | "iniciada_revisao"
  | "aprovado"
  | "reprovado";

export interface FieldChange {
  field: string;
  old_value: unknown;
  new_value: unknown;
}

export interface RdaAuditLog {
  id: string;
  actor_id: string;
  action: RdaAuditAction;
  field_changes: FieldChange[] | null;
  comment: string | null;
  created_at: string;
}
