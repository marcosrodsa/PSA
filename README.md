# PSA — Triagem de Mensagens WhatsApp no n8n

Olá! Este repositório foi desenvolvido para o **Desafio Prático de Analista de IA da PSA (Profissionais SA)**.

Aqui você encontra a solução completa entregue em dois níveis:
1. **O Entregável Oficial**: Atendimento 100% fiel a todos os requisitos do documento do desafio (PDF), utilizando nós nativos do n8n com nó Code defensivo.
2. **O Overdelivery (Enterprise AI)**: Um segundo workflow em produção equipado com **Inteligência Artificial real (OpenAI GPT-4o-mini)** para classificação semântica de intenções, geração de respostas empáticas, validação de schema (400 Bad Request) e metadados de observabilidade.

Ambos os fluxos estão **ativos em produção** e prontos para teste imediato.

---

## 🚀 Como testar em 1 minuto

Você pode testar a solução de três formas diferentes:

### 1. Simulador Web Interativo (Sem instalar nada)
Criamos um simulador visual no estilo WhatsApp Web que permite alternar entre o **Modo Oficial** e o **Modo Enterprise AI** com um clique:
- Abra o arquivo [`demo.html`](./demo.html) direto no seu navegador (basta dar duplo clique), ou
- Acesse via GitHub Pages: [marcosrodsa.github.io/PSA](https://marcosrodsa.github.io/PSA)

![Simulador Interativo](./screenshots/simulador_demo_enterprise.jpg)

---

### 2. Via Linha de Comando (cURL)

**Teste 1 — Fluxo Oficial (Com ajuda):**
```bash
curl -X POST https://n8n.ulbrads.site/webhook/triagem-mensagem \
  -H "Content-Type: application/json" \
  -d '{"from": "5511999990000", "mensagem": "Olá, preciso de ajuda com meu pedido"}'
```
> **Resposta esperada:** `{"usuario":"5511999990000","resposta":"Olá! Vou te ajudar agora mesmo."}`

**Teste 2 — Fluxo Oficial (Sem ajuda):**
```bash
curl -X POST https://n8n.ulbrads.site/webhook/triagem-mensagem \
  -H "Content-Type: application/json" \
  -d '{"from": "5511999990000", "mensagem": "Gostaria de saber os horários de atendimento"}'
```
> **Resposta esperada:** `{"usuario":"5511999990000","resposta":"Mensagem recebida. Em breve retornaremos."}`

**Teste 3 — Fluxo Enterprise AI (OpenAI GPT-4o-mini):**
```bash
curl -X POST https://n8n.ulbrads.site/webhook/triagem-mensagem-enterprise \
  -H "Content-Type: application/json" \
  -d '{"from": "5511999990000", "mensagem": "Meu produto chegou danificado, preciso de troca urgente!"}'
```
> **Resposta da IA:** Classifica a intenção como `SUPORTE_URGENTE`, gera uma resposta empática em tempo real e retorna métricas de confiança e resumo.

---

### 3. Coleção do Postman
Importe o arquivo [`psa_triagem.postman_collection.json`](./psa_triagem.postman_collection.json) no Postman ou Insomnia. Todas as requisições, variáveis e asserções automatizadas de teste já estão configuradas.

---

## 📋 Entregável 1: Fluxo Oficial (Requisitos do PDF)

O enunciado solicita um workflow que receba uma mensagem via Webhook POST, trate o texto com um nó Code em JavaScript, avalie se contém `"ajuda"` em um nó IF e responda via nó de resposta com merge dos caminhos.

### Arquitetura do Fluxo

```mermaid
graph LR
    WH["📥 Webhook<br><b>Receber Mensagem</b>"] --> CODE["⚡ Code JS<br><b>Extrair & Normalizar</b>"]
    CODE --> IF{"🔀 IF<br><b>Contém 'ajuda'?</b>"}
    IF -- "True" --> SET_TRUE["🟢 Set<br><b>Resposta Ajuda</b>"]
    IF -- "False" --> SET_FALSE["⚪ Set<br><b>Resposta Padrão</b>"]
    SET_TRUE --> MERGE["🔗 Merge<br><b>Unificar</b>"]
    SET_FALSE --> MERGE
    MERGE --> RESP["📤 Respond to Webhook<br><b>200 OK</b>"]
```

### Canvas no n8n (Produção)
![Canvas Oficial n8n](./screenshots/workflow_canvas.jpg)

### O Código JavaScript do Nó Code
Implementamos uma normalização com foco em tolerância a falhas e boas práticas de processamento de texto:
1. **Fallback no payload:** Evita quebras caso o body chegue encapsulado ou vazio.
2. **Normalização NFD:** Decompõe e remove acentos diacríticos (ex: `"ajudá"` vira `"ajuda"`).
3. **Conversão para minúsculas:** Trata `"AJUDA"`, `"Ajuda"` e `"ajuda"` de forma uniforme.
4. **Tolerância a espaços intercalados:** Caso o cliente digite com espaço no meio (ex: `"A JUDA?"` ou `"a j u d a"`), o sistema detecta a intenção e garante o match correto.

```javascript
// BÔNUS: Nó Code em JavaScript (Engenharia Defensiva)

// 1. Extração segura do body com fallback
const payload = $input.first().json.body || $input.first().json;

// 2. Identificador do usuário
const usuario = (payload.from || 'desconhecido').toString().trim();

// 3. Normalização NLP do texto
const rawMensagem = (payload.mensagem || '').toString().trim();
let texto = rawMensagem
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLowerCase();

// 4. Tolerância a espaços intercalados (ex: 'A JUDA', 'a j u d a')
const textoSemEspacos = texto.replace(/\s+/g, '');
if (textoSemEspacos.includes('ajuda') && !texto.includes('ajuda')) {
  texto = texto + ' ajuda';
}

return [{ json: { usuario, texto, rawMensagem } }];
```

### Evidências de Teste em Produção

| Cenário de Teste | Print / Evidência |
|:---|:---|
| **Caminho True (Contém "ajuda")** | ![Teste Com Ajuda](./screenshots/teste_com_ajuda.jpg) |
| **Caminho False (Sem "ajuda")** | ![Teste Sem Ajuda](./screenshots/teste_sem_ajuda.jpg) |
| **Painel de Execuções do n8n** | ![Execuções n8n](./screenshots/painel_n8n_execucao.jpg) |
| **Simulador Web (Modo Oficial)** | ![Simulador Oficial](./screenshots/simulador_demo_oficial.jpg) |

O JSON exportado deste fluxo está disponível em:
- [`workflows/01_workflow_oficial.json`](./workflows/01_workflow_oficial.json)
- [`workflow_psa_triagem.json`](./workflow_psa_triagem.json) (cópia raiz)

---

## 🌟 Entregável 2: Overdelivery — Enterprise AI (GPT-4o-mini)

### Por que criamos um segundo fluxo?
Na prática de atendimento ao cliente, buscar apenas a palavra `"ajuda"` é frágil:
- Clientes com problemas urgentes costumam escrever: *"meu produto veio quebrado"*, *"não consigo acessar minha conta"* ou *"socorro, preciso de suporte"*.
- Clientes comerciais perguntam: *"quanto custa a licença corporativa?"* ou *"quero fechar uma proposta"*.
- Clientes insatisfeitos dizem: *"quero estorno do cartão e cancelar agora"*.

Nenhum desses casos contém a palavra literal `"ajuda"`, mas todos precisam de roteamento prioritário.

Por isso, construímos o **PSA - Triagem Enterprise AI**, conectando o n8n diretamente à **OpenAI (GPT-4o-mini)** para inferência semântica em tempo real.

### Arquitetura Enterprise

```mermaid
graph LR
    WH["📥 Webhook Ingestão"] --> VAL["🛡️ Code: Validação Defensiva"]
    VAL --> IF_VAL{"Validação OK?"}
    IF_VAL -- "Inválido" --> R400["⚠️ Respond 400 Bad Request"]
    IF_VAL -- "Válido" --> BUILDER["⚙️ Code: Montar Request LLM"]
    BUILDER --> OPENAI["🧠 HTTP Request: OpenAI GPT-4o-mini"]
    OPENAI --> PARSER["📊 Code: Formatar Metadados"]
    PARSER --> R200["📤 Respond 200 OK"]
```

### Canvas do Workflow Enterprise no n8n
![Canvas Enterprise n8n](./screenshots/workflow_enterprise_canvas.jpg)

### Principais Diferenciais Técnicos:
1. **Validação Defensiva (400 Bad Request):** Se a requisição vier sem o telefone ou com mensagem vazia, o webhook rejeita imediatamente com HTTP 400 e JSON explicativo, protegendo os custos de chamadas de LLM.
2. **Classificação Semântica em 4 Categorias:**
   - `SUPORTE_URGENTE` (reclamações, falhas, defeitos, urgências)
   - `COMERCIAL_VENDAS` (preços, contratações, orçamentos, planos)
   - `CANCELAMENTO` (estorno, encerramento de contrato, devolução)
   - `DUVIDA_GERAL` (dúvidas institucionais, horários, perguntas comuns)
3. **Respostas Empáticas Contextuais:** Em vez de uma frase engessada, a LLM gera uma resposta personalizada para a situação do cliente.
4. **Metadados de IA (Observabilidade):** O webhook retorna a intenção categorizada, grau de confiança da IA (ex: 95%), resumo executivo e modelo utilizado:

```json
{
  "usuario": "5511999990000",
  "resposta": "Lamentamos muito pelo inconveniente com o seu produto. Vamos resolver isso o mais rápido possível...",
  "metadata": {
    "intencao": "SUPORTE_URGENTE",
    "confianca": 0.95,
    "resumo": "Produto chegou danificado e cliente solicita troca urgente.",
    "motor": "openai/gpt-4o-mini"
  }
}
```

O JSON exportado do fluxo Enterprise está disponível em:
- [`workflows/02_workflow_enterprise_ai.json`](./workflows/02_workflow_enterprise_ai.json)

---

## 📁 Estrutura do Repositório

```text
├── README.md                               # Documentação completa do projeto
├── Desafio Prático Analista IA.pdf         # Enunciado original do desafio PSA
├── demo.html / index.html                  # Simulador WhatsApp Web dual-mode
├── workflow_psa_triagem.json               # JSON do fluxo oficial para importação
├── psa_triagem.postman_collection.json     # Coleção do Postman com testes prontos
├── workflows/
│   ├── 01_workflow_oficial.json            # Fluxo oficial (IF + Merge + Set)
│   └── 02_workflow_enterprise_ai.json      # Fluxo avançado (OpenAI GPT-4o-mini)
├── screenshots/                            # Evidências em alta resolução
│   ├── workflow_canvas.jpg                 # Canvas do workflow oficial no n8n
│   ├── workflow_enterprise_canvas.jpg      # Canvas do workflow enterprise no n8n
│   ├── painel_n8n_execucao.jpg             # Histórico de execuções no n8n
│   ├── teste_com_ajuda.jpg                 # Teste no Postman com ajuda (True)
│   ├── teste_sem_ajuda.jpg                 # Teste no Postman sem ajuda (False)
│   ├── simulador_demo_oficial.jpg          # Demonstração do modo oficial no simulador
│   └── simulador_demo_enterprise.jpg       # Demonstração da IA com card de métricas
└── scripts/                                # Utilitários de automação em Python
    ├── test_oficial.py                     # Suíte de testes do webhook oficial
    ├── test_enterprise.py                  # Suíte de testes do webhook enterprise
    ├── export_oficial_workflow.py          # Exportador sincronizado do fluxo oficial
    └── export_enterprise_workflow.py       # Exportador higienizado do fluxo enterprise
```

---

## 🛠️ Como reproduzir na sua própria máquina (Auto-hospedado)

Caso você queira subir sua própria instância do n8n localmente:

1. **Inicie o n8n via Docker:**
   ```bash
   docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n docker.n8n.io/n8nio/n8n
   ```

2. **Acesse a interface:**
   Abra `http://localhost:5678` no seu navegador e crie sua conta de administrador local.

3. **Importe os workflows:**
   - No menu lateral, clique em **Workflows** > **Add Workflow** > menu de três pontos no canto superior direito > **Import from File...**
   - Selecione [`workflows/01_workflow_oficial.json`](./workflows/01_workflow_oficial.json) para o fluxo oficial, ou [`workflows/02_workflow_enterprise_ai.json`](./workflows/02_workflow_enterprise_ai.json) para o fluxo com IA (adicionando sua chave da OpenAI).
   - Ative o workflow no botão **Publish** / **Active**.

---

<div align="center">
  <sub>Projeto desenvolvido com dedicação para o processo seletivo de <b>Analista de IA</b> da <b>PSA (Profissionais SA)</b>.</sub>
</div>
