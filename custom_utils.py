#customized utils

def parse_input(edgefile, delimiter, isDirected=False, isWeighted=False):
    """
    Input file parser that takes in a file full of edges and parses them according to a modular delimiter. Can handle edge files that have weights, but the setting is off by default.
    Returns a graph object.
    Throws out self loops.
    """
    edge_set = set()
    node_set = set()
    if not isWeighted:
        max_edge_size = 2
    else:
        max_edge_size = 3

    with open(edgefile, 'r') as f:
        for line in f:
            ls = line.strip('\n').split(delimiter)
            if (len(ls) != max_edge_size) and (len(ls) != max_edge_size-1):
                print("Something went wrong during input_parser(). There were " + str(len(ls)) + " columns in line:\n" + line.strip('\n') + "\nExpected " + str(max_edge_size) + " or " + str(max_edge_size-1) + " columns.")
                return -1

            handleData(ls, edge_set, node_set, isDirected, isWeighted)


    nodes = set_to_list(node_set)

    edges = []
    for e in edge_set:
        edges.append(set_to_list(e))
    
    g = Graph(nodes, edges)

    return g, nodes, edges



def handleData(ls, edge_set, node_set, isDirected, isWeighted):
    #helper function for parse_input
    #updates edge_set and node_set according to the number of elements in the data list and isDirected, isWeighted
    if not isWeighted:
        if len(ls) == 2:      #wont add self loops to the edge list, but adds nodes in self loops to the node list
            if not isDirected:
                new_edge = frozenset(ls)
                edge_set.add(new_edge)
            else:
                new_edge = (ls[0],ls[1])
                edge_set.add(new_edge)
        for node in ls:
            node_set.add(node)

    else:
        if len(ls) == 3:              #wont add self loops to edge list, but adds nodes in self loops to the node list
            if not isDirected:
                new_edge = frozenset(ls)
                edge_set.add(new_edge)
            else:
                new_edge = (ls[0],ls[1],ls[2])
                edge_set.add(new_edge)
            node_set.add(ls[0])
            node_set.add(ls[1])

        if len(ls) == 2:
            node_set.add(ls[0])


def set_to_list(s):
    #helper function
    #converts a set to a list
    ls = []
    for item in s:
        ls.append(item)
    return ls

'''
#uncomment this and comment out all the code below to get parse_input() to run if it's currently throwing an error.
class Graph:
    #dummy graph class so that parse_input() doesn't throw an error during testing
    def __init__(self, nodes, edges):
        pass
'''

class Graph:
"""
This class will provide all the planned functionality. The basic idea is to be able to scale a given visual attribute (on graphspace) by a given data attribute as easily as possible without loss of customization power.
We do this by keeping a directory of data attributes which can be updated by the user on the fly. Additionally, a basic adjacency list method is included if a user doesn't want to deal with the hassle of learning my framework.
"""

    def __init__(self, nodes, edges, isDirected=False, isWeighted=False):
        self.isDirected = isDirected
        self.isWeighted = isWeighted

        self.working_node_dir = set()
        self.working_edge_dir = set()
        self.naive_nodes = nodes
        self.naive_edges = edges
        
        self.nodes = self.init_nodes(nodes)
        self.edges = self.init_edges(edges)

    def init_nodes(self,nodes):
        self.init_node_dir()
        pass
    

    def init_edges(self,edges):
        self.init_edge_dir()
        pass

    def init_node_dir(self):
        pass

    def init_edge_dir(self):
        pass
    
    def __dir__(self):
        return (self.working_node_dir, self.working_edge_dir)

    def get_adj_ls(self):
        #returns a naive adjacency list based on the data given by parse_input()
        d = {}
        for n in self.naive_nodes:
            d[n] = []

        for e in self.naive_edges:
            if not self.isDirected:
                d[e[0]] = e[1]
                d[e[1]] = e[0]
            else:
                d[e[0]] = e[1]
        return d
                
            


class Node:
    #node class for the graph with attributes that can be dynamically updated by a user(!)
    #we do this by keeping track of a set of terms called the directory (accessible using the Python inbuilt dir() function) and a dictionary which holds all the information
    #to make a new attribute, run newAttr() to install a new term in the directory. Only then is put() able to add a key value pair to the dictionary for that attribute.
    #to access data from this node class, use the accession function get()
    def __init__(self, ID):
        self.d = {}
        self.dir_set = set()
        self.newAttr('ID')
        self.put('ID', ID)

    def put(self, attrName,val,loud=False):
        #inputs a value for an existing attribute
        if attrName not in dir(self):
            raise NameError('Node object contains no attribute called ' + str(attrName))
        else:
            self.d[attrName] = val

    def get(self,attrName,loud=False):
        #gets a value for an existing attribute
        #if the attribute exists in the directory, but no value has been put, returns None (prints a warning if the loud argument is True)
        if attrName not in dir(self):
            raise NameError('Node object contains no attribute called ' + str(attrName))
        elif attrName not in self.d:
            if loud:
                print("Warning! Attempting to get() attribute " + str(attrName) + " value from node " + str(self.get('ID')) + ". A value for this attribute has not been set. (returns None)")
            return None
        else:
            return self.d[attrName]
        
            
    def newAttr(self, attrName,loud=False):
        #installs a new attribute in the directory for recognition by the put() and get() methods.
        #uses a set to avoid adding the same attribute multiple times (prints a warning when this happens if loud=True)
        if loud and (attrName in dir_set):
            print("Warning! Attempting to add a new attribute " + str(attrName) + " to node " + str(self.get('ID')) + " but that attribute already exists in the directory.")
            
        self.dir_set.add(attrName)

    def __dir__(self):
        #gives the directory in list form.
        #this is magic class syntax. access this method via the Python inbuilt function dir()
        #for example, if you made a node whose variable name is a, then to see the directory you would give dir(a) in python interactive.
        return set_to_list(self.dir_set)

