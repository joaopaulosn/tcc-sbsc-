import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re

BASE_URL = "https://sol.sbc.org.br/index.php/sbsc/issue/archive"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def fazer_requisicao_segura(url, max_tentativas=3):
    """Faz uma requisição HTTP tratando erros de conexão e aplicando tentativas."""
    for tentativa in range(1, max_tentativas + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                print("   ⚠️ Limite de requisições atingido. Aguardando 15 segundos...")
                time.sleep(15)
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ Falha na conexão (tentativa {tentativa}/{max_tentativas}): {e}")
            time.sleep(5 * tentativa)
    return None

def obter_links_edicoes():
    print("Obtendo links das edições...")
    response = fazer_requisicao_segura(BASE_URL)
    if not response:
        print("❌ Não foi possível acessar a página de edições.")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links_edicoes = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/issue/view/' in href and href not in links_edicoes:
            links_edicoes.append(href)
                
    print(f"Total de edições encontradas: {len(links_edicoes)}")
    return links_edicoes

def extrair_dados_artigo(url_artigo):
    response = fazer_requisicao_segura(url_artigo)
    if not response:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. Título
    titulo = ""
    titulo_elem = soup.find('h1', class_='page_title') or soup.find('h1', class_='article-title') or soup.find('h1')
    if titulo_elem:
        titulo = titulo_elem.text.strip()

    # 2. Ano de Publicação
    ano = ""
    data_elem = soup.find('div', class_='published') or soup.find('span', class_='date-published')
    if data_elem:
        match_ano = re.search(r'\b(20\d{2}|19\d{2})\b', data_elem.text)
        if match_ano:
            ano = match_ano.group(1)
            
    if not ano:
        meta_date = soup.find('meta', attrs={'name': 'citation_publication_date'}) or soup.find('meta', attrs={'name': 'DC.Date.created'})
        if meta_date and meta_date.get('content'):
            match_ano = re.search(r'\b(20\d{2}|19\d{2})\b', meta_date['content'])
            if match_ano:
                ano = match_ano.group(1)

    # 3. Autores e Filiações
    autores_lista = []
    filiacoes_lista = []

    meta_authors = soup.find_all('meta', attrs={'name': 'citation_author'})
    meta_affils = soup.find_all('meta', attrs={'name': 'citation_author_institution'})

    if meta_authors:
        for m in meta_authors:
            autores_lista.append(m.get('content', '').strip())
        for m in meta_affils:
            filiacoes_lista.append(m.get('content', '').strip())
    else:
        autores_elems = soup.find_all('span', class_='name') or soup.find_all('div', class_='author-name')
        for a in autores_elems:
            autores_lista.append(a.text.strip())

    # 4. Resumo
    resumo = ""
    resumo_elem = soup.find('section', class_='item abstract') or soup.find('div', class_='abstract')
    if resumo_elem:
        resumo = resumo_elem.text.replace('Resumo', '').replace('Abstract', '').strip()

    # 5. Palavras-chave
    palavras_chave = ""
    kw_elem = soup.find('section', class_='item keywords') or soup.find('div', class_='keywords')
    if kw_elem:
        palavras_chave = kw_elem.text.replace('Palavras-chave', '').replace('Keywords', '').replace(':', '').strip()

    return {
        'titulo': titulo,
        'ano': ano,
        'autores': "; ".join(autores_lista),
        'filiacoes': "; ".join(filiacoes_lista),
        'resumo': resumo,
        'palavras_chave': palavras_chave,
        'url': url_artigo
    }

def executar_scraping():
    edicoes = obter_links_edicoes()
    todos_artigos = []

    for idx, edicao_url in enumerate(edicoes, 1):
        print(f"\n[{idx}/{len(edicoes)}] Processando edição: {edicao_url}")
        res = fazer_requisicao_segura(edicao_url)
        if not res:
            continue
            
        soup_edicao = BeautifulSoup(res.text, 'html.parser')
        
        links_artigos = []
        for a in soup_edicao.find_all('a', href=True):
            href = a['href']
            if '/article/view/' in href and '/article/viewFile/' not in href and '/download/' not in href:
                if href not in links_artigos:
                    links_artigos.append(href)

        print(f"   -> Encontrados {len(links_artigos)} artigos nesta edição.")
        
        for art_idx, art_url in enumerate(links_artigos, 1):
            dados = extrair_dados_artigo(art_url)
            if dados and dados['titulo']:
                todos_artigos.append(dados)
            
            # Pausa dinâmica entre 1 e 2.5 segundos para não sobrecarregar o servidor
            time.sleep(random.uniform(1.0, 2.5))

        # Salvamento parcial a cada edição concluída
        if todos_artigos:
            df_temp = pd.DataFrame(todos_artigos)
            df_temp.to_csv("dados_sbsc_brutos.csv", index=False, encoding='utf-8-sig')
            print(f"   💾 Progresso salvo! Total acumulado: {len(todos_artigos)} artigos.")

    print(f"\n✅ Processo finalizado! {len(todos_artigos)} artigos salvos em 'dados_sbsc_brutos.csv'.")

if __name__ == "__main__":
    executar_scraping()