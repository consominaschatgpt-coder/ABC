"""Modelos HTML padrao (Consominas) usados quando o contrato nao tem um
ReportTemplate proprio cadastrado. Sao templates Jinja2 simples, pensados
para impressao/PDF (ver app/services/report_service.py)."""

BASE_STYLE = """
<style>
  body { font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #222; }
  .header { border-bottom: 3px solid #6d3bff; padding-bottom: 8px; margin-bottom: 16px; }
  .header h1 { color: #6d3bff; font-size: 18px; margin: 0 0 4px; }
  .header .subtitle { color: #666; font-size: 12px; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
  th, td { border: 1px solid #ccc; padding: 4px 8px; text-align: left; vertical-align: top; }
  th { background: #f2f0fa; }
  .meta-table td:first-child { font-weight: bold; width: 160px; background: #fafafa; }
  .rda-block { margin-bottom: 24px; page-break-inside: avoid; }
  .footer { color: #999; font-size: 9px; margin-top: 24px; }
  .badge { display: inline-block; padding: 2px 6px; border-radius: 3px; background: #eee; }
</style>
"""

DEFAULT_SINGLE_TEMPLATE = (
    BASE_STYLE
    + """
<div class="header">
  <h1>{{ organization_name }}</h1>
  <div class="subtitle">Relatorio Diario de Atividades — Contrato {{ contract_name }} / Equipe {{ team_name }}</div>
</div>

<table class="meta-table">
  <tr><td>Status</td><td><span class="badge">{{ status }}</span></td></tr>
  <tr><td>Coletor</td><td>{{ coletor_name }}</td></tr>
  <tr><td>Enviado em</td><td>{{ submitted_at or "-" }}</td></tr>
  <tr><td>Revisado por</td><td>{{ coordenador_name or "-" }}</td></tr>
  <tr><td>Revisado em</td><td>{{ reviewed_at or "-" }}</td></tr>
  {% if review_comment %}<tr><td>Comentario da revisao</td><td>{{ review_comment }}</td></tr>{% endif %}
</table>

<table>
  <tr><th>Campo</th><th>Resposta</th></tr>
  {% for field in fields %}
  <tr><td>{{ field.label }}</td><td>{{ field.value }}</td></tr>
  {% endfor %}
</table>

<div class="footer">Gerado automaticamente em {{ generated_at }} — Sistema de RDA de Campo</div>
"""
)

DEFAULT_CONSOLIDATED_TEMPLATE = (
    BASE_STYLE
    + """
<div class="header">
  <h1>{{ organization_name }}</h1>
  <div class="subtitle">Relatorio consolidado — Contrato {{ contract_name }} — {{ period_label }}</div>
</div>

<table class="meta-table">
  <tr><td>Total de RDAs aprovados</td><td>{{ total_rdas }}</td></tr>
  <tr><td>Periodo</td><td>{{ period_label }}</td></tr>
</table>

{% for rda in rdas %}
<div class="rda-block">
  <h2>Equipe {{ rda.team_name }} — {{ rda.submitted_at or "-" }}</h2>
  <table>
    <tr><th>Campo</th><th>Resposta</th></tr>
    {% for field in rda.fields %}
    <tr><td>{{ field.label }}</td><td>{{ field.value }}</td></tr>
    {% endfor %}
  </table>
</div>
{% endfor %}

<div class="footer">Gerado automaticamente em {{ generated_at }} — Sistema de RDA de Campo</div>
"""
)
