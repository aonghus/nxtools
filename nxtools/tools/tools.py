#!/usr/bin/env python
# -*- coding: utf-8 -*-

import networkx as nx
import logging
import simplejson as json
from itertools import count
import collections
from networkx.readwrite.json_graph import node_link_data, node_link_graph

logging.basicConfig(format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
logging.getLogger().setLevel(logging.INFO)

class GTAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        import graph_tool        
        print 'default:', type(obj)
        if isinstance(obj, graph_tool.Vertex):
            print 'Vertex', obj
            return json.JSONEncoder.default(self, int(obj))
        elif isinstance(obj, graph_tool.Vector_double):
            print 'Vector_double', obj
            return json.JSONEncoder.default(self, obj.get_array().tolist())
        
        return json.JSONEncoder.default(self, obj)

class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        elif isinstance(obj, nx.Graph):
            return node_link_data(obj)
        return json.JSONEncoder.default(self, obj)


def writeEdgeList(G, path, data=None):
    if isinstance(path, str): path = open(path, 'w')
    # with open(f_edge_out, 'w') as f:
    for i, (u, v, d) in enumerate(G.edges(data=True)):
        if data:
            path.write('{} {} {}\n'.format(G.node[u]['id'], G.node[v]['id'], ' '.join(str(d[k]) for k in data)))
        else:
            path.write('{} {}\n'.format(G.node[u]['id'], G.node[v]['id']))                
    return

def ipairstonx(infile=None, sym=True, parser=None):
    def rowParser(row):
        source, target, weight = None, None, None
        if len(row) >= 2:
            source, target = int(row[0]), int(row[1])
            weight = float(row[2]) if len(row) > 2 else None
        return source, target, weight

    G = None
    if sym:
        G = nx.Graph()
    else:
        G = nx.DiGraph()

    parser = parser if parser else rowParser

    with open(infile, 'r') as f:
        for l in f:
            if l.startswith('#'): continue
            row = l.strip().split()
            source, target, weight = parser(row)
            # logging.info("row: %s %s %s [%s]" % (source, target, weight, l))
            # don't add undefined weights
            if weight:
                G.add_edge(source, target, weight=weight)
            else:
                G.add_edge(source, target)
    return G


def nxtojson(G, outfile):
    f = gzip.open(outfile, 'w') if outfile.endswith('.gz') else open(outfile, 'w')
    
    mapping = dict(zip(G, count()))
    print 'G: ', [n for n in G]
    print 'mapping:', mapping
    f.write('{\n')
    f.write("\"directed\": {0},\n".format(G.is_directed()).replace("True", "true").replace("False", "false"))
    f.write("\"multigraph\": {0},\n".format(G.is_multigraph()).replace("True", "true").replace("False", "false"))
    # f.write("\"multigraph\": {0},\n".format(G.is_multigraph()).replace("True", "true").replace("False", "false"))
    f.write("\"graph\": {0},\n".format(json.dumps(G.graph.items())))

    f.write('\"nodes\": [\n  ')
    for (i, node) in enumerate(G):
        # print 'node:', node, node.__class__, node.getPropertyKeys()
        if i != 0:
            f.write(',\n  ') 
        f.write(json.dumps(dict(id=node, **G.node[node])))
    
    f.write('],\n')
    f.write('\"links\": [\n  ')
    for (i, (u, v, d)) in enumerate(G.edges(data=True)):
        if i != 0:
            f.write(',\n  ')
        print u, v, mapping[u], mapping[v]
        f.write(json.dumps(dict(source=mapping[u], target=mapping[v], **d)))
        
    f.write(']\n')
    f.write('}\n')
    

def readCommunityFromTP(f):
    if isinstance(f, str):
        f = open(f, 'r')
    
    community = {}
    m_id = 0
    for l in f:
        if l.startswith('#'): continue
        if not m_id in community:
            community[m_id] = set()
        for nodeId in map(int, l.strip().split(' ')):
            community[m_id].add(nodeId)
        m_id += 1
    return community

def readCommunitiesFromTree(f):
    import re
    if isinstance(f, str):
        f = open(f, 'r')
    
    communities = {}
    for l in f:
        if l.startswith('#'): continue
        m = re.match("(.*) (.*) \"(.*)\"", l)
        # print m.group(1), '!', m.group(2), '!', m.group(3)
        
        modules = map(int, m.group(1).split(':'))
        nodeId = m.group(3)
        for i, m in enumerate(modules):
            if not i in communities: communities[i] = {}
            if not m in communities[i]:
                communities[i][m] = set()
            communities[i][m].add(nodeId)
        
    return communities


def readCommunity(filename):
    """
    The community is a dict of sets -> key(module_id), value(set of nodes)
    """
    import re
    f = gzopen(filename, 'r') if filename.endswith('.gz') else open(filename, 'r')
    line = f.readline()
    
    def _read_module_vertices(C, row):
        module = re.match("(\d+)", row[0]).group(1)
        C.append(set(map(int, row[1:])))
        # print 'row:', module, vertices, row
        return
    
    def _read_vertex_modules(C, row):
        vertex = re.match("(\d+)", row[0]).group(1)
        C.append(set(map(int, row[1:])))

        return
    
    read_module = None
    if re.match('# module: vertices', line):
        logging.info("module -> vertices")
        C = {}
        for i, line in enumerate(f):
            row = line.strip().split()
            module = int(re.match("(\d+)", row[0]).group(1))
            # C.append(set(map(int, row[1:])))
            C[module] = set(map(int, row[1:]))
        return C
    elif re.match('# vertex: modules', line):
        logging.info("vertex -> modules")
        C = collections.defaultdict(set)
        for i, line in enumerate(f):
            if line.startswith('#'): continue
            row = line.strip().split()
            vertex = int(re.match("(\d+)", row[0]).group(1))
            for m in row[1:]:
                module = int(m)
                # if not module in C: C[module] = set()
                C[module].add(vertex)
        return C
    
    return None

def affiliation_dict(community):
    """Return dictionary mapping node to a list of community labels.
    The community labels are arbitrary.
    """
    aff = collections.defaultdict(set)
    elems = enumerate(community) if isinstance(community, list) else community.iteritems()
    for i, partition in elems:
        for n in partition:
            aff[n].add(i)
    return aff
