const fs = require('fs');
const https = require('https');

// Ler .env manualmente
const env = Object.fromEntries(
  fs.readFileSync('.env', 'utf8')
    .split('\n')
    .filter(l => l.trim() && !l.startsWith('#'))
    .map(l => l.split('=').map(s => s.trim()))
);

const BASE_URL = env.N8N_BASE_URL.replace(/\/$/, '');
const API_KEY  = env.N8N_API_KEY;

const workflow = {
  name: "PSA - Triagem de Mensagens WhatsApp",
  nodes: [
    {
      parameters: { httpMethod: "POST", path: "triagem-mensagem", responseMode: "responseNode", options: {} },
      id: "node-webhook",
      name: "Webhook - Receber Mensagem",
      type: "n8n-nodes-base.webhook",
      typeVersion: 2,
      position: [240, 300],
      webhookId: "psa-triagem-webhook-001"
    },
    {
      parameters: {
        language: "javaScript",
        jsCode: `// BÔNUS: Nó Code em JavaScript
// Extrai os campos do payload e normaliza o texto para minúsculas
const payload = $input.first().json.body || $input.first().json;

const usuario = payload.from;
const texto = payload.mensagem.toLowerCase();

return [{ json: { usuario, texto } }];`
      },
      id: "node-code",
      name: "Code - Extrair e Normalizar",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [460, 300]
    },
    {
      parameters: {
        conditions: {
          options: { caseSensitive: false, typeValidation: "strict" },
          conditions: [
            {
              id: "cond-ajuda",
              leftValue: "={{ $json.texto }}",
              rightValue: "ajuda",
              operator: { type: "string", operation: "contains" }
            }
          ],
          combinator: "and"
        },
        options: {}
      },
      id: "node-if",
      name: "IF - Contem ajuda?",
      type: "n8n-nodes-base.if",
      typeVersion: 2,
      position: [680, 300]
    },
    {
      parameters: {
        assignments: {
          assignments: [
            { id: "a1", name: "usuario", value: "={{ $('Code - Extrair e Normalizar').first().json.usuario }}", type: "string" },
            { id: "a2", name: "resposta", value: "Olá! Vou te ajudar agora mesmo.", type: "string" }
          ]
        },
        options: {}
      },
      id: "node-set-ajuda",
      name: "Set - Resposta Ajuda",
      type: "n8n-nodes-base.set",
      typeVersion: 3.4,
      position: [900, 160]
    },
    {
      parameters: {
        assignments: {
          assignments: [
            { id: "b1", name: "usuario", value: "={{ $('Code - Extrair e Normalizar').first().json.usuario }}", type: "string" },
            { id: "b2", name: "resposta", value: "Mensagem recebida. Em breve retornaremos.", type: "string" }
          ]
        },
        options: {}
      },
      id: "node-set-padrao",
      name: "Set - Resposta Padrao",
      type: "n8n-nodes-base.set",
      typeVersion: 3.4,
      position: [900, 440]
    },
    {
      parameters: { mode: "append", options: {} },
      id: "node-merge",
      name: "Merge - Unificar",
      type: "n8n-nodes-base.merge",
      typeVersion: 3,
      position: [1120, 300]
    },
    {
      parameters: {
        respondWith: "json",
        responseBody: "={{ JSON.stringify({ usuario: $json.usuario, resposta: $json.resposta }) }}",
        options: { responseCode: 200 }
      },
      id: "node-respond",
      name: "Respond to Webhook",
      type: "n8n-nodes-base.respondToWebhook",
      typeVersion: 1.1,
      position: [1340, 300]
    }
  ],
  connections: {
    "Webhook - Receber Mensagem": {
      main: [[{ node: "Code - Extrair e Normalizar", type: "main", index: 0 }]]
    },
    "Code - Extrair e Normalizar": {
      main: [[{ node: "IF - Contem ajuda?", type: "main", index: 0 }]]
    },
    "IF - Contem ajuda?": {
      main: [
        [{ node: "Set - Resposta Ajuda", type: "main", index: 0 }],
        [{ node: "Set - Resposta Padrao", type: "main", index: 0 }]
      ]
    },
    "Set - Resposta Ajuda": {
      main: [[{ node: "Merge - Unificar", type: "main", index: 0 }]]
    },
    "Set - Resposta Padrao": {
      main: [[{ node: "Merge - Unificar", type: "main", index: 1 }]]
    },
    "Merge - Unificar": {
      main: [[{ node: "Respond to Webhook", type: "main", index: 0 }]]
    }
  },
  settings: { executionOrder: "v1" }
};

const body = JSON.stringify(workflow);
const url = new URL(`${BASE_URL}/api/v1/workflows`);

const options = {
  hostname: url.hostname,
  port: url.port || 443,
  path: url.pathname,
  method: 'POST',
  headers: {
    'X-N8N-API-KEY': API_KEY,
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body)
  }
};

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const result = JSON.parse(data);
    if (result.id) {
      console.log('✅ Workflow criado com sucesso!');
      console.log(`ID: ${result.id}`);
      console.log(`Nome: ${result.name}`);
      console.log(`Webhook URL: ${BASE_URL}/webhook/triagem-mensagem`);
      // Salvar ID no .env
      let envContent = fs.readFileSync('.env', 'utf8');
      envContent = envContent.replace(/N8N_WORKFLOW_ID=.*/, `N8N_WORKFLOW_ID=${result.id}`);
      fs.writeFileSync('.env', envContent);
      console.log('✅ ID salvo no .env!');
    } else {
      console.error('❌ Erro:', JSON.stringify(result, null, 2));
    }
  });
});

req.on('error', e => console.error('❌ Erro de conexão:', e.message));
req.write(body);
req.end();
