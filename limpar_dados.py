import re
import pandas as pd

# 1. Carregar os dados brutos
df = pd.read_csv('dadossbsc.csv')

# 2. Filtrar apenas linhas que possuem título do artigo
df_artigos = df.dropna(subset=['titulo', 'autores']).copy()

# Descartar duplicatas de clique, se houver
df_artigos = df_artigos.drop_duplicates(subset=['link_artigo-href'])


# Função para limpar e estruturar autores e filiações
def limpar_autores(texto_autores):
    if pd.isna(texto_autores):
        return '', []

    # Divide por quebras de linha e remove espaços extras
    linhas = [
        linha.strip()
        for linha in str(texto_autores).split('\n')
        if linha.strip()
    ]

    # Como o OJS alterna [Nome, Instituição, Nome, Instituição...], tentamos separar
    autores_lista = []
    for item in linhas:
        # Se não for uma instituição óbvia curta isolada e parecer nome
        autores_lista.append(item)

    # Nomes formatados em string única separada por ponto e vírgula
    autores_str = ' ; '.join(linhas)
    return autores_str


# Função para extrair apenas o ano
def extrair_ano(data_raw):
    if pd.isna(data_raw):
        return ''
    match = re.search(r'\d{2}/\d{2}/(\d{4})', str(data_raw))
    if match:
        return match.group(1)
    # Se não achar data padrão, busca 4 dígitos de ano
    match_ano = re.search(r'(20\d{2})', str(data_raw))
    return match_ano.group(1) if match_ano else ''


# Aplicar limpeza
df_artigos['autores_limpos'] = df_artigos['autores'].apply(limpar_autores)
df_artigos['ano'] = df_artigos['data_publicacao'].apply(extrair_ano)
df_artigos['resumo_limpo'] = (
    df_artigos['resumo']
    .astype(str)
    .str.replace(r'^\s*Resumo\s*', '', regex=True)
    .str.strip()
)
df_artigos['titulo_limpo'] = df_artigos['titulo'].astype(str).str.strip()

# Selecionar e renomear colunas finais
df_final = df_artigos[[
    'ano',
    'titulo_limpo',
    'autores_limpos',
    'resumo_limpo',
    'palavras_chave',
    'link_edicao',
    'link_artigo-href',
]].copy()

df_final.columns = [
    'Ano',
    'Título',
    'Autores_e_Filiacao',
    'Resumo',
    'Palavras_Chave',
    'Edicao',
    'URL',
]

# Salvar a base tratada
df_final.to_csv('sbsc_artigos_limpos.csv', index=False, encoding='utf-8-sig')
print(
    f'Sucesso! {len(df_final)} artigos limpos salvos em "sbsc_artigos_limpos.csv".'
)
