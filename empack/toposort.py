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

    try:
        sorted_nodes = [name_to_meta[n] for n in nx.topological_sort(g)]
    except nx.exception.NetworkXUnfeasible as e:
        print('Failed to perform the topological sorting on graph:')
        for edge in g.edges:
            print(edge)
        raise e

    return sorted_nodes
