import urllib.request, urllib.error, json

tests = [
    ("COM AJUDA maiusculo",   {"from": "5511111111", "mensagem": "Preciso de AJUDA agora"}),
    ("SEM ajuda",             {"from": "5511222222", "mensagem": "Quero informacoes sobre preco"}),
]

for label, t in tests:
    data = json.dumps(t).encode("utf-8")
    req = urllib.request.Request(
        "https://n8n.ulbrads.site/webhook/triagem-mensagem",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read().decode("utf-8"))
            resp = body.get("resposta", "?")[:80]
            print(f"[{label}]  HTTP {r.status}  -> {resp}")
    except urllib.error.HTTPError as e:
        print(f"[{label}]  HTTP {e.code}")
    except Exception as e:
        print(f"[{label}]  Erro: {e}")
