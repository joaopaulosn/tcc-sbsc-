import pandas as pd
import re

def clean_text(text):
    """Remove quebras de linha (\n, \r), tabulações (\t) e múltiplos espaços."""
    if not isinstance(text, str) or pd.isna(text):
        return None
    cleaned = re.sub(r'[\r\n\t]+', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else None

def format_author_name(name):
    """Formata o nome do autor no padrão: nome x. x. sobrenome (em minúsculas)."""
    name = clean_text(name)
    if not name:
        return None
    parts = name.split()
    if len(parts) == 1:
        return parts[0].lower()
    
    first_name = parts[0].lower()
    last_name = parts[-1].lower()
    middle_parts = parts[1:-1]
    
    initials = []
    for p in middle_parts:
        p_clean = p.replace('.', '').strip().lower()
        if p_clean:
            initials.append(f"{p_clean[0]}.")
            
    if initials:
        return f"{first_name} {' '.join(initials)} {last_name}"
    else:
        return f"{first_name} {last_name}"

def format_affiliation(aff):
    """Extrai a sigla da filiação entre parênteses, se presente."""
    aff = clean_text(aff)
    if not aff:
        return None
    match = re.search(r'\(([^)]+)\)', aff)
    if match:
        return match.group(1).strip()
    return aff

def extract_keywords(kw_str):
    """Remove prefixos e divide a string de palavras-chave em uma lista."""
    kw_str = clean_text(kw_str)
    if not kw_str:
        return []
    kw_str = re.sub(r'^Palavras-chave:\s*', '', kw_str, flags=re.IGNORECASE)
    keywords = [k.strip() for k in re.split(r'[,;]', kw_str) if k.strip()]
    return keywords

def processar_dataset(input_file, output_csv, output_excel):
    # Carregar dados brutos extraídos pelo scraper
    df_input = pd.read_csv(input_file)
    
    # Remover linhas referentes aos links dos PDFs
    df_clean_input = df_input.dropna(subset=['title']).copy()
    
    # Agrupar pelo link único de cada artigo
    grouped = df_clean_input.groupby('article_link-href', sort=False)
    
    processed_rows = []
    
    for href, group in grouped:
        first_row = group.iloc[0]
        
        # Limpeza do Resumo (Abstract)
        abstract_val = clean_text(first_row['abstract'])
        if abstract_val:
            abstract_val = re.sub(r'^Resumo\s*', '', abstract_val, flags=re.IGNORECASE).strip()
            
        row_data = {
            'title': clean_text(first_row['title']),
            'category': clean_text(first_row['category']),
            'publish-date': int(first_row['publish-date']) if pd.notnull(first_row['publish-date']) else None,
            'abstract': abstract_val,
        }
        
        # Palavras-chave (da 1ª à 8ª)
        kws = extract_keywords(first_row['keywords'])
        kw_cols = [
            'first-keyword', 'second-keyword', 'third-keyword', 'fourth-keyword', 
            'fifth-keyword', 'sixth-keyword', 'seventh-keyword', 'eighth-keyword'
        ]
        for idx, col in enumerate(kw_cols):
            row_data[col] = kws[idx] if idx < len(kws) else None
            
        row_data['language'] = clean_text(first_row['language'])
        
        # Autores e Filiações (do 1º ao 8º)
        author_ordinal = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth']
        authors = group[['author_name', 'author_affiliation']].dropna(how='all').to_dict(orient='records')
        
        for idx, ord_prefix in enumerate(author_ordinal):
            name_col = f"{ord_prefix}-author-name"
            aff_col = f"{ord_prefix}-author-affiliation"
            if idx < len(authors):
                auth = authors[idx]
                row_data[name_col] = format_author_name(auth.get('author_name'))
                row_data[aff_col] = format_affiliation(auth.get('author_affiliation'))
            else:
                row_data[name_col] = None
                row_data[aff_col] = None
                
        processed_rows.append(row_data)

    df_final = pd.DataFrame(processed_rows)
    
    # Exporta para CSV com enconding utf-8-sig (para acentuação perfeita no Excel/Sheets)
    df_final.to_csv(output_csv, index=False, encoding='utf-8-sig', sep=',')
    df_final.to_excel(output_excel, index=False)
    
    print(f"Processamento concluído com sucesso!")
    print(f"CSV salvo em: {output_csv}")
    print(f"Excel salvo em: {output_excel}")

# Execução do script
if __name__ == '__main__':
    processar_dataset(
        input_file='sbsc_2026_extendidos_completo.csv',
        output_csv='sbsc_2026_extendido_padronizado.csv',
        output_excel='sbsc_2026_extendido_padronizado.xlsx'
    )
