import urllib.request
import json
import os

key = None
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip().startswith('OPENAI_API_KEY='):
            key = line.strip().split('=', 1)[1]

print("Key starts with:", key[:12] if key else "None")

req = urllib.request.Request(
    'https://api.openai.com/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    },
    data=json.dumps({
        'model': 'gpt-4o-mini',
        'messages': [
            {
                'role': 'system',
                'content': 'Você é o motor de IA de triagem de WhatsApp da PSA (Profissionais SA). Classifique em: SUPORTE_URGENTE, COMERCIAL_VENDAS, CANCELAMENTO, DUVIDA_GERAL. Retorne JSON: {"intencao": string, "confianca": number, "resumo": string, "resposta": string}'
            },
            {
                'role': 'user',
                'content': 'Meu produto veio danificado e preciso de troca urgente!'
            }
        ],
        'response_format': {'type': 'json_object'}
    }).encode('utf-8')
)

try:
    with urllib.request.urlopen(req) as resp:
        print('Status:', resp.status)
        result = json.loads(resp.read().decode('utf-8'))
        print('Response message content:\n', result['choices'][0]['message']['content'])
except Exception as e:
    print('Error:', e)
