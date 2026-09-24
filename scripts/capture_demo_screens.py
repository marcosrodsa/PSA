from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1180, 'height': 820})
    file_path = os.path.abspath('demo.html')
    page.goto(f'file:///{file_path}')
    page.wait_for_timeout(1000)
    
    # 1. Modo Oficial: enviar mensagem de teste
    page.fill('#messageInput', 'Olá, preciso de ajuda com meu pedido!')
    page.click('#btnSend')
    page.wait_for_timeout(2000)
    page.screenshot(path='screenshots/simulador_demo_oficial.jpg', quality=95)
    print('Oficial screenshot OK')
    
    # 2. Modo Enterprise: alternar e enviar mensagem de suporte urgente
    page.click('#cardEnterprise')
    page.wait_for_timeout(1000)
    page.fill('#messageInput', 'Meu produto chegou danificado, preciso de troca urgente!')
    page.click('#btnSend')
    page.wait_for_timeout(5000) # esperar resposta OpenAI GPT-4o-mini
    page.screenshot(path='screenshots/simulador_demo_enterprise.jpg', quality=95)
    print('Enterprise screenshot OK')
    
    browser.close()

print('Todas as capturas geradas com sucesso!')
