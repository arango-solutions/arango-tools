{{/* Expand the name of the chart. */}}
{{- define "arango-tools.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Fully qualified app name. */}}
{{- define "arango-tools.fullname" -}}
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

{{- define "arango-tools.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "arango-tools.labels" -}}
helm.sh/chart: {{ include "arango-tools.chart" . }}
{{ include "arango-tools.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "arango-tools.selectorLabels" -}}
app.kubernetes.io/name: {{ include "arango-tools.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* Image reference, defaulting the tag to the chart appVersion. */}}
{{- define "arango-tools.image" -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- printf "%s:%s" .Values.image.repository $tag -}}
{{- end }}

{{/* Name of the secret holding the ArangoDB password. */}}
{{- define "arango-tools.secretName" -}}
{{- if .Values.connection.existingSecret -}}
{{- .Values.connection.existingSecret -}}
{{- else -}}
{{- printf "%s-secret" (include "arango-tools.fullname" .) -}}
{{- end -}}
{{- end }}

{{/* Whether a password is configured (inline or via existing secret). */}}
{{- define "arango-tools.hasPassword" -}}
{{- if or .Values.connection.password .Values.connection.existingSecret -}}
true
{{- end -}}
{{- end }}
