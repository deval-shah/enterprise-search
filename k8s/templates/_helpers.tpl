{{/*
Create the model list
*/}}
{{- define "ollama.modelList" -}}
{{- $modelList := default list -}}
{{- if .Values.ollama.models -}}
  {{- $modelList = concat $modelList .Values.ollama.models -}}
{{- end -}}
{{- if .Values.ollama.defaultModel -}}
  {{- $modelList = append $modelList .Values.ollama.defaultModel -}}
{{- end -}}
{{- $modelList = $modelList | uniq -}}
{{- print (join " && ollama pull " $modelList) -}}
{{- end -}}

{{/* Generate ollama pull command */}}
{{- define "ollama.pullCommand" -}}
{{- $models := .Values.ollama.models -}}
{{- if gt (len $models) 0 -}}
ollama pull {{ join " && ollama pull " $models }}
{{- end -}}
{{- end -}}
