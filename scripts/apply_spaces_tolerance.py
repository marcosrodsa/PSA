"""
Atualiza o nó Code do workflow oficial para tolerar espaços intercalados (ex: 'A JUDA', 'a j u d a').
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
WF_ID    = 'jz570cBqWph2CrXs'

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

print(f'[1/3] Obtendo workflow {WF_ID}...')
status, data = n8n('GET', f'/workflows/{WF_ID}')
if status != 200:
    print(f'ERRO {status}: {data}')
    sys.exit(1)

NEW_JS_CODE = (
    "// BÔNUS: Nó Code em JavaScript (Engenharia Defensiva)\n\n"
    "// 1. Extração segura do body com fallback\n"
    "const payload = $input.first().json.body || $input.first().json;\n\n"
    "// 2. Identificador do usuário\n"
    "const usuario = (payload.from || 'desconhecido').toString().trim();\n\n"
    "// 3. Normalização NLP do texto:\n"
    "//    - toString() seguro contra nulos\n"
    "//    - normalize('NFD') decompõe acentos (ex: ajudá -> ajuda)\n"
    "//    - replace unicode diacríticos\n"
    "//    - toLowerCase() padroniza para minúsculas\n"
    "//    - trim() remove espaços nas pontas\n"
    "const rawMensagem = (payload.mensagem || '').toString().trim();\n"
    "let texto = rawMensagem\n"
    "  .normalize('NFD')\n"
    "  .replace(/[\\u0300-\\u036f]/g, '')\n"
    "  .toLowerCase();\n\n"
    "// 4. Tolerância a espaços intercalados (ex: 'A JUDA', 'a j u d a')\n"
    "const textoSemEspacos = texto.replace(/\\s+/g, '');\n"
    "if (textoSemEspacos.includes('ajuda') && !texto.includes('ajuda')) {\n"
    "  texto = texto + ' ajuda';\n"
    "}\n\n"
    "return [{ json: { usuario, texto, rawMensagem } }];"
)

for node in data['nodes']:
    if node.get('name') == 'Code - Extrair e Normalizar':
        node['parameters']['jsCode'] = NEW_JS_CODE
        print('  Nó atualizado com sucesso no JSON local.')
        break

payload_put = {
    'name': data['name'],
    'nodes': data['nodes'],
    'connections': data['connections'],
    'settings': {'executionOrder': data.get('settings', {}).get('executionOrder', 'v1')}
}

print(f'[2/3] Enviando atualização PUT para o n8n...')
status, resp = n8n('PUT', f'/workflows/{WF_ID}', payload_put)
if status != 200:
    print(f'ERRO {status}: {resp}')
    sys.exit(1)

print(f'[3/3] Reativando workflow...')
n8n('POST', f'/workflows/{WF_ID}/activate')
print('OK! Workflow atualizado.')
