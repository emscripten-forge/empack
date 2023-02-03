import networkx as nx


def toposort(pkg_metas):
    
    # from nx docu:
    # A topological sort is a nonunique permutation of the nodes of a directed graph 
    # such that an edge from u to v implies that u appears before v in the topological sort order.

    g = nx.DiGraph()

    name_to_meta = dict()
    for pkg_meta in pkg_metas:

        name = pkg_meta['name']
        g.add_node(name)
        name_to_meta[name] = pkg_meta
    
    for pkg_meta in pkg_metas:  
        name = pkg_meta['name']
        depends = [d.split(' ')[0] for d in pkg_meta['depends']]

        for d in depends:
            g.add_edge(d, name)


    sorted_nodes = [name_to_meta[n] for n in  nx.topological_sort(g)]
    print([n['name'] for n in sorted_nodes])
    return sorted_nodes
