import urllib.request, urllib.error, json

tests = [
    {"from": "5511999990000", "mensagem": "Minha encomenda nao chegou, preciso de ajuda urgente!"},
    {"from": "5511888880000", "mensagem": "Quero saber o preco dos planos e fazer um orcamento"},
    {"from": "5511777770000", "mensagem": "Quero cancelar meu contrato e ter meu dinheiro de volta"},
    {"from": "",              "mensagem": ""},
]

for t in tests:
    data = json.dumps(t).encode("utf-8")
    req = urllib.request.Request(
        "https://n8n.ulbrads.site/webhook/triagem-mensagem-enterprise",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode("utf-8"))
            m = body.get("metadata", {})
            fr = str(t["from"])[:15].ljust(15)
            intent = str(m.get("intencao", body.get("codigo", "?"))).ljust(22)
            print(f"from={fr} HTTP {r.status}  {intent}  conf={m.get('confianca', '-')}  motor={m.get('motor', '-')}")
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        fr = str(t["from"])[:15].ljust(15)
        print(f"from={fr} HTTP {e.code}   {body.get('codigo', 'ERR')}")
    except Exception as e:
        print(f"  Erro: {e}")
