# PSA — Triagem de Mensagens WhatsApp com n8n

> **Desafio Prático — Analista de IA** · Profissionais SA (PSA)

[![n8n](https://img.shields.io/badge/n8n-workflow-orange)](https://n8n.io)
[![Status](https://img.shields.io/badge/status-ativo%20em%20producao-brightgreen)](https://n8n.ulbrads.site/webhook/triagem-mensagem)

---

## Problema Proposto

O desafio consiste em criar um **workflow no n8n** que simule a triagem básica de mensagens recebidas via WhatsApp — do recebimento até a resposta automática.

> Ver: [Desafio Prático Analista IA.pdf](./Desafio%20Prático%20Analista%20IA.pdf)

### Requisitos
- Receber mensagens via **Webhook** (from, mensagem)
- Extrair e normalizar o texto (minúsculas)
- **Classificar** se a mensagem contém a palavra "ajuda"
- Retornar respostas automáticas diferentes para cada caso
- Entregar JSON do workflow + código JS (bônus) + prints

---

## Solução

### Fluxo do Workflow

`
Webhook → Code JS → IF ("ajuda"?) → Set Ajuda / Set Padrão → Merge → Respond Webhook
`

### Nós do Workflow

| # | Nó | Tipo | Função |
|---|-----|------|--------|
| 1 | Webhook - Receber Mensagem | webhook | Recebe POST com { from, mensagem } |
| 2 | Code - Extrair e Normalizar ⭐ | code | JS: extrai usuario e normaliza texto |
| 3 | IF - Contém ajuda? | if | Verifica se texto contém "ajuda" |
| 4a | Set - Resposta Ajuda | set | Resposta para mensagens de ajuda |
| 4b | Set - Resposta Padrão | set | Resposta padrão |
| 5 | Merge - Unificar | merge | Une os dois caminhos |
| 6 | Respond to Webhook | respondToWebhook | Retorna { usuario, resposta } |

---

## Bônus — Código JavaScript (Nó Code)

`javascript
// Extrai os campos do payload e normaliza o texto para minúsculas
const payload = $input.first().json.body || $input.first().json;
const usuario = payload.from;
const texto = payload.mensagem.toLowerCase();
return [{ json: { usuario, texto } }];
`

---

## Testes

### Endpoint
`
POST https://n8n.ulbrads.site/webhook/triagem-mensagem
Content-Type: application/json
`

### Teste 1 — COM "ajuda"
Request:
`json
{ "from": "5511999990000", "mensagem": "Olá, preciso de AJUDA com meu pedido" }
`
Response:
`json
{ "usuario": "5511999990000", "resposta": "Olá! Vou te ajudar agora mesmo." }
`

### Teste 2 — SEM "ajuda"
Request:
`json
{ "from": "5511888880000", "mensagem": "Oi, quero informações sobre o produto" }
`
Response:
`json
{ "usuario": "5511888880000", "resposta": "Mensagem recebida. Em breve retornaremos." }
`

---

## Screenshots

### 1. Workflow Montado no n8n (Editor)
![Workflow PSA no n8n](./screenshots/workflow_canvas.jpg)

### 2. Execução com Sucesso no Painel do n8n
![Execução no n8n](./screenshots/painel_n8n_execucao.jpg)

### 3. Teste no Postman — Mensagem COM "ajuda"
![Teste 1 - Com Ajuda](./screenshots/teste_com_ajuda.jpg)

### 4. Teste no Postman — Mensagem SEM "ajuda"
![Teste 2 - Sem Ajuda](./screenshots/teste_sem_ajuda.jpg)

---

## Estrutura do Projeto

```
PSA/
├── Desafio Prático Analista IA.pdf   # Problema proposto
├── workflow_psa_triagem.json          # Workflow exportado oficial do n8n
├── deploy_workflow.js                 # Script de automação/deploy via API
├── screenshots/
│   ├── workflow_canvas.jpg            # Print do workflow montado (Canvas)
│   ├── painel_n8n_execucao.jpg        # Print da execução no painel do n8n
│   ├── teste_com_ajuda.jpg            # Print do teste Postman (com ajuda)
│   └── teste_sem_ajuda.jpg           # Print do teste Postman (sem ajuda)
├── .env                               # Credenciais (não versionado)
├── .gitignore
└── README.md
```

---

## Como Importar e Rodar

### 1. Importar no n8n
`
n8n → Menu → Import Workflow → selecionar workflow_psa_triagem.json
`

### 2. Testar via curl
`ash
curl -X POST https://n8n.ulbrads.site/webhook/triagem-mensagem \
  -H "Content-Type: application/json" \
  -d '{"from":"5511999990000","mensagem":"preciso de ajuda"}'
`

---

## Execuções em Produção

| Execução | Status | Horário | Tipo |
|----------|--------|---------|------|
| #50890 | sucesso | 24/09/2026 11:03 | COM ajuda |
| #50891 | sucesso | 24/09/2026 11:03 | SEM ajuda |

---

## Tecnologias

- **n8n** — Plataforma de automação de workflows
- **JavaScript** — Nó Code para transformação de dados
- **Webhook** — Integração via HTTP POST
- **REST API n8n** — Deploy automatizado via script

---

*Desenvolvido para o Desafio Prático Analista IA — PSA · Setembro 2026*
