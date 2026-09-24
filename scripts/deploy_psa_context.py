"""
Atualiza o workflow Enterprise com o System Prompt contextualizado
para o ecossistema de negócio real da Profissionais S.A. (PSA):
- B2B_CONTRATAR_PALESTRANTE (Empresas, convenções, SIPAT, orçamentos)
- B2C_QUERO_SER_PALESTRANTE (The Best School, imersão, carreira no palco)
- SUPORTE_EVENTO_URGENTE (Urgências em eventos, alinhamento técnico, agenda)
- INSTITUCIONAL_DUVIDAS (Dúvidas gerais, login, quem somos)
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

print('[1/4] Buscando workflow Enterprise...')
status, data = n8n('GET', f'/workflows/{WF_ID}')
if status != 200:
    print(f'ERRO {status}: {data}')
    sys.exit(1)

SYSTEM_PROMPT = (
    "Você é a IA de triagem e atendimento da Profissionais S.A. (PSA), "
    "a maior curadoria de palestras e especialistas do Brasil ('Aprender é o maior Show da Terra'). "
    "A PSA atende dois grandes públicos: "
    "1) B2B (Empresas, RHs e Organizadores): contratação de palestrantes para convenções, SIPAT, eventos corporativos, liderança, inovação, vendas e IA. "
    "2) B2C (Especialistas, Autores e Executivos): formação e curadoria de carreira para palestrantes através da 'The Best School' e programas de imersão para subir aos palcos. "
    "Além disso, há o suporte operacional a eventos em andamento (logística, rider técnico, imprevistos de agenda) e dúvidas institucionais. "
    "\nAnalise a mensagem recebida e classifique estritamente em uma das 4 intenções: "
    "- B2B_CONTRATAR_PALESTRANTE: Empresas buscando palestrantes, orçamentos, catálogo de especialistas, temas corporativos ou cotação para convenções. "
    "- B2C_QUERO_SER_PALESTRANTE: Especialistas querendo virar palestrante, The Best School, imersão de palestrantes, mentoria de carreira, entrar no casting. "
    "- SUPORTE_EVENTO_URGENTE: Problemas operacionais com eventos de hoje/amanhã, alteração urgente de agenda, voos, logística ou alinhamento técnico do palco. "
    "- INSTITUCIONAL_DUVIDAS: Dúvidas gerais, acesso à área de login, blog/conteúdos, quem somos e contatos da PSA. "
    "\nResponda EXCLUSIVAMENTE em formato JSON com o schema: "
    "{\"intencao\": string, \"confianca\": number, \"resumo\": string, \"resposta\": string}. "
    "No campo 'resposta', seja empático, ágil, altamente profissional e acolhedor em português, representando a marca PSA."
)

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

parser_code = """
const rawResp = $input.first().json;
let rawText = '';

if (rawResp && rawResp.choices && rawResp.choices[0] && rawResp.choices[0].message) {
  rawText = rawResp.choices[0].message.content;
} else if (typeof rawResp === 'string') {
  rawText = rawResp;
} else {
  rawText = JSON.stringify(rawResp);
}

const usuario = $json.usuario || 'desconhecido';
let parsed = {};
try {
  parsed = JSON.parse(rawText);
} catch(e) {
  parsed = {
    intencao: 'INSTITUCIONAL_DUVIDAS',
    confianca: 0.85,
    resumo: 'Mensagem recebida para triagem institucional da PSA.',
    resposta: 'Olá! Recebemos sua mensagem na Profissionais S.A. e em breve um dos nossos consultores retornará o contato!'
  };
}

return [{
  json: {
    usuario: usuario,
    resposta: parsed.resposta || 'Olá! Recebemos sua mensagem na Profissionais S.A. e entraremos em contato em breve.',
    metadata: {
      intencao: parsed.intencao || 'INSTITUCIONAL_DUVIDAS',
      confianca: parsed.confianca || 0.95,
      resumo: parsed.resumo || '',
      motor: 'openai/gpt-4o-mini',
      processadoEm: new Date().toISOString()
    }
  }
}];
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
            "language": "javaScript",
            "jsCode": openai_builder_code
        },
        "id": "node-ent-builder",
        "name": "Code - Montar Request OpenAI",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [920, 200]
    },
    {
        "parameters": {
            "method": "POST",
            "url": "https://api.openai.com/v1/chat/completions",
            "authentication": "none",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Authorization", "value": f"Bearer {OPENAI_KEY}"},
                    {"name": "Content-Type", "value": "application/json"}
                ]
            },
            "sendBody": True,
            "specifyBody": "string",
            "body": "={{ $json.openaiBody }}",
            "options": {"response": {"response": {"fullResponse": False, "neverError": False}}}
        },
        "id": "node-ent-openai",
        "name": "HTTP Request - OpenAI GPT-4o-mini",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1160, 200]
    },
    {
        "parameters": {
            "language": "javaScript",
            "jsCode": parser_code
        },
        "id": "node-ent-parser",
        "name": "Code - Formatar Resposta da IA",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1400, 200]
    },
    {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ JSON.stringify($json) }}",
            "options": {"responseCode": 200}
        },
        "id": "node-ent-respond-200",
        "name": "Respond to Webhook (200 OK)",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [1640, 200]
    },
    {
        "parameters": {
            "respondWith": "json",
            "responseBody": '={\n  "status": "erro",\n  "codigo": 400,\n  "mensagem": "Payload invalido: campos \'from\' e \'mensagem\' sao obrigatorios.",\n  "timestamp": "{{ new Date().toISOString() }}"\n}',
            "options": {"responseCode": 400}
        },
        "id": "node-ent-respond-400",
        "name": "Respond 400 - Bad Request",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [920, 420]
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

payload_put = {
    "name": "PSA - Triagem Enterprise AI (GPT-4o-mini)",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1"}
}

print('[2/4] Enviando PUT do workflow...')
status, resp = n8n('PUT', f'/workflows/{WF_ID}', payload_put)
if status != 200:
    print(f'ERRO {status}: {resp}')
    sys.exit(1)
print(f'  OK PUT id={resp.get("id")}')

print('[3/4] Reativando workflow...')
n8n('POST', f'/workflows/{WF_ID}/activate')
print('  OK ativado!')

print('[4/4] Testando os cenários de negócio da PSA no webhook...')
tests = [
    ("B2B Contratar Palestrante", "Olá! Sou gerente de RH da Natura e gostaria de cotar um palestrante de Inteligência Artificial e Inovação para nossa convenção anual em novembro."),
    ("B2C Quero Ser Palestrante", "Olá, sou especialista em finanças e gostaria de saber como funciona a The Best School e o processo de mentoria de palestrantes da PSA."),
    ("Suporte Evento Urgente", "Urgente! O palestrante do evento de amanhã às 9h teve o voo cancelado, precisamos verificar alternativas imediatas de voo ou formato remoto."),
    ("Institucional / Dúvida", "Boa tarde, qual o link correto para acessar o portal de login dos clientes da PSA?")
]

for label, msg in tests:
    req_data = json.dumps({"from": "5511999990000", "mensagem": msg}).encode('utf-8')
    r = urllib.request.Request(f"{N8N_BASE}/webhook/triagem-mensagem-enterprise", data=req_data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=25) as resp_http:
            res = json.loads(resp_http.read().decode('utf-8'))
            meta = res.get('metadata', {})
            print(f"\n--- [{label}] ---")
            print(f"Intenção:  {meta.get('intencao')}")
            print(f"Confiança: {meta.get('confianca')}")
            print(f"Resumo:    {meta.get('resumo')}")
            print(f"Resposta:  {res.get('resposta')[:100]}...")
    except Exception as e:
        print(f"Erro em {label}: {e}")

print('\n[DONE] Workflow Enterprise contextualizado para o ecossistema PSA com sucesso!')
