{{- define "database.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "database.fullname" -}}
{{- printf "%s-database" .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "database.labels" -}}
app.kubernetes.io/name: {{ include "database.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}