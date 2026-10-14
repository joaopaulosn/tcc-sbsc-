import itertools
from pyvis.network import Network
import networkx as nx
import pandas as pd

# 1. Carregar dataset consolidado (2006-2026)
df = pd.read_csv("sbsc_dataset_genero_completo_2006_2026.csv")

# 2. Construir o grafo da rede de colaboração entre Instituições
G = nx.Graph()
positions = [
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
]

for idx, row in df.iterrows():
    affiliations = []
    for pos in positions:
        col_aff = f"{pos}-author-affiliation"
        col_reg = f"{pos}_author_regiao"
        col_uf = f"{pos}_author_uf"

        if (
            col_aff in df.columns
            and pd.notna(row[col_aff])
            and str(row[col_aff]).strip() != ""
        ):
            inst = str(row[col_aff]).strip().upper()
            reg = (
                str(row[col_reg]).strip()
                if (col_reg in df.columns and pd.notna(row[col_reg]))
                else "Outro/Internacional"
            )
            uf = (
                str(row[col_uf]).strip()
                if (col_uf in df.columns and pd.notna(row[col_uf]))
                else "Outro/Internacional"
            )

            affiliations.append(inst)
            if inst not in G:
                G.add_node(inst, regiao=reg, uf=uf)

    # Adiciona arestas entre instituições distintas que colaboraram no mesmo artigo
    unique_affs = set(affiliations)
    for inst1, inst2 in itertools.combinations(unique_affs, 2):
        if G.has_edge(inst1, inst2):
            G[inst1][inst2]["weight"] += 1
        else:
            G.add_edge(inst1, inst2, weight=1)

# 3. Calcular métricas de centralidade
deg_centrality = nx.degree_centrality(G)
betweenness_centrality = nx.betweenness_centrality(G)
closeness_centrality = nx.closeness_centrality(G)
degree_dict = dict(G.degree())

nodes_data = []
for node in G.nodes():
    nodes_data.append({
        "Instituição": node,
        "Região": G.nodes[node].get("regiao", "N/A"),
        "UF": G.nodes[node].get("uf", "N/A"),
        "Instituições Parceiras Diretas": degree_dict[node],
        "Centralidade Grau": round(deg_centrality[node], 6),
        "Intermediação (Betweenness)": round(betweenness_centrality[node], 6),
        "Proximidade (Closeness)": round(closeness_centrality[node], 6),
    })

df_metrics = pd.DataFrame(nodes_data)
df_metrics.sort_values(
    by="Instituições Parceiras Diretas", ascending=False, inplace=True
)

# -------------------------------------------------------------
# EXPORTAÇÃO 1: Tabela completa em CSV
# -------------------------------------------------------------
df_metrics.to_csv(
    "metricas_centralidade_instituicoes.csv",
    index=False,
    encoding="utf-8-sig",
)
print("Arquivo 'metricas_centralidade_instituicoes.csv' gerado com sucesso!")

# -------------------------------------------------------------
# EXPORTAÇÃO 2: Relatório em TXT com Resumo e Rankings
# -------------------------------------------------------------
top_degree = df_metrics.sort_values(
    by="Instituições Parceiras Diretas", ascending=False
).head(10)
top_betweenness = df_metrics.sort_values(
    by="Intermediação (Betweenness)", ascending=False
).head(10)
top_closeness = df_metrics.sort_values(
    by="Proximidade (Closeness)", ascending=False
).head(10)

with open("resumo_rede_instituicoes.txt", "w", encoding="utf-8") as f:
    f.write("=== RESUMO GLOBAL DA REDE DE INSTITUIÇÕES SBSC (2006-2026) ===\n")
    f.write(f"Total de Instituições (Nós): {G.number_of_nodes()}\n")
    f.write(
        f"Total de Parcerias Interinstitucionais (Arestas): {G.number_of_edges()}\n"
    )
    f.write(
        f"Número de Componentes Conectados: {nx.number_connected_components(G)}\n\n"
    )

    f.write("=== TOP 10 - CENTRALIDADE DE GRAU (MAIS PARCERIAS) ===\n")
    f.write(
        top_degree[[
            "Instituição",
            "Região",
            "UF",
            "Instituições Parceiras Diretas",
            "Centralidade Grau",
        ]].to_string(index=False)
    )

    f.write("\n\n=== TOP 10 - CENTRALIDADE DE INTERMEDIAÇÃO (PONTES) ===\n")
    f.write(
        top_betweenness[[
            "Instituição",
            "Região",
            "UF",
            "Intermediação (Betweenness)",
        ]].to_string(index=False)
    )

    f.write("\n\n=== TOP 10 - PROXIMIDADE ===\n")
    f.write(
        top_closeness[[
            "Instituição",
            "Região",
            "UF",
            "Proximidade (Closeness)",
        ]].to_string(index=False)
    )

print("Arquivo 'resumo_rede_instituicoes.txt' gerado com sucesso!")

# -------------------------------------------------------------
# EXPORTAÇÃO 3: Grafo Interativo com PyVis (Maior Componente Conectada)
# -------------------------------------------------------------
largest_cc = max(nx.connected_components(G), key=len)
subG = G.subgraph(largest_cc)

net = Network(
    height="750px",
    width="100%",
    bgcolor="#ffffff",
    font_color="black",
    notebook=False,
)

# Paleta de cores para identificar as regiões brasileiras
color_map = {
    "Sudeste": "#1f77b4",  # Azul
    "Nordeste": "#ff7f0e",  # Laranja
    "Sul": "#2ca02c",  # Verde
    "Norte": "#d62728",  # Vermelho
    "Centro-Oeste": "#9467bd",  # Roxo
    "Outro/Internacional": "#8c564b",  # Marrom / Cinza
}

top_15 = set(
    df_metrics.sort_values(
        by="Instituições Parceiras Diretas", ascending=False
    ).head(15)["Instituição"]
)

for n in subG.nodes():
    regiao = subG.nodes[n].get("regiao", "Outro/Internacional")
    uf = subG.nodes[n].get("uf", "N/A")
    color = color_map.get(regiao, "gray")

    size = degree_dict[n] * 1.8 + 10
    label = n if n in top_15 else ""  # Nome visível para as 15 maiores instituições

    net.add_node(
        n,
        label=label,
        title=f"Instituição: {n}\nRegião: {regiao}\nUF: {uf}\nParceiros Diretos: {degree_dict[n]}",
        color=color,
        size=size,
    )

for edge in subG.edges(data=True):
    net.add_edge(
        edge[0], edge[1], weight=edge[2].get("weight", 1), color="#cccccc"
    )

net.repulsion(
    node_distance=180,
    central_gravity=0.2,
    spring_length=220,
    spring_strength=0.05,
)
net.save_graph("rede_colaboracao_instituicoes_sbsc_2006_2026.html")
print(
    "Arquivo 'rede_colaboracao_instituicoes_sbsc_2006_2026.html' gerado com sucesso!"
)
