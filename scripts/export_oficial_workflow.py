"""
Exporta o workflow OFICIAL atualizado e salva no repositório.
"""

import urllib.request, json

env = {}
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v

N8N_BASE = env['N8N_BASE_URL'].rstrip('/')
N8N_KEY  = env['N8N_API_KEY']
WF_ID    = 'jz570cBqWph2CrXs'

req = urllib.request.Request(
    f'{N8N_BASE}/api/v1/workflows/{WF_ID}',
    headers={'X-N8N-API-KEY': N8N_KEY, 'Accept': 'application/json'},
    method='GET'
)

with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())

exported = {
    "name": data["name"],
    "nodes": data["nodes"],
    "connections": data["connections"],
    "settings": data.get("settings", {"executionOrder": "v1"})
}

for f_path in ['workflow_psa_triagem.json', 'workflows/01_workflow_oficial.json']:
    with open(f_path, 'w', encoding='utf-8') as f:
        json.dump(exported, f, ensure_ascii=False, indent=2)
    print(f'Exportado: {f_path}')

print('OK.')
