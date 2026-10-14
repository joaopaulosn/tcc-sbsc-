import pandas as pd

# 1. Carregar os dois datasets
df1 = pd.read_csv('sbsc_dataset_enriquecido_ibge_2006_2025.csv')
df2 = pd.read_csv('sbsc_dataset_enriquecido_limpo.csv')

# 2. Definir as colunas que serão transferidas
colunas_genero = [
    'first_author_gender',
    'second_author_gender',
    'third_author_gender',
    'fourth_author_gender',
    'fifth_author_gender',
    'sixth_author_gender',
    'seventh_author_gender'
]

# 3. Substituir os valores das colunas no primeiro dataset
df1[colunas_genero] = df2[colunas_genero]

# 4. Salvar o resultado em um novo arquivo (ou sobrescrever o original)
df1.to_csv('sbsc_dataset_enriquecido_ibge_2006_2025_atualizado.csv', index=False)
