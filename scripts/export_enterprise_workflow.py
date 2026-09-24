"""
Exporta o workflow enterprise do n8n e salva em workflows/02_workflow_enterprise_ai.json
com a chave OpenAI substituida por placeholder para segurança no repositório público.
"""

import urllib.request
import urllib.error
import json
import re
import sys

env = {}
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v

N8N_BASE   = env['N8N_BASE_URL'].rstrip('/')
N8N_KEY    = env['N8N_API_KEY']
OPENAI_KEY = env['OPENAI_API_KEY']
WF_ID      = '6jjc9uYf8xKraadZ'

HEADERS = {
    'X-N8N-API-KEY': N8N_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

req = urllib.request.Request(
    f'{N8N_BASE}/api/v1/workflows/{WF_ID}',
    headers=HEADERS,
    method='GET'
)

with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())

# Campos exportáveis
exported = {
    "name": data["name"],
    "nodes": data["nodes"],
    "connections": data["connections"],
    "settings": data.get("settings", {"executionOrder": "v1"})
}

# Serializar e substituir a chave OpenAI por placeholder
json_str = json.dumps(exported, ensure_ascii=False, indent=2)
json_str = json_str.replace(OPENAI_KEY, "YOUR_OPENAI_API_KEY_HERE")

with open('workflows/02_workflow_enterprise_ai.json', 'w', encoding='utf-8') as f:
    f.write(json_str)

print('Exportado para workflows/02_workflow_enterprise_ai.json')
print('Chave OpenAI substituida por placeholder.')
# Verificar que nao ficou nenhum segredo
if OPENAI_KEY in json_str:
    print('AVISO: Chave OpenAI ainda presente no JSON!')
    sys.exit(1)
else:
    print('OK: Nenhuma chave secreta no arquivo exportado.')
