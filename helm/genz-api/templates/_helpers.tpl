{{- define "genz-api.fullname" -}}
{{- if .Release.Name -}}
{{ printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- else -}}
{{ .Chart.Name }}
{{- end -}}
{{- end -}}