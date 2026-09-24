"""
Atualiza o Code node do workflow OFICIAL com NFD normalization completa.
Mantém 100% a lógica do enunciado (detecta 'ajuda'), só robustece a normalização.
"""

import urllib.request
import urllib.error
import json
import sys

env = {}
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v

N8N_BASE = env['N8N_BASE_URL'].rstrip('/')
N8N_KEY  = env['N8N_API_KEY']
WF_ID    = 'jz570cBqWph2CrXs'   # workflow oficial

HEADERS = {
    'X-N8N-API-KEY': N8N_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

def n8n(method, path, payload=None):
    url  = f'{N8N_BASE}/api/v1{path}'
    data = json.dumps(payload).encode() if payload else None
    req  = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')

# 1. Buscar workflow atual
print(f'[1/3] Buscando workflow oficial {WF_ID}...')
status, data = n8n('GET', f'/workflows/{WF_ID}')
if status != 200:
    print(f'ERRO {status}: {data}')
    sys.exit(1)
print(f'  OK  nome={data["name"]}  active={data.get("active")}')

# 2. Encontrar o nó Code e atualizar o jsCode com NFD normalization
CODE_NODE_NAME = "Code - Extrair e Normalizar"
NEW_JS_CODE = (
    "// BÔNUS: Nó Code em JavaScript (Engenharia Defensiva)\n\n"
    "// 1. Extração segura do body com fallback\n"
    "const payload = $input.first().json.body || $input.first().json;\n\n"
    "// 2. Identificador do usuário\n"
    "const usuario = (payload.from || 'desconhecido').toString().trim();\n\n"
    "// 3. Normalização NLP completa do texto:\n"
    "//    - toString() seguro contra nulos\n"
    "//    - normalize('NFD') decompõe caracteres acentuados (ã → a + ˜)\n"
    "//    - replace unicode diacríticos (remove os sinais soltos)\n"
    "//    - toLowerCase() padroniza para minúsculas\n"
    "//    - trim() remove espaços nas extremidades\n"
    "const rawMensagem = (payload.mensagem || '').toString().trim();\n"
    "const texto = rawMensagem\n"
    "  .normalize('NFD')\n"
    "  .replace(/[\\u0300-\\u036f]/g, '')\n"
    "  .toLowerCase();\n\n"
    "return [{ json: { usuario, texto, rawMensagem } }];"
)

nodes = data['nodes']
updated = False
for node in nodes:
    if node.get('name') == CODE_NODE_NAME:
        node['parameters']['jsCode'] = NEW_JS_CODE
        updated = True
        print(f'  Nó "{CODE_NODE_NAME}" encontrado e atualizado.')
        break

if not updated:
    # Tentar pelo tipo code
    for node in nodes:
        if node.get('type') == 'n8n-nodes-base.code':
            print(f'  Atualizando nó code: {node["name"]}')
            node['parameters']['jsCode'] = NEW_JS_CODE
            updated = True
            break

if not updated:
    print('  AVISO: nó Code não encontrado. Listando nós:')
    for n in nodes:
        print(f'    - {n["name"]} ({n["type"]})')
    sys.exit(1)

# 3. PUT do workflow atualizado
payload_put = {
    'name': data['name'],
    'nodes': nodes,
    'connections': data['connections'],
    'settings': {'executionOrder': data.get('settings', {}).get('executionOrder', 'v1')}
}

print(f'[2/3] Fazendo PUT do workflow com NFD normalization...')
status, resp = n8n('PUT', f'/workflows/{WF_ID}', payload_put)
if status != 200:
    err = json.dumps(resp, ensure_ascii=False)[:600] if isinstance(resp, dict) else resp[:600]
    print(f'  ERRO {status}: {err}')
    sys.exit(1)
print(f'  OK  id={resp.get("id")}  nome={resp.get("name")}')

# 4. Ativar (garantia)
print(f'[3/3] Ativando workflow...')
status, resp2 = n8n('POST', f'/workflows/{WF_ID}/activate')
print(f'  OK  active={resp2.get("active") if isinstance(resp2, dict) else "?"}')

print('\n[DONE] Workflow oficial atualizado com NFD normalization!')
