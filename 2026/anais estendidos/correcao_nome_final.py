from collections import defaultdict
import re
import unicodedata
import pandas as pd

# 1. Carregar dataset consolidado
input_file = 'sbsc_dataset_genero_completo_2006_2026.csv'
output_file = 'sbsc_dataset_genero_completo_2006_2026_nomes_corrigidos.csv'

df = pd.read_csv(input_file)

# Limpar nomes das colunas
df.columns = [c.strip() for c in df.columns]
df = df.loc[:, ~df.columns.duplicated(keep='first')]

author_cols = [
    f'{p}-author-name'
    for p in [
        'first',
        'second',
        'third',
        'fourth',
        'fifth',
        'sixth',
        'seventh',
        'eighth',
    ]
    if f'{p}-author-name' in df.columns
]
affil_cols = [
    f'{p}-author-affiliation'
    for p in [
        'first',
        'second',
        'third',
        'fourth',
        'fifth',
        'sixth',
        'seventh',
        'eighth',
    ]
    if f'{p}-author-affiliation' in df.columns
]


# Função auxiliar para remover acentos/cedilhas na hora de comparar chaves de grupos
def remove_accents(text):
  return ''.join(
      c
      for c in unicodedata.normalize('NFD', text)
      if unicodedata.category(c) != 'Mn'
  )


# 2. Coletar e agrupar TODAS as variações de nomes existentes no dataset
raw_names = set()
for col in author_cols:
  for val in df[col].dropna().astype(str):
    name = val.strip()
    if len(name) > 2:
      raw_names.add(name)

groups = defaultdict(set)
for name in raw_names:
  clean_name = re.sub(r'\s+', ' ', name).strip()
  parts = clean_name.split()
  if len(parts) >= 2:
    # Agrupa ignorando acentos/cedilhas no primeiro e ultimo nome
    first = remove_accents(parts[0].lower())
    last = remove_accents(parts[-1].lower())
    groups[(first, last)].add(clean_name)

# 3. Gerar o Dicionário de Equivalências Completo para os Autores
equiv_dict = {}

# Mapeamentos manuais para garantir 100% de precisão em casos com variações de acento/cedilha
manual_overrides = {
    'juliana frança': 'juliana b. d. s. frança',
    'juliana franca': 'juliana b. d. s. frança',
    'juliana b. s. frança': 'juliana b. d. s. frança',
    'juliana b. s. franca': 'juliana b. d. s. frança',
    'juliana b. d. s. franca': 'juliana b. d. s. frança',
    'juliana b. d. s. frança': 'juliana b. d. s. frança',
}

for (first, last), names_set in groups.items():
  if len(names_set) > 1:
    sorted_names = sorted(list(names_set), key=lambda x: len(x), reverse=True)
    canonical_target = sorted_names[0].lower()

    for n in names_set:
      equiv_dict[n.lower()] = canonical_target

# Aplica as exceções manuais sobre o dicionário de equivalências
equiv_dict.update(manual_overrides)


# Função de substituição dos nomes dos autores
def correct_author_name(name):
  if not isinstance(name, str) or pd.isna(name):
    return None

  clean_val = name.strip()
  clean_lower = clean_val.lower()

  if clean_lower in equiv_dict:
    return equiv_dict[clean_lower]

  return clean_val


# 4. Função de limpeza de filiações (Manter 1ª instituição e padronizar CP2)
def clean_first_affiliation(aff):
  if not isinstance(aff, str) or pd.isna(aff):
    return None
  aff = aff.strip()

  # Pega apenas a primeira instituição em caso de barras ou ponto e vírgula (ex: UFRJ/CP2 -> UFRJ)
  first_part = re.split(r'[/;]', aff)[0].strip()

  # Se houver sigla dentro de parênteses, extrai a sigla
  match = re.search(r'\(([^)]+)\)', first_part)
  if match:
    first_part = match.group(1).strip()

  # Padronização do Colégio Pedro II: cpii / Pedro II / Colégio Pedro II -> CP2
  if re.search(r'\b(cpii|colégio pedro ii|pedro ii)\b', first_part, re.IGNORECASE):
    return 'CP2'

  return first_part


# 5. Aplicar todo o tratamento no DataFrame
for pos in [
    'first',
    'second',
    'third',
    'fourth',
    'fifth',
    'sixth',
    'seventh',
    'eighth',
]:
  col_name = f'{pos}-author-name'
  col_aff = f'{pos}-author-affiliation'

  if col_name in df.columns:
    df[col_name] = df[col_name].apply(correct_author_name)

  if col_aff in df.columns:
    df[col_aff] = df[col_aff].apply(clean_first_affiliation)

# 6. Salvar o arquivo final tratado
df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f'Total de variações de autores mapeadas no dicionário: {len(equiv_dict)}')
print(f"Dataset tratado e salvo em '{output_file}'.")
