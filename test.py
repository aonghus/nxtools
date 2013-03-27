#!/usr/bin/env python

import optparse

import networkx as nx
import nxtools as nxt
import logging

logging.basicConfig(format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
logging.getLogger().setLevel(logging.INFO)

def main_old():
    G = nx.barbell_graph(3,0)
    C = nxt.greedy_max_modularity_partition(G)
    nxt.write_community_gecmi(C, open('comm_gecmi.dat', 'w'))
    return

def main():
    parser = optparse.OptionParser()
    parser.add_option("--infile", dest="infile", help="infile", default=None, type='str')
    parser.add_option("--outfile", dest="outfile", help="outfile", default=None, type='str')
    (opts, args) = parser.parse_args()    

    graph = None
    if opts.infile.endswith('.ipairs'):
        print 'reading edgelist'
        graph = nx.read_edgelist(opts.infile, create_using=nx.Graph(), nodetype=int, data=False)
    elif opts.infile.endswith('.pkl'):
        graph = nx.read_gpickle(opts.infile)
    else:
        logging.info("could not identify this graph type- trying edgelist")
        graph = nx.read_edgelist(opts.infile, create_using=nx.Graph(), nodetype=int, data=False)

    print 'graph:', graph
    C = nxt.spectral_modularity_partition(graph)
    #C = nxt.greedy_max_modularity_partition(graph)
    nxc.write_community_gecmi(C, open('comm_gecmi.dat', 'w'))


    return

if __name__ == '__main__':
    main()
