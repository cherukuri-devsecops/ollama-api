{{/*
Expand the name of the chart.
*/}}
{{- define "ollama-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ollama-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Chart label.
*/}}
{{- define "ollama-api.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "ollama-api.labels" -}}
helm.sh/chart: {{ include "ollama-api.chart" . }}
{{ include "ollama-api.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "ollama-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ollama-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Ollama component name and labels.
*/}}
{{- define "ollama-api.ollama.fullname" -}}
{{- printf "%s-ollama" (include "ollama-api.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "ollama-api.ollama.selectorLabels" -}}
{{ include "ollama-api.selectorLabels" . }}
app.kubernetes.io/component: ollama
{{- end }}

{{/*
Ollama API component name and labels.
*/}}
{{- define "ollama-api.api.fullname" -}}
{{- printf "%s-api" (include "ollama-api.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "ollama-api.api.selectorLabels" -}}
{{ include "ollama-api.selectorLabels" . }}
app.kubernetes.io/component: ollama-api
{{- end }}
