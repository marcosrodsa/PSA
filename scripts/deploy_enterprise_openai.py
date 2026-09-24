"""
Deploy v2 - Enterprise workflow com nó Code montando o body do OpenAI
para garantir que a mensagem do usuario seja interpolada corretamente.
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

N8N_BASE   = env['N8N_BASE_URL'].rstrip('/')
N8N_KEY    = env['N8N_API_KEY']
OPENAI_KEY = env['OPENAI_API_KEY']
WF_ID      = '6jjc9uYf8xKraadZ'

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

print('[1/4] Buscando workflow...')
status, data = n8n('GET', f'/workflows/{WF_ID}')
if status != 200:
    print(f'ERRO {status}: {data}')
    sys.exit(1)
existing_settings = data.get('settings', {'executionOrder': 'v1'})
print(f'  OK  active={data.get("active")}')

SYSTEM_PROMPT = (
    "Voce e o motor de IA de triagem semantica de WhatsApp da PSA (Profissionais SA). "
    "Analise a mensagem do cliente e classifique com precisao em uma das 4 intencoes: "
    "SUPORTE_URGENTE (problemas, reclamacoes, urgencias, produto danificado, entrega atrasada), "
    "COMERCIAL_VENDAS (interesse em compra, precos, orcamentos, catalogo, planos), "
    "CANCELAMENTO (cancelar contrato, reembolso, estorno, desistir), "
    "DUVIDA_GERAL (outras duvidas e perguntas gerais). "
    "Responda EXCLUSIVAMENTE com JSON: {\"intencao\": string, \"confianca\": number, \"resumo\": string, \"resposta\": string}. "
    "O campo resposta deve ser uma mensagem empatica e profissional em portugues para enviar ao cliente."
)

# O nó Code vai montar o JSON body do OpenAI dinamicamente
openai_builder_code = f"""
const mensagem = $json.mensagemOriginal;
const body = {{
  model: "gpt-4o-mini",
  temperature: 0.2,
  response_format: {{ type: "json_object" }},
  messages: [
    {{
      role: "system",
      content: {json.dumps(SYSTEM_PROMPT)}
    }},
    {{
      role: "user",
      content: mensagem
    }}
  ]
}};
return [{{ json: {{ ...($json), openaiBody: JSON.stringify(body) }} }}];
"""

nodes = [
    {
        "parameters": {
            "httpMethod": "POST",
            "path": "triagem-mensagem-enterprise",
            "responseMode": "responseNode",
            "options": {}
        },
        "id": "node-ent-webhook",
        "name": "Webhook - Ingestao WhatsApp",
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [200, 300],
        "webhookId": "psa-triagem-enterprise-webhook"
    },
    {
        "parameters": {
            "language": "javaScript",
            "jsCode": "const rawInput = $input.first().json.body || $input.first().json || {};\nconst rawFrom = rawInput.from;\nconst rawMensagem = rawInput.mensagem;\n\nif (!rawFrom || !rawMensagem || typeof rawMensagem !== 'string' || rawMensagem.trim().length === 0) {\n  return [{ json: { isValid: false, errorCode: 'INVALID_PAYLOAD', errorMessage: \"Os campos 'from' e 'mensagem' sao obrigatorios.\", received: rawInput } }];\n}\n\nconst usuario = String(rawFrom).replace(/\\D/g, '') || String(rawFrom).trim();\n\nreturn [{ json: { isValid: true, usuario, mensagemOriginal: rawMensagem.trim(), receivedAt: new Date().toISOString() } }];"
        },
        "id": "node-ent-validator",
        "name": "Code - Validacao Defensiva",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [440, 300]
    },
    {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "typeValidation": "strict"},
                "conditions": [{"id": "c1", "leftValue": "={{ $json.isValid }}", "rightValue": True, "operator": {"type": "boolean", "operation": "true"}}],
                "combinator": "and"
            },
            "options": {}
        },
        "id": "node-ent-if",
        "name": "IF - Payload Valido?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2,
        "position": [680, 300]
    },
    {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ JSON.stringify({ status: 'error', codigo: $json.errorCode, mensagem: $json.errorMessage, payloadRecebido: $json.received }) }}",
            "options": {"responseCode": 400}
        },
        "id": "node-ent-400",
        "name": "Respond 400 - Bad Request",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [940, 480]
    },
    # Nó que monta o body do OpenAI dinamicamente com a mensagem real
    {
        "parameters": {
            "language": "javaScript",
            "jsCode": openai_builder_code
        },
        "id": "node-ent-builder",
        "name": "Code - Montar Request OpenAI",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [940, 160]
    },
    # HTTP Request ao OpenAI usando o body montado pelo nó anterior
    {
        "parameters": {
            "method": "POST",
            "url": "https://api.openai.com/v1/chat/completions",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Authorization", "value": f"Bearer {OPENAI_KEY}"},
                    {"name": "Content-Type",  "value": "application/json"}
                ]
            },
            "sendBody": True,
            "contentType": "raw",
            "rawContentType": "application/json",
            "body": "={{ $json.openaiBody }}",
            "options": {}
        },
        "id": "node-ent-openai",
        "name": "HTTP Request - OpenAI GPT-4o-mini",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1180, 160]
    },
    {
        "parameters": {
            "language": "javaScript",
            "jsCode": "const httpResp = $input.first().json;\nlet aiResult = {};\ntry {\n  const raw = httpResp.choices[0].message.content;\n  aiResult = JSON.parse(raw);\n} catch(e) {\n  aiResult = { intencao: 'DUVIDA_GERAL', confianca: 0.5, resumo: 'Falha ao parsear IA', resposta: 'Mensagem recebida. Em breve entraremos em contato.' };\n}\n\nconst validado = $('Code - Validacao Defensiva').first().json;\n\nreturn [{ json: { usuario: validado.usuario, mensagemOriginal: validado.mensagemOriginal, resposta: aiResult.resposta, intencao: aiResult.intencao, confianca: aiResult.confianca, resumo: aiResult.resumo, motor: 'openai/gpt-4o-mini', receivedAt: validado.receivedAt, processedAt: new Date().toISOString() } }];"
        },
        "id": "node-ent-formatter",
        "name": "Code - Formatar Resposta da IA",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1440, 160]
    },
    {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ JSON.stringify({ status: 'success', usuario: $json.usuario, resposta: $json.resposta, metadata: { intencao: $json.intencao, confianca: $json.confianca, resumo: $json.resumo, motor: $json.motor, processadoEm: $json.processedAt } }) }}",
            "options": {"responseCode": 200}
        },
        "id": "node-ent-200",
        "name": "Respond to Webhook (200 OK)",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [1700, 160]
    }
]

connections = {
    "Webhook - Ingestao WhatsApp": {
        "main": [[{"node": "Code - Validacao Defensiva", "type": "main", "index": 0}]]
    },
    "Code - Validacao Defensiva": {
        "main": [[{"node": "IF - Payload Valido?", "type": "main", "index": 0}]]
    },
    "IF - Payload Valido?": {
        "main": [
            [{"node": "Code - Montar Request OpenAI", "type": "main", "index": 0}],
            [{"node": "Respond 400 - Bad Request", "type": "main", "index": 0}]
        ]
    },
    "Code - Montar Request OpenAI": {
        "main": [[{"node": "HTTP Request - OpenAI GPT-4o-mini", "type": "main", "index": 0}]]
    },
    "HTTP Request - OpenAI GPT-4o-mini": {
        "main": [[{"node": "Code - Formatar Resposta da IA", "type": "main", "index": 0}]]
    },
    "Code - Formatar Resposta da IA": {
        "main": [[{"node": "Respond to Webhook (200 OK)", "type": "main", "index": 0}]]
    }
}

payload = {
    "name": "PSA - Triagem Enterprise AI (GPT-4o-mini)",
    "nodes": nodes,
    "connections": connections,
    "settings": existing_settings
}

print('[2/4] Fazendo PUT do workflow com arquitetura corrigida...')
status, resp = n8n('PUT', f'/workflows/{WF_ID}', payload)
if status != 200:
    err = json.dumps(resp, ensure_ascii=False)[:1000] if isinstance(resp, dict) else resp[:1000]
    print(f'  ERRO {status}: {err}')
    sys.exit(1)
print(f'  OK  id={resp.get("id")}  nome={resp.get("name")}')

print('[3/4] Ativando workflow...')
status, resp = n8n('POST', f'/workflows/{WF_ID}/activate')
if status not in (200, 201):
    print(f'  AVISO {status}: {resp}')
else:
    print(f'  OK  active={resp.get("active")}')

print('[4/4] Testando 4 casos de uso no webhook enterprise...')
tests = [
    {"from": "5511999990000", "mensagem": "Minha encomenda nao chegou, preciso de ajuda urgente!"},
    {"from": "5511888880000", "mensagem": "Quero saber o preco dos planos e fazer um orcamento"},
    {"from": "5511777770000", "mensagem": "Quero cancelar meu contrato e ter meu dinheiro de volta"},
    {"from": "",              "mensagem": ""},
]

for t in tests:
    data = json.dumps(t).encode("utf-8")
    req = urllib.request.Request(
        f'{N8N_BASE}/webhook/triagem-mensagem-enterprise',
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode("utf-8"))
            m = body.get("metadata", {})
            fr = str(t["from"])[:15].ljust(15)
            intent = str(m.get("intencao", "?")).ljust(22)
            print(f"  from={fr} HTTP {r.status}  {intent}  conf={m.get('confianca', '-')}  motor={m.get('motor', '-')}")
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        fr = str(t["from"])[:15].ljust(15)
        print(f"  from={fr} HTTP {e.code}   {body.get('codigo', 'ERR')}")
    except Exception as e:
        print(f"  Erro: {e}")

print('\n[DONE] Deploy v2 completo!')
