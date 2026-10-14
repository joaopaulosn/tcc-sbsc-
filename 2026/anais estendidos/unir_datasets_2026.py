import pandas as pd

# 1. Arquivos de entrada
file1 = 'sbsc_dataset_genero_completo2026_estendido_atualizado.csv'
file2 = 'sbsc_dataset_genero_completo2026_atualizado.csv'
output_file = 'sbsc_2026_unificado.csv'

# 2. Carregar os DataFrames
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# 3. Remover espaços dos nomes das colunas
df1.columns = df1.columns.str.strip()
df2.columns = df2.columns.str.strip()

# 4. Concatenar na ordem especificada
df_concat = pd.concat([df2, df1], ignore_index=True)

# Garante que não hajam colunas duplicadas por diferença de espaço prévia
df_concat = df_concat.loc[:, ~df_concat.columns.duplicated(keep='first')]

# 5. Criar a coluna 'Ano_Publicacao' preenchida com 2026
df_concat['Ano_Publicacao'] = 2026

# 6. Reorganizar a posição da coluna 'Ano_Publicacao' para ficar após 'eighth-author-affiliation'
cols = list(df_concat.columns)
if 'eighth-author-affiliation' in cols:
    cols.remove('Ano_Publicacao')
    idx = cols.index('eighth-author-affiliation') + 1
    cols.insert(idx, 'Ano_Publicacao')
    df_concat = df_concat[cols]

# 7. Salvar o resultado final
df_concat.to_csv(output_file, index=False, encoding='utf-8-sig')

print("Processamento concluído com sucesso!")
print(f"Dataset salvo em: {output_file}")
