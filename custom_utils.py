#customized utils
import math
import json_utils
import graphspace_utils

try:
    import networkx as nx
    print("networkx was succesfully imported!")
    nx_import = True
except ImportError:
    print("networkx was not successfully imported.")
    nx_import = False


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
    edges = set_to_list(edge_set)
    
    g = Graph(nodes, edges, isDirected, isWeighted)

    return g, nodes, edges



def handleData(ls, edge_set, node_set, isDirected, isWeighted):
    #helper function for parse_input
    #updates edge_set and node_set according to the number of elements in the data list and isDirected, isWeighted
    if not isWeighted:
        if len(ls) == 2:      #wont add self loops to the edge list, but adds nodes in self loops to the node list
            new_edge = tuple(ls)
            edge_set.add(new_edge)
        for node in ls:
            node_set.add(node)

    else:
        if len(ls) == 3:              #wont add self loops to edge list, but adds nodes in self loops to the node list
            new_edge = tuple(ls)
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
    
    
def vector_add(ls1, ls2):
    #helper function, does vector addition
    if len(ls1) != len(ls2):
        raise IndexError("Error! Tried to add vectors " + str(ls1) + " and " + str(ls2) + " but these vectors have different lengths.")
    new = []
    for i in range(len(ls1)):
        new.append(ls1[i] + ls2[i])
    return new

def scalar_mult(s, vector):
    #helper function, multiplies a vector by a scalar
    new = []
    for e in vector:
        new.append(s*e)
    return new

def vector_to_RGB(vector):
    if len(vector) != 3:
        raise IndexError("Error! Tried to convert vector " + str(vector) + " to RGB hex string, but vector was not length 3.")
    for i in vector:
        if i > 255 or i < 0:
            raise ValueError("Error! Tried to convert vector " + str(vector) + " to RGB hex string but vector value " + str(i) + " was not between 0 and 255.")
    
    return '#{:02x}{:02x}{:02x}'.format(int(vector[0]),int(vector[1]),int(vector[2]))
    
    
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
    We do this by keeping a directory of data attributes which can be updated by the user on the fly. (Though the directory kept in the Graph object is mostly superficial at the moment. The Node class does all of the heavy lifting when it comes to actually enforcing the directory rules.)
    Additionally, a basic adjacency list method is included if a user doesn't want to deal with the hassle of learning my framework.
    Now has a working method normNodeAttr() that returns a normalized dictionary for any node attribute. Pretty snazzy.
    """

    ########################################################
    #INFRASTRUCTURE METHODS (not for user)##################
    ########################################################
    
    def __init__(self, nodes, edges, isDirected=False, isWeighted=False):
        self.isDirected = isDirected
        self.isWeighted = isWeighted

        self.node_dir = set()
        self.edge_dir = set()
        self.naive_nodes = nodes
        self.naive_edges = edges
        
        self.nodes = self.init_nodes(nodes)
        self.edges = self.init_edges(edges)
        
        self.GSnodeDir = set()
        self.GSedgeDir = set()
        
        self.GSnodeAttrs = self.initGSnodeAttrs()
        self.GSedgeAttrs = self.initGSedgeAttrs()
        
        self.GStitle = None
        self.GSdesc = None
        self.GStags = None

    def __dir__(self):
        return [set_to_list(self.node_dir), set_to_list(self.edge_dir)]


    #
    #infrastructure methods for nodes
    #
    def init_nodes(self,nodes):
        self.init_node_dir()
        node_ls = []
        for n in nodes:
            node_ls.append(Node(n))
        node_ls.sort(key=lambda x: x.get('ID'))    #sorts the node list by ID
        return node_ls
    
    def init_node_dir(self):
        self.node_dir.add('ID')
    
    def newNodeAttr(self,attrName,loud=False):
        #helper function for installNodeAttr
        #installs attrName in the directory of each node in the graph.
        for n in self.nodes:
            n.newAttr(attrName,loud)
        self.node_dir.add(attrName)

    
    def putNodeAttrs(self,attrName, attrDict, loud=False):
        #helper function for installNodeAttr
        #give a dictionary whose keys are node IDs and whose values are the values for the desired attribute as attrDict
        #this function uses put() to update the values of the given attribute for each node.
        for n in self.nodes:
            n.put(attrName,attrDict[n.get('ID')],loud)
    
    
    #
    #infrastructure methods for edges
    #
    def init_edges(self,edges):
        self.init_edge_dir()
        edge_ls = []
        for e in edges:
            if self.isWeighted and self.isDirected:
                edge_ls.append(Edge(e[0],e[1],e[2],directed=True))
            elif self.isWeighted:
                edge_ls.append(Edge(e[0],e[1],e[2]))
            elif (not self.isWeighted) and self.isDirected:
                edge_ls.append(Edge(e[0],e[1],directed=True))
            else:
                edge_ls.append(Edge(e[0],e[1]))
        return edge_ls
    
    def init_edge_dir(self):
        self.edge_dir.add('nodes')
        self.edge_dir.add('ID')
        self.edge_dir.add('source')
        self.edge_dir.add('target')
        if self.isWeighted:
            self.edge_dir.add('weight')
    
    def newEdgeAttr(self,attrName,loud=False):
        for e in self.edges:
            e.newAttr(attrName,loud)
        self.node_dir.add(attrName)
    
    def putEdgeAttrs(self, attrName, attrDict, loud=False):
        for e in self.edges:
            e.put(attrName, attrDict[e.get('ID')],loud)
    
    
    
    #############################
    #misc helper functions#######
    #############################
    
    def check_nore(self, n_or_e):
        if n_or_e == 'n':
            return self.nodes
        elif n_or_e == 'e':
            return self.edges
        else:
            raise NameError('n_or_e must be either \'n\' for nodes or \'e\' for edges.')

    
    
    #########################################################
    #DATA INPUT/RETRIEVAL METHODS############################
    #########################################################
    
    def installNodeAttr(self, attrName, attrDict, loud=False):
        #this method works a new attribute into the dynamic framework of the Node class
        #give the desired name of the new attribute, along with a dictionary whose keys are node IDs and whose values are the values for the new attribute
        #run this method and all the nodes in the graph will now have that attribute and the associated value from the dictionary.
        self.newNodeAttr(attrName, loud)
        self.putNodeAttrs(attrName, attrDict, loud)
    
    def installEdgeAttr(self, attrName, attrDict, loud=False):
        #same as installNodeAttr() but for edges
        self.newEdgeAttr(attrName, loud)
        self.putEdgeAttrs(attrName, attrDict, loud)
    
    def getAttr(self, attrName, n_or_e, loud=False):
        #returns a dictionary whose keys are IDs and whose values are values of the given attribute
        d = {}
        if n_or_e == 'n':
            working_group = self.nodes
        elif n_or_e == 'e':
            working_group = self.edges
        else:
            raise NameError('n_or_e must be either \'n\' for nodes or \'e\' for edges.')
        
        for x in working_group:
            d[x.get('ID',loud)] = x.get(attrName,loud)
        
        return d
    
    def getNodeAttr(self, attrName, loud=False):
        #returns a dictionary whose keys are node IDs and whose values are the given attribute
        return self.getAttr(attrName, 'n', loud)
        
    def getEdgeAttr(self, attrName, loud=False):
        #returns a dictionary whose keys are edge IDs and whose values are the given attribute
        return self.getAttr(attrName, 'e', loud)
    
    def putAttrs(self, attrName, attrDict, n_or_e, loud=False):
        if n_or_e == 'n':
            working_group = self.nodes
        elif n_or_e == 'e':
            working_group = self.edges
        else:
            raise NameError('n_or_e must be either \'n\' for nodes or \'e\' for edges.')
        
        for x in working_group:
            x.put(attrName, attrDict[x.get('ID')])
        
    def putNodeAttr(self, attrName, attrDict, loud=False):
        self.putAttrs(attrName,attrDict,'n',loud)
    
    def putEdgeAttr(self, attrName, attrDict, loud=False):
        self.putAttrs(attrName,attrDict,'e',loud)
    
    #########################################################
    #UTILITY METHODS#########################################
    #########################################################        
    
    def normNodeAttr(self,attrName,loud=False):
        #normalizes the values for the given node attribute and returns the normalized values as a dictionary
        return self.normByAttr(attrName, 'n', loud)

    def normEdgeAttr(self,attrName,loud=False):
        #normalizes the values for the given edge attribute and returns the normalized values as a dictionary
        return self.normByAttr(attrName, 'e', loud)

    def normByAttr(self, attrName, n_or_e='n', loud=False):
        #generalized method for getting a dictionary with normalized values according to the given attribute
        #the keys of the dictionary are the ID's of the objects.
        d = {}
        if n_or_e == 'n':
            working_group = self.nodes
        elif n_or_e == 'e':
            working_group = self.edges
        else:
            raise NameError('n_or_e must be either \'n\' for nodes or \'e\' for edges.')
        
        for x in working_group:
            d[x.get('ID')] = float('nan')
        
        for x in working_group:
            if x.get(attrName,loud) != None:
                a_max = x.get(attrName,loud)
                max_x = x
                break
        else:
            raise TypeError('Could not normalize by attribute ' + str(attrName) + 'because all nodes have None for that attribute.')
        
        for x in working_group:
            if x.get(attrName,loud) != None and x.get(attrName,loud) > a_max:
                a_max = x.get(attrName,loud)
                max_x = x
        
        for x in working_group:
            if x.get(attrName,loud) != None:
                d[x.get('ID')] = x.get(attrName,loud)/float(a_max)
        
        return d


    def get_adj_ls(self):
        #returns a naive adjacency list based on the data given by parse_input()
        d = {}
        for n in self.naive_nodes:
            d[n] = []

        for e in self.naive_edges:
            if not self.isDirected:
                d[e[0]].append(e[1])
                d[e[1]].append(e[0])
            else:
                d[e[0]].append(e[1])
        return d

    def better_adj_ls(self):
        d = {}
        for n in self.nodes:
            d[n.get('ID')] = []
            
        for e in self.edges:
            if not self.isDirected:
                d[e.get('source')].append(e.get('target'))
                d[e.get('target')].append(e.get('source'))
            else:
                d[e.get('source')].append(e.get('target'))
        return d

    ###############################################
    #GRAPHSPACE METHODS############################
    ###############################################

    def initGSnodeAttrs(self):
        attrs = {}
        for n in self.nodes:
            attrs[n.get('ID')] = {}
            attrs[n.get('ID')]['id'] = n.get('ID')
            attrs[n.get('ID')]['content'] = n.get('ID')
        return attrs
    
    def initGSedgeAttrs(self):
        attrs = {}
        for e in self.edges:
            s = e.get('source')
            t = e.get('target')
            if s not in attrs:
                attrs[s] = {}
            attrs[s][t] = {}
        return attrs
    
    
    def GSnodeAttrInstall(self,GSattr,loud=False):
        #finds the node attribute corresponding with the given GraphSpace attribute and puts it into the GSnodeAttr dictionary.
        if GSattr not in self.GSnodeDir:
            if loud:
                print('GraphSpace attribute ' + GSattr + ' not yet in GS Node Attribute Directory. Adding now.')
            self.GSnodeDir.add(GSattr)
        
        key_str = '__'+GSattr+'__'
        attrs = self.GSnodeAttrs
        for n in self.nodes:
            attrs[n.get('ID')][GSattr] = n.get(key_str,loud)
        self.GSnodeAttrs = attrs

    
    def GSedgeAttrInstall(self,GSattr,loud=False):
        #finds the edge attribute corresponding with the given GraphSpace attribute and puts it into the GSnodeAttr dictionary.
        if GSattr not in self.GSedgeDir:
            if loud:
                print('GraphSpace attribute ' + GSattr + ' not yet in GS Edge Attribute Directory. Adding now.')
            self.GSedgeDir.add(GSattr)
        
        key_str = '__'+GSattr+'__'
        attrs = self.GSedgeAttrs
        for e in self.edges:
            attrs[e.get('source')][e.get('target')][GSattr] = e.get(key_str)
        self.GSedgeAttrs = attrs

        
    def GSattrsUpdate(self, loud=False):
        for attr in self.GSnodeDir:
            self.GSnodeAttrInstall(attr,loud)
        
        for attr in self.GSedgeDir:
            self.GSedgeAttrInstall(attr,loud)
        
        
        
    def uploadGraph(self, title=None, graphID=None, desc=None, tags=None):
        self.GSattrsUpdate()
        json_filename = 'graphspace_upload.json'
        user = input("Graphspace username: ")
        pw = input("Graphspace password: ")
        if title == None and self.GStitle == None:
            title = input("Graph title: ")
        if graphID == None:
            graphID = input("Graph ID: ")
        if desc == None and self.GSdesc == None:
            desc = input("Graph description: ")
        if tags == None and self.GStags == None:
            tag_str = input("Graph tags (separated by comma): ")
            tags = tag_str.strip().split(',')
        
        n_ls = [x.get('ID') for x in self.nodes]
        
        e_ls = []
        for e in self.edges:
            e_ls.append([e.get('source'), e.get('target')])
        
        data = json_utils.make_json_data(n_ls, e_ls, self.GSnodeAttrs, self.GSedgeAttrs, title, desc, tags)
        json_utils.write_json(data,json_filename)
        graphspace_utils.postGraph(graphID, json_filename, user, pw)
        
        
    ###############################################################
    #SCALABILITY HELPER METHODS (not for user)#####################
    ###############################################################
    
    def scaleGradientByNodeAttr(self, color1, color2, attrName, loud=False):
        normDict = self.normNodeAttr(attrName,loud)
        self.getNodeGradient(color1,color2,normDict,loud)
    
    def getNodeGradient(self, color1, color2, normDict, loud=False):
        color_dict = {}
        for n in self.nodes:
            color_dict[n.get('ID',loud)] = n.getGColor(color1,color2,normDict[n.get('ID',loud)]) #not sure how this handles None or nan yet, I'll figure out those corner cases later on.
        
        if 'background_color' not in self.node_dir:
            self.installNodeAttr('__background_color__',color_dict,loud)
        else:
            self.putNodeAttrs('__background_color__',color_dict,loud)
        self.GSnodeAttrInstall('background_color',loud)
        
    
    ##################################################
    #GRAPH ANALYSIS METHODS###########################
    ##################################################
    
    def getNodeDegree(self,loud=False):
        adj_ls = self.better_adj_ls()
        deg_dict = {}
        for n in self.nodes:
            deg_dict[n.get('ID',loud)] = len(adj_ls[n.get('ID',loud)])
        self.installNodeAttr('degree',deg_dict,loud)

    
    
    ##################################################################################
    #NETWORKX HOOKUP (ONLY HAPPENS IF NETWORKX IMPORT WAS SUCCESSFUL)#################
    ##################################################################################
    
    if nx_import:
        def init_nx(self):
            self.nx_graph = nx.Graph()
            
            for n in self.nodes:
                self.nx_graph.add_node(n.get('ID'))
            
            for e in self.edges:
                self.nx_graph.add_edge(e.get('source'),e.get('target'))
            
            
            
        def nx_graphwide_analysis(self, algorithmName, n_or_e, loud=False):
            #given (as a string) the name of a graphwide analysis algorithm that returns a dictionary from Networkx, installs the results of that algorithm into the nodes or edges with attrName: 'nx_[algorithmName]'
            try:
                alg = getattr(self.nx_graph, algorithmName)
            except AttributeError:
                print("Networkx algorithm: " + str(algorithmName) + " was not found.")
            
            working_group = self.check_nore(n_or_e)
            
            result_dict = alg()
            
            if n_or_e == 'n':
                self.installNodeAttr('nx_'+algorithmName, result_dict, loud)
            else:
                self.installEdgeAttr('nx_'+algorithmName, result_dict, loud)
            
    
    
class GenericDynamicObject:
    #Parent class for nodes and edges that allows attributes that can be dynamically updated by a user(!)
    #GenericDynamicObject does this by keeping track of a set of terms called the directory (accessible using the Python inbuilt dir() function) and a dictionary which holds the value associated with each term.
    #to use this infrastructure, run newAttr() to install a new term in the directory. Only then is put() able to add a key value pair to the dictionary for that attribute.
    #to access the data after it is put(), use the accession method get()
    def __init__(self):
        self.d = {}
        self.dir_set = set()
    
    def newAttr(self, attrName,loud=False):
        #installs a new attribute in the directory for recognition by the put() and get() methods.
        #uses a set to avoid adding the same attribute multiple times (prints a warning when this happens if loud=True)
        if loud and (attrName in self.dir_set):
            print("Warning! Attempting to add a new attribute " + str(attrName) + " to " + str(self.__class__.__name__) + " " + str(self.get('ID')) + " but that attribute already exists in the directory.")
            
        self.dir_set.add(attrName)
    
    def get(self,attrName,loud=False):
        #gets a value for an existing attribute
        #if the attribute exists in the directory, but no value has been put, returns None (prints a warning if the loud argument is True)
        if attrName not in dir(self):
            raise NameError(str(self.__class__.__name__) +' object contains no attribute called ' + str(attrName))
        elif attrName not in self.d:
            if loud:
                print("Warning! Attempting to get() attribute " + str(attrName) + " value from " + str(self.__class__.__name__) + " " + str(self.get('ID')) + ". A value for this attribute has not been set. (returns None)")
            return None
        else:
            return self.d[attrName]
    
    def put(self, attrName,val,loud=False):
        #inputs a value for an existing attribute
        if attrName not in dir(self):
            raise NameError(str(self.__class__.__name__) + ' object contains no attribute called ' + str(attrName))
        else:
            self.d[attrName] = val
    
    def __dir__(self):
        #gives the directory in list form.
        #this is magic class syntax. access this method via the Python inbuilt function dir()
        #for example, if you made a node whose variable name is a, then to see the directory you would give dir(a) in python interactive.
        return set_to_list(self.dir_set)

    
    ########################
    #Non-structural methods#
    ########################
    
    def getGColor(self, color1, color2, normVal):
        gradient_vector = vector_add(scalar_mult((1-normVal),color1), scalar_mult(normVal,color2))     #in plain mathematics: (1-normVal)*color1 + (normVal)*color2 
        return vector_to_RGB(gradient_vector)
        
class Node(GenericDynamicObject):
    #Nodes are instantiated using a GenericDynamicObject initialized with an ID.
    def __init__(self, ID):
        self.d = {}
        self.dir_set = set()
        self.newAttr('ID')
        self.put('ID', ID)


class Edge(GenericDynamicObject):
    #Edges are instantiated using a GenericDynamicObject initialized with a source and target (arbitrary if undirected), and optionally a weight and direction.
    #All edges have 'source' 'target' and 'ID' in their directory by default. 
    #If the edge is not directed, 'source' and 'target' are determined by alphabetization. This also factors into the 'ID' attribute.
    #For edges, 'ID' is a string composed of the source string and the target string, delimited by a semicolon.
    def __init__(self, s, t, weight=None, directed=False):
        self.d = {}
        self.dir_set = set()
        self.newAttr('source')
        self.newAttr('target')
        if directed:
            self.put('source', s)
            self.put('target', t)
        else:      #if the edges are not directed, then the source and target are determined by alphabetical order (just for the sake of consistency)
            first = max(str(s),str(t))
            second = min(str(s),str(t))
            self.put('source',first)
            self.put('target',second)
        
        if weight:
            self.newAttr('weight')
            self.put('weight', weight)
        self.newAttr('nodes')
        self.put('nodes',set([s,t]))
        
        self.newAttr('ID')
        if directed:
            self.put('ID',str(s)+";"+str(t))
        else:      #if the edges are not directed, then the ID is the two strings, alphabetatized with a ; delimiter
            self.put('ID',first+";"+second)
