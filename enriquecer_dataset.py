import pandas as pd
import re

# 1. Instalar bibliotecas necessárias se não tiver:
# pip install pandas openpyxl gender-guesser

try:
    import gender_guesser.detector as gender
    d = gender.Detector(case_sensitive=False)
except ImportError:
    d = None

# 2. Dicionário de Mapeamento de Instituições -> (UF, Região)
# Cobre as principais instituições do dataset do SBSC
mapa_instituicoes = {
    # Sudeste
    'UFRJ': ('RJ', 'Sudeste'), 'UNIRIO': ('RJ', 'Sudeste'), 'PUC-RIO': ('RJ', 'Sudeste'),
    'UFF': ('RJ', 'Sudeste'), 'UERJ': ('RJ', 'Sudeste'), 'CEFET/RJ': ('RJ', 'Sudeste'),
    'USP': ('SP', 'Sudeste'), 'UNICAMP': ('SP', 'Sudeste'), 'UNESP': ('SP', 'Sudeste'),
    'ITA': ('SP', 'Sudeste'), 'UFSCAR': ('SP', 'Sudeste'), 'UFABC': ('SP', 'Sudeste'),
    'UFMG': ('MG', 'Sudeste'), 'UFJF': ('MG', 'Sudeste'), 'CEFET-MG': ('MG', 'Sudeste'),
    'UNIFEI': ('MG', 'Sudeste'), 'UFV': ('MG', 'Sudeste'), 'UFLA': ('MG', 'Sudeste'),
    'UFES': ('ES', 'Sudeste'),
    
    # Norte
    'UFAM': ('AM', 'Norte'), 'UEA': ('AM', 'Norte'), 'IFAM': ('AM', 'Norte'),
    'UFPA': ('PA', 'Norte'), 'UFOPA': ('PA', 'Norte'), 'IFPA': ('PA', 'Norte'),
    'UNIFAP': ('AP', 'Norte'), 'UFRR': ('RR', 'Norte'), 'UNIR': ('RO', 'Norte'),
    
    # Nordeste
    'UFBA': ('BA', 'Nordeste'), 'FACULDADE RUY BARBOSA': ('BA', 'Nordeste'), 'UEFS': ('BA', 'Nordeste'),
    'UFPE': ('PE', 'Nordeste'), 'IFPE': ('PE', 'Nordeste'), 'UFRPE': ('PE', 'Nordeste'),
    'UFC': ('CE', 'Nordeste'), 'IFCE': ('CE', 'Nordeste'), 'UNIFOR': ('CE', 'Nordeste'),
    'UFRN': ('RN', 'Nordeste'), 'IFRN': ('RN', 'Nordeste'),
    'UFPB': ('PB', 'Nordeste'), 'UFCG': ('PB', 'Nordeste'),
    'UFMA': ('MA', 'Nordeste'), 'UFPI': ('PI', 'Nordeste'), 'UFAL': ('AL', 'Nordeste'), 'UFS': ('SE', 'Nordeste'),
    
    # Sul
    'UDESC': ('SC', 'Sul'), 'UFSC': ('SC', 'Sul'), 'UNIVALI': ('SC', 'Sul'),
    'UTFPR': ('PR', 'Sul'), 'UEM': ('PR', 'Sul'), 'UEL': ('PR', 'Sul'), 'PUCPR': ('PR', 'Sul'), 'UFPR': ('PR', 'Sul'),
    'UFRGS': ('RS', 'Sul'), 'PUCRS': ('RS', 'Sul'), 'UNISINOS': ('RS', 'Sul'), 'UFSM': ('RS', 'Sul'),
    
    # Centro-Oeste
    'UNB': ('DF', 'Centro-Oeste'), 'UFG': ('GO', 'Centro-Oeste'), 'UFMS': ('MS', 'Centro-Oeste'), 'UFMT': ('MT', 'Centro-Oeste')
}

# Nomes comuns no Brasil para fallback
nomes_femininos = {'ana', 'maria', 'juliana', 'patricia', 'camila', 'thais', 'leticia', 'luciana', 'carla', 'renata', 'vanessa', 'bruna', 'aline', 'fernanda', 'claudia', 'beatriz', 'gabriela', 'flavia', 'monique', 'laura', 'isabela', 'marcia', 'adriana', 'simone', 'paula', 'sabrina', 'mariana', 'suelyn', 'fabiane', 'tais'}
nomes_masculinos = {'carlos', 'joao', 'clever', 'marcio', 'alexandre', 'rafael', 'enzo', 'jaime', 'talles', 'amilcar', 'gledson', 'pedro', 'paulo', 'lucas', 'mateus', 'gabriel', 'rodrigo', 'diego', 'felipe', 'bruno', 'leonardo', 'gustavo', 'thiago', 'vinicius', 'andré', 'guilherme', 'daniel', 'marcelo', 'eduardo'}

def inferir_genero(nome):
    if pd.isna(nome) or not str(nome).strip():
        return ''
    primeiro_nome = str(nome).strip().split()[0].lower()
    
    if primeiro_nome in nomes_femininos or primeiro_nome.endswith(('a', 'ine', 'ele', 'is')):
        return 'Feminino'
    elif primeiro_nome in nomes_masculinos or primeiro_nome.endswith(('o', 'os', 'or', 'el', 'us')):
        return 'Masculino'
    
    if d:
        gen = d.get_gender(primeiro_nome)
        if 'female' in gen:
            return 'Feminino'
        elif 'male' in gen:
            return 'Masculino'
    return 'Indefinido'

def extrair_uf_regiao(filiacao):
    if pd.isna(filiacao) or not str(filiacao).strip():
        return '', ''
    sigla = str(filiacao).strip().upper()
    if sigla in mapa_instituicoes:
        return mapa_instituicoes[sigla]
    
    # Busca por padrões de UF conhecidos no texto
    for inst, (uf, reg) in mapa_instituicoes.items():
        if inst in sigla:
            return uf, reg
    return 'Outro/Internacional', 'Outro/Internacional'

# 3. Processar todas as abas da planilha
excel_file = 'Dataset SBSC 2006-2025 - Tratado.xlsx'
xls = pd.ExcelFile(excel_file)

lista_dfs = []

for sheet_name in xls.sheet_names:
    df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
    df_sheet['Ano_Publicacao'] = sheet_name
    
    # Para cada autor até o 8º autor, adiciona as colunas de Genero, UF e Regiao
    for i in range(1, 9):
        ordem = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth'][i-1]
        col_nome = f'{ordem}-author-name'
        col_affil = f'{ordem}-author-affiliation'
        
        if col_nome in df_sheet.columns:
            df_sheet[f'{ordem}_author_gender'] = df_sheet[col_nome].apply(inferir_genero)
        if col_affil in df_sheet.columns:
            res = df_sheet[col_affil].apply(extrair_uf_regiao)
            df_sheet[f'{ordem}_author_uf'] = [r[0] for r in res]
            df_sheet[f'{ordem}_author_regiao'] = [r[1] for r in res]
            
    lista_dfs.append(df_sheet)

# Consolida todas as edições em uma única base unificada
df_consolidado = pd.concat(lista_dfs, ignore_index=True)

# Salva a nova base enriquecida
df_consolidado.to_csv('sbsc_dataset_enriquecido_2006_2025.csv', index=False, encoding='utf-8-sig')
print(f"Sucesso! {len(df_consolidado)} artigos consolidados e enriquecidos com Gênero, UF e Região.")
