#ネットワーク図の描画
#ここではpyvisを使用
import networkx as nx
from networkx.algorithms.community import girvan_newman
from pyvis.network import Network

# 使用する色を定義
class ColoredObject:
    def __init__(self, color):
        self.color = color

colors = ["#CBCCCD", "#FF9999", "blue", "green", "#A2CEF6", "magenta", "brown",  "yellow", "orange", "purple", "#EDABE5", "black" ]

#インデックスに基づいた色の選択
def choose_color(index):
    #インデックスが色のリストを超えないよう調整
    return colors[index % len(colors)]

def kyoki_word_network(df):

    #Girvan-Newmanアルゴリズムによるコミュニティ分割（networkxの機能）
    G = nx.from_pandas_edgelist(df, '1番目', '2番目', ['count'])
    comp = girvan_newman(G)
    communities = tuple(sorted(c) for c in next(comp))

    #各コミュニティに色を割り当てる
    color_map = {}
    for i, community in enumerate(communities):
        color = choose_color(i) 
        for node in community:
            color_map[node] = color
        
    got_net = Network(height="1000px", width="95%", bgcolor="#FFFFFF", font_color="black", notebook=True)

    got_net.force_atlas_2based()
    got_data = df

    sources = got_data['1番目']
    targets = got_data['2番目']
    weights = got_data['count']

    edge_data = zip(sources, targets, weights)

    for e in edge_data:
        src = e[0]
        dst = e[1]
        w = e[2]
        got_net.add_node(src, src, title=src, color=color_map.get(src, None))
        got_net.add_node(dst, dst, title=dst, color=color_map.get(dst, None))
        got_net.add_edge(src, dst, value=w)

    # コミュニティごとにノードの色を設定
    for node, color in color_map.items():
        got_net.add_node(node, color=color)

    neighbor_map = got_net.get_adj_list()

    for node in got_net.nodes:
        node["title"] += " Neighbors:<br>" + "<br>".join(neighbor_map[node["id"]])
        node["value"] = len(neighbor_map[node["id"]])

    return got_net