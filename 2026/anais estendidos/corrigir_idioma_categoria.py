import pandas as pd
import re

# Carrega o dataset enriquecido de gênero e o CSV do scraper
df_genero = pd.read_csv('sbsc_dataset_genero_completo2026_extendido.csv')
df_lingua = pd.read_csv('sbsc_categoria_lingua_extendido.csv')

def get_article_id(url):
    """Extrai o ID único do artigo a partir do link da página."""
    if not isinstance(url, str):
        return None
    match = re.search(r'/article/view/(\d+)', url)
    return match.group(1) if match else None

# Mapeia os IDs dos artigos
df_lingua['article_id'] = df_lingua['article_link-href'].apply(get_article_id)

# Identifica o idioma pela legenda do botão do PDF ("PDF" = Português, "PDF (English)" = Inglês)
pdf_rows = df_lingua[df_lingua['article_link'].str.contains('PDF', na=False)].copy()

def map_language(text):
    if 'English' in str(text):
        return 'Inglês'
    elif 'PDF' in str(text):
        return 'Português'
    return None

pdf_rows['language_mapped'] = pdf_rows['article_link'].apply(map_language)
lang_dict = pdf_rows.set_index('article_id')['language_mapped'].to_dict()

# Relaciona com o título do artigo no dataset principal
article_rows = df_lingua[df_lingua['title'].notnull()].copy()
title_to_id = article_rows.set_index('title')['article_id'].to_dict()

df_genero['article_id'] = df_genero['title'].map(title_to_id)
df_genero['language'] = df_genero['article_id'].map(lang_dict)

# Define 'category' como 'Anais Estendidos' para todas as entradas
df_genero['category'] = 'Anais Estendidos'

# Remove a coluna temporária de controle
df_genero_final = df_genero.drop(columns=['article_id'])

# Salva apenas o arquivo CSV
df_genero_final.to_csv('sbsc_dataset_genero_completo2026_estendido_atualizado.csv', index=False, encoding='utf-8-sig')

print("Processamento concluído com sucesso!")