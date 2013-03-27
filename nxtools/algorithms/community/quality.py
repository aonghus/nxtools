from __future__ import division  # to ensure float division

import random
import networkx as nx
import nxtools as nxt

import logging

logging.basicConfig(format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s")
logging.getLogger().setLevel(logging.INFO)
#    Copyright(C) 2011 by
#    Ben Edwards <bedwards@cs.unm.edu>
#    Aric Hagberg <hagberg@lanl.gov>
#    All rights reserved.
#    BSD license.
__author__ = """\n""".join(['Ben Edwards (bedwards@cs.unm.edu)',
                          'Aric Hagberg (hagberg@lanl.gov)',
                          'Aonghus Lawlor (aonghuslawlor@gmail.com)'])


def choose(n, k):
    r"""
        Binomial coefficient
        
        Use this (slow) function when its not possible to import scipy.special.binom (eg. with pypy)
    """
    if 0 <= k <= n:
        p = 1
        for t in xrange(min(k, n - k)):
            p = (p * (n - t)) // (t + 1)
        return p
    return 0


def modularity(G, communities, weight='weight'):
    r"""Determines the Modularity of a partition C
    on a graph G.

    Modularity is defined as

    .. math::

        Q = \frac{1}{2m} \sum_{ij} \left( A_{ij} - \frac{k_ik_j}{2m}\right) 
            \delta(c_i,c_j)

    where `m` is the number of edges, `A` is the adjacency matrix of G, 
    `k_i` is the degree of `i` and `\delta(c_i,c_j)` is 1 if `i` and `j` 
    are in the same community and 0 otherwise.

    Parameters
    ----------
    G : NetworkX Graph

    communinities : list of sets
      Non-overlaping sets of nodes 

    Returns
    -------
    Q : Float
      The Modularity of the paritition

    Raises
    ------
    NetworkXError
      If C is not a partition of the Nodes of G

    Examples
    --------
    >>> G = nx.Graph()
    >>> nx.modularity(G,nx.kernighan_lin(G))
    0.3571428571428571

    Notes
    -----
    Defined on all Graph types, tested on Graph.
    Add more tests.
    
    References
    ----------
    .. [1] M. E. J Newman 'Networks: An Introduction', page 224
       Oxford University Press 2011.
    """
    if not nxt.unique_community(G, communities):
        raise NetworkXError("communities is not a unique partition of G")

    multigraph = G.is_multigraph()
    m = float(G.size(weight=weight))
    directed = G.is_directed()
    if G.is_directed():
        out_degree = G.out_degree(weight=weight)
        in_degree = G.in_degree(weight=weight)
        norm = 1.0 / m
    else:
        out_degree = G.degree(weight=weight)
        in_degree = out_degree
        norm = 1.0 / (2.0 * m)
    affiliation = nxt.affiliation_dict(communities)
    Q = 0.0
    for u in G:
        nbrs = (v for v in G if affiliation[u] == affiliation[v])
        for v in nbrs:
            try:
                if multigraph:
                    w = sum(d.get(weight, 1) for k, d in G[u][v].items())
                else:
                    w = G[u][v].get(weight, 1)
            except KeyError:
                w = 0
            #  double count self loop if undirected
            if u == v and not directed:
                w *= 2.0
            Q += w - in_degree[u] * out_degree[v] * norm
    return Q * norm


def modularityOverlap(G, communities, affiliation_dict=None, weight=None):
    r"""Determines the Overlapping Modularity of a partition C
    on a graph G.

    Modularity is defined as

    .. math::

    M_{c_{r}}^{ov} = \sum_{i \in c_{r}} \frac{\sum_{j \in c_{r}, i \neq j}a_{ij} - \sum_{j \not \in c_{r}}a_{ij}}{d_{i} \cdot s_{i}} \cdot \frac{n_{c_{r}}^{e}}{n_{c_{r}} \cdot \binom{n_{c_{r}}}{2}}

    Parameters
    ----------
    G : NetworkX Graph

    communinities : list of sets
      Non-overlaping sets of nodes 

    Returns
    -------
    Q : Float
      The Overlapping Modularity of the paritition

    Raises
    ------
    NetworkXError
      If C is not a partition of the Nodes of G

    Examples
    --------
    >>> G = nx.Graph()
    >>> nx.modularityOverlap(G,nx.kernighan_lin(G))
    0.3571428571428571

    Notes
    -----
    Defined on all Graph types, tested on Graph.
    Add more tests.
    
    References
    ----------
    "Modularity measure of networks with overlapping communities", A. Lazar, D. Abel and T. Vicsek, 
    EPL, 90 (2010) 18001
    doi: 10.1209/0295-5075/90/18001 
    """

    """
    # actually no need for binom since binom(n, 2) = n * (n - 1) / 2
    try:
        import scipy.special
        from scipy.special import binom
    except:
        binom = choose
    """

    if G.is_multigraph():
        raise NetworkXError("G should be not be a multigraph")

    if not affiliation_dict:
        affiliation_dict = nxutil.affiliation_dict(communities)
    
    # actually this factor is not necessary- I double count the edges for undirected graphs, 
    # so the factor turns out to be the same as for directed 
    # if G.is_directed():
    #    edgeCountNorm = 2
    # else:
    #    edgeCountNorm = 1
    # logging.info('edgeCountNorm {}'.format(edgeCountNorm))
    
    mOvTotal = 0
    
    for commId, nodes in communities.iteritems():
        nCommNodes = len(nodes)
        if nCommNodes <= 1: continue
        # logging.info('commId {} {}'.format(commId, nCommNodes))
        nInwardEdges = 0 
        commStrength = 0

        for node in nodes:
            degree, inwardEdges, outwardEdges = 0, 0, 0
            for (u, v, data) in G.edges(node, data=True):
                weight = data.get(weight, 1)
                degree += weight
                if v in nodes:
                    inwardEdges += weight
                else:
                    outwardEdges += weight

            nInwardEdges += inwardEdges
            affiliationCount = len(affiliation_dict[node])        
            commStrength += (inwardEdges - outwardEdges) / (degree * affiliationCount)
            # logging.info('{} {} {} {}'.format(commId, node, degree, affiliationCount))
        
        binomC = nCommNodes * (nCommNodes - 1)
        v1 = commStrength / nCommNodes
        v2 = (nInwardEdges / binomC)
        mOv = v1 * v2
        logging.info('comm, len(comm), v1, v2 = mOv: {} {} {} {} {}'.format(commId, nCommNodes, v1, v2, mOv))
        mOvTotal += mOv

    return mOvTotal / len(communities)

