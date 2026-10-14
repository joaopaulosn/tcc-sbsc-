import pandas as pd

# 1. Arquivos de entrada e de saída
file_2026 = 'sbsc_2026_unificado.csv'
file_historico = 'sbsc_dataset_genero_completo.csv'
output_file = 'sbsc_dataset_genero_completo_2006_2026.csv'

# 2. Carregar os datasets
df_2026 = pd.read_csv(file_2026)
df_historico = pd.read_csv(file_historico)

# 3. Remover espaços sobressalentes dos nomes das colunas
df_2026.columns = df_2026.columns.str.strip()
df_historico.columns = df_historico.columns.str.strip()

# 4. Eliminar colunas duplicadas que possam existir devido a espaços prévios (ex: 'eighth-author-name ')
df_2026 = df_2026.loc[:, ~df_2026.columns.duplicated(keep='first')]
df_historico = df_historico.loc[:, ~df_historico.columns.duplicated(keep='first')]

# 5. Concatenar na ordem solicitada (primeiro 2026, depois histórico)
df_consolidado = pd.concat([df_2026, df_historico], ignore_index=True)

# 6. Garantir limpeza de nomes de colunas no DataFrame final
df_consolidado.columns = df_consolidado.columns.str.strip()
df_consolidado = df_consolidado.loc[:, ~df_consolidado.columns.duplicated(keep='first')]

# 7. Salvar o arquivo final
df_consolidado.to_csv(output_file, index=False, encoding='utf-8-sig')

print("--- CONCATENAÇÃO CONCLUÍDA COM SUCESSO ---")
print(f"Total de registros 2026: {len(df_2026)}")
print(f"Total de registros histórico: {len(df_historico)}")
print(f"Total de registros salvos em '{output_file}': {len(df_consolidado)}")
print(f"Total de colunas únicas: {len(df_consolidado.columns)}")
