{{- define "ingress.apiService" -}}
{{- printf "%s-api" .Release.Name }}
{{- end }}

{{- define "ingress.frontendService" -}}
{{- printf "%s-frontend" .Release.Name }}
{{- end }}