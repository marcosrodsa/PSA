import urllib.request, urllib.error, json

tests = [
    ("A JUDA? (com espaco)",          {"from": "5511111111", "mensagem": "A JUDA?"}),
    ("a j u d a (espaco entre cada)",  {"from": "5511111111", "mensagem": "a j u d a"}),
    ("AJUDA maiusculo normal",        {"from": "5511111111", "mensagem": "Preciso de AJUDA agora"}),
    ("SEM ajuda",                     {"from": "5511222222", "mensagem": "Quero informacoes sobre preco"}),
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
            resp = body.get("resposta", "?")
            print(f"{label:35} -> HTTP {r.status} | {resp}")
    except Exception as e:
        print(f"{label:35} -> Erro: {e}")
