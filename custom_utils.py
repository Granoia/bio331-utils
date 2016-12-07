#customized utils
import math
import numpy
import json_utils
import graphspace_utils
import numpy as np
import getpass

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    print("matplotlib was successfully imported!")
    matplotlib_import = True
except ImportError:
    print("matplotlib was not successfully imported. matplotlib hookup methods will be inaccessible.")
    matplotlib_import = False
    
try:
    import networkx as nx
    print("networkx was successfully imported!")
    nx_import = True
except ImportError:
    print("networkx was not successfully imported. networkx hookup methods will be inacessible.")
    nx_import = False


def parse(edgefile, delimiter='\t', isDirected=False, edgeHeader=None, nodefile=None, nodeHeader=None, nodeDelimiter=None, edgeDelimiter=None):
    e_formatted = True
    n_formatted = True
    if edgeHeader:
        e_formatted = (edgeHeader[0].lower() in ['source', 's']) and (edgeHeader[1].lower() in ['target','t'])
    if nodeHeader:
        n_formatted = (nodeHeader[0].lower() == 'id')
    if not e_formatted and n_formatted:
        raise StandardError("A header given to parse() as an argument was not formatted correctly. Edgefile headers should start with 'source' followed by 'target'. Nodefile headers should start with 'ID'.")

    
    #if for some abominable reason your nodefile and edgefile have different delimiters, this next chunk will handle it
    if nodeDelimiter:
        n_delimiter = nodeDelimiter
    else:
        n_delimiter = delimiter
    
    if edgeDelimiter:
        e_delimiter = edgeDelimiter
    else:
        e_delimiter = delimiter
    
    #figures out whether the header is supplied in the arguments or needs to be fetched from the file.
    #if the header needs to be fetched from the file, this block also notes that the actual data starts on line 1 instead of line 0.
    if edgeHeader:
        edge_header = edgeHeader
        e_startline = 0
    else:
        edge_header = get_header(edgefile, e_delimiter, 'e')
        e_startline = 1

    
    
    if nodefile == None:
        nodes, edges = handle_edgefile(isDirected, edgefile, edge_header, e_delimiter, e_startline)

    else:
        throwaway, edges = handle_edgefile(isDirected, edgefile, edge_header, e_delimiter, e_startline)
        
        if nodeHeader:
            node_header = nodeHeader
            n_startline = 0
        else:
            node_header = get_header(nodefile, n_delimiter, 'n')
            n_startline = 1        
        nodes = handle_nodefile(nodefile, node_header, n_delimiter, n_startline)
    
    return Graph(nodes,edges,isDirected)

    
def get_header(file, delimiter, n_or_e):
    with open(file, 'r') as f:
        h = f.readline()
        ls = h.strip().split(delimiter)
    
    if n_or_e == 'n':
        print("No header was supplied as argument for parsing node file " + file + "\nProceeding with automatic header detection.")
        if not ls[0].lower() == 'id':
            print("Warning! get_header() sees that the first entry of the header is not called 'ID'. A properly formatted node file should have a column of node ID's first, followed optionally by other attribute columns.")
            verify = input("Please verify: Does the first column of the node file contain node ID's despite not being called 'ID'? \n('yes' to proceed, 'no' to quit): ")
            if verify.lower() == 'yes':
                ls[0] = 'ID'
            else:
                raise ValueError("Quitting.")

    
    if n_or_e == 'e':
        print("No header was supplied as argument for parsing edge file " + file + "\nProceeding with automatic header detection.")
        if len(ls) == 1:
            raise SyntaxError("\n\nThe parser has detected a header with only one column in the edge file. Edges must start with a source column and a target column. \nTip: Make sure you are supplying the correct delimiter for the input file. It defaults to tab ('\\t') but it can be supplied as an argument (e.g. parse('my_edgefile.txt',nodefile='my_nodefile.txt',delimiter=';'))")
        if (not ls[0].lower() in ['source','s']) and (not ls[1].lower() in ['target', 't']):
            print("Warning! get_header() sees that the first two entries of the header are not called 'source' and 'target' respectively. A properly formatted edge file should have a column of source nodes first, and a column of target nodes second, followed optionally by other attribute columns.")
            verify = input("Please verify: Do the first two columns of the edge file contain the nodes linked by each edge despite not being labelled 'source' and 'target'?\n('yes' to proceed, 'no' to quit): ")
            if verify.lower() == 'yes':
                ls[0] = 'source'
                ls[1] = 'target'
            else:
                raise ValueError("Quitting.")
    print(ls)
    return ls

def handle_edgefile(isDirected, edgefile, header, delimiter, startline):
    header_numtypes = find_header_numtypes(edgefile, header, delimiter, startline)
    edges = []
    nodes = []
    node_set = set()
    with open(edgefile, 'r') as ef:
        i = 0
        while i<startline:
            ef.readline()
            i+=1
        for line in ef.readlines():
            ls = line.strip().split(delimiter)
            if len(ls) != len(header):
                print("Warning! While parsing " + edgefile +", the following line did not match the number of entries given by the header. Thus it was not included in the Graph.\n" + line)
                continue
            node1 = handle_type(ls[0], header_numtypes[0])
            node2 = handle_type(ls[1], header_numtypes[1])
            node_set.add(node1)
            node_set.add(node2)
            new = Edge(node1, node2, directed=isDirected)
            edges.append(new)
            for i in range(2,len(header)):
                new.newAttr(header[i])
                new.put(header[i], handle_type(ls[i], header_numtypes[i]))
    
    for n in node_set:
        new_node = Node(n)
        nodes.append(new_node)
    
    return nodes, edges
    
    
    
    

def check_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def check_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def handle_nodefile(nodefile, node_header, delimiter='\t', startline=0):
    nodes = []
    header_numtypes = find_header_numtypes(nodefile, node_header, delimiter, startline)
    with open(nodefile,'r') as f:
        i = 0
        while i < startline:     #scroll to the start of the data
            f.readline()
            i+=1
        for line in f.readlines():
            ls = line.strip().split(delimiter)
            if len(ls) != len(node_header):
                raise IndexError("Error while reading " + nodefile + ". Line with ID " + ls[0] + " did not have the correct number of data entries according to the header.")
            new = Node(handle_type(ls[0], header_numtypes[0]))
            nodes.append(new)
            for i in range(1,len(node_header)):
                new.newAttr(node_header[i])
                new.put(node_header[i],handle_type(ls[i], header_numtypes[i]))
    return nodes

def find_header_numtypes(file, header, delimiter='\t', startline=0):
    col_dict = {}
    for e in header:
        col_dict[e] = []
    
    with open(file, 'r') as f:
        i = 0
        while i < startline:
            f.readline()
            i += 1
        for line in f.readlines():
            ls = line.strip().split(delimiter)
            for i in range(len(ls)):
                col_dict[header[i]].append(ls[i])
    
    header_numtypes = []
    for h in header:
        t = determine_column_numtype(col_dict[h], h)
        header_numtypes.append(t)
    return header_numtypes


def determine_column_numtype(col, head):
    if head.lower() in ['id','source','s','target','t']:
        #for columns containing node ID's, we want to be strict with our typing.
        #this ensures that if any of the node ID's are not numerical, the column is given the label string
        all_numeric = True
        for e in col:
            if not check_float(e):
                return 'string'
            
    else:
        #for other columns I wanted to allow the possibility of putting multiple types in a given attribute
        #the only actual ambiguity this creates is whether to process numbers without decimals as ints or floats
        #this code will label any column containing floats as 'float' so that numbers without decimals are processed as floats in those columns
        no_nums = True

        for e in col:
            if check_float(e) and not check_int(e):
                return 'float'
            elif check_int(e):
                no_nums = False
            
        if no_nums:
            return None
        else:
            return 'int'


def handle_type(entry, numtype):
    if numtype == 'string':
        return entry
    
    if entry == 'None':
        return None
    elif entry == "True":
        return True
    elif entry == "False":
        return False
    elif numtype=='int':
        if check_int(entry):
            return int(entry)
    elif numtype=='float':
        if check_float(entry):
            return float(entry)
    else:
        return entry
    
    
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
    for e in vector:
        if math.isnan(e):
            return None

    return '#{:02x}{:02x}{:02x}'.format(int(vector[0]),int(vector[1]),int(vector[2]))

def getGColor(color1, color2, normVal):
    if math.isnan(normVal):
        return None
    gradient_vector = vector_add(scalar_mult((1-normVal),color1), scalar_mult(normVal,color2))     #in plain mathematics: (1-normVal)*color1 + (normVal)*color2 
    return vector_to_RGB(gradient_vector)


def quick_plot(d):
    data = []
    for k in d:
        data.append(d[k])
    
    values, base = np.histogram(data, bins=40)
    
    cumulative = np.cumsum(values)
    
    plt.plot(base[:-1], cumulative, c='blue')
    
    plt.savefig('testplot.png')
    
def parse_RGB_input(user_query):
    s = input(user_query)
    ls = s.strip('[]()').split(',')
    if len(ls) != 3:
        raise TypeError('The given input was not an RGB vector. Please supply an RGB vector of the form [R, G, B] e.g. [255, 17, 134]')
    RGB = []
    for n in ls:
        RGB.append(int(n))
        if int(n) < 0 or 255 < int(n):
            raise ValueError('The given value ' + n + ' was not an appropriate RGB value. RGB values must be in the range [0,255].')
    
    return RGB  

def restricted_input(prompt, ls=None,case_sensitive=False):
    if ls == None:
        return input(prompt)
    
    if case_sensitive:
        candidate = input(prompt)
    else:
        candidate = input(prompt).lower()
    if candidate not in ls:
        raise NameError("The given input was not found in the list of accepted inputs. Please enter one of the following: " + str(ls))
    else:
        return candidate
    
    
    
shape_ls = ["rectangle", "ellipse", "triangle", "pentagon", "hexagon", "heptagon", "octagon", "star", "diamond", "vee", "rhomboid", "roundrectangle"]        
def pick_shape(n):
    if n == None:
        return None
    if n > 11:
        raise ValueError("Too many discrete groups to visualize by shape (GraphSpace has 12 unique node shapes)")
    else:
        return shape_ls[n]
    
def check_key(s):
    #helper that checks if a string has leading and trailing double underscores e.g. '__line_width__'
    if len(s) > 4 and (s[:2] == '__' and s[-2:] == '__'):
        return True
    else:
        return False

def check_control_str(given, want):
    #helper for display
        if given == 1:
            return True
        if given == want:
            return True
        else:
            return False
    
class Graph:
    """
    This class will provide all the planned functionality. The basic idea is to be able to scale a given visual attribute (on graphspace) by a given data attribute as easily as possible without loss of customization power.
    We do this by keeping a directory of data attributes which can be updated by the user on the fly. (Though the directory kept in the Graph object is mostly superficial at the moment. The Node class does all of the heavy lifting when it comes to actually enforcing the directory rules.)
    Additionally, a basic adjacency list method is included if a user doesn't want to deal with the hassle of learning my framework.
    Now has a working method normNodeAttr() that returns a normalized dictionary for any node attribute. Pretty snazzy.
    """
    #####################
    #user methods########
    #####################
    #future note for reorganization - user methods should include the following functions:
    #visualize()
    #display()
    #default()
    #nodeInstall()
    #edgeInstall() future note: these should both make it so that the user can't add an attribute beginning and ending with '__' (except maybe using an advanced options boolean argument?)
    #edgeGet()
    #nodeGet()
    #remove()
    #export()
    #upload()
    
    #installNodeAttr and installEdgeAttr should be here
    #removeNodeAttr and removeEdgeAttr should be here
    
    def nodeGet(self, attrName):
        return self.getNodeAttr(attrName)
    
    def edgeGet(self, attrName):
        return self.getEdgeAttr(attrName)
    
    def nodeInstall(self, attrName, valueDict):
        if check_key(attrName):
            raise NameError("Please do not use leading and trailing double underscores (e.g. '__my_attribute__') in your attribute names.")
        else:
            self.installNodeAttr(attrName, valueDict)
    
    def edgeInstall(self, attrName, valueDict):
        if check_key(attrName):
            raise NameError("Please do not use leading and trailing double underscores (e.g. '__my_attribute__') in your attribute names.")
        self.installEdgeAttr(attrName, valueDict)
    
    def display(self, c=1):
        if check_control_str(c,'data'):
            print("Directory of Node Data Attributes:\n"+str(self.node_dir)+"\n\n")
            print("Directory of Edge Data Attributes:\n"+str(self.edge_dir)+"\n\n")
        
        if check_control_str(c, 1):
            print("####################################################")
            print("####################################################\n\n")
        
        if check_control_str(c, 'visual'):
            print("Directory of User-Modified Node GraphSpace Visual Attributes:\n"+str(self.GSnodeDir)+"\n\n")
            print("Directory of User-Modified Edge GraphSpace Visual Attributes:\n"+str(self.GSedgeDir)+"\n\n")
        
        if check_control_str(c,1):
            print("####################################################")
            print("####################################################\n\n")
        
        if check_control_str(c,'default'):
            print("Default Node GraphSpace Visual Attributes:\n"+str(self.GSnodeDefaults)+"\n\n")
            print("Default Edge GraphSpace Visual Attributes:\n"+str(self.GSedgeDefaults)+"\n\n")
        
        if c == 'nodes':
            for n in self.nodes:
                print(str(n))
        
        if c == 'edges':
            for e in self.edges:
                print(str(e))
            
    
    def remove(self, attrName):
        if attrName in (self.node_dir | self.edge_dir) and attrName in (self.GSnodeDir | self.GSedgeDir):
            d_or_v = restricted_input("Do you mean the data attribute or the visual attribute? Please enter one of the following:\ndata\tvisual\n>>> ",['data','visual'])
        
        if attrName in self.node_dir and attrName in self.edge_dir:
            n_or_e = restricted_input("Do you mean the node attribute or the edge attribute? Please enter one of the following:\nnode\tedge\n>>> ",['node','edge'])
        elif attrName in self.node_dir:
            n_or_e = 'node'
        elif attrName in self.edge_dir:
            n_or_e = 'edge'
        elif '__' + attrName + '__' in self.node_dir:
            n_or_e = 'node'
        elif '__' + attrName + '__' in self.edge_dir:
            n_or_e = 'edge'
        else:
            return NameError("The given attribute '" + str(attrName) + "' was not found in the Graph directory.")
        
        if n_or_e == 'node':
            n_or_e = 'n'
        else:
            n_or_e = 'e'
        
        if check_key(attrName):
            #if the input string was a GS_key, e.g. '__line_width__', then we should remove both the GS visual attribute and its corresponding data attribute
            self.removeGS(attrName[2:-2])
            self.removeAttr(attrName, n_or_e)
            return
        
        elif attrName in (self.GSnodeDir | self.GSedgeDir):
            #if the input string was a GS attr, e.g. 'line_width', then we should remove both the GS visual attribute and its corresponding data attribute
            if d_or_v == 'data':
                #unless for some reason the user made a data attribute with the same name as a visual attribute, in which case we just want to remove the data attribute
                #a situation for which I am accommodating because I'm a masochist, apparently
                pass
            else:
                self.removeGS(attrName)
                self.removeAttr('__'+attrName+'__', n_or_e)
                return
        
        #otherwise it's just a data attribute so we remove it.
        self.removeAttr(attrName, n_or_e)
        return    
    
    def removeGS(self, GS_attr):
        if GS_attr not in (self.GSnodeDir | self.GSedgeDir):
            raise NameError("The given visual attribute '" + str(GS_attr) + "' was not found in the directory of modified visual attributes.")
        elif GS_attr in self.GSnodeDir:
            self.GSnodeDir = self.GSnodeDir - set([str(GS_attr)])
        elif GS_attr in self.GSedgeDir:
            self.GSedgeDir = self.GSedgeDir - set([str(GS_attr)])
    
    def removeAttr(self, attrName, n_or_e):
        if attrName not in (self.node_dir | self.edge_dir):
            raise NameError("The given attribute '" + str(attrName) + "' was not found in the Graph directory.")
        elif n_or_e == 'n':
            self.node_dir = self.node_dir - set([attrName])
            for n in self.nodes:
                n.delete(attrName)
        elif n_or_e == 'e':
            self.edge_dir = self.edge_dir - set([attrName])
            for e in self.edges:
                e.delete(attrName)
        else:
            raise NameError("removeAttr() argument n_or_e must be set to either 'n' or 'e'")
        
    def default(self, GS_attr=None, value=None):
        if GS_attr == None and value==None:
            self.display('default')
            print("Input default(<GS_attr>,<new default value>) to change the default value of any listed visual attribute.")
        else:
            self.change_default(GS_attr, value)
    
    def change_default(self, GS_attr, value):
        if GS_attr not in (list(self.GSnodeDefaults.keys()) + list(self.GSedgeDefaults.keys())):
            raise NameError("You can't set '" + GS_attr + "' as a default attribute. Default attributes you can set are:\nNodes:\n" + str(list(self.GSnodeDefaults.keys())) + "\nEdges:\n" + str(list(self.GSedgeDefaults.keys())))
        elif GS_attr in list(self.GSnodeDefaults.keys()):
            self.GSnodeDefaults[GS_attr] = value
        else:
            self.GSedgeDefaults[GS_attr] = value
    
    def upload(self):
        self.uploadGraph()
    
    
    def visualize(self, attrName):
        if attrName in self.node_dir and attrName in self.edge_dir:
            n_or_e = input('Do you mean ' + attrName + ' for nodes or edges? (input \'n\' or \'e\'): ')
        elif attrName in self.node_dir:
            n_or_e = 'n'
        elif attrName in self.edge_dir:
            n_or_e = 'e'
        else:
            raise NameError("The given attribute was not found in either of the data directories. (use my_graph.display('data') to print the data directories if you want to see what's in them)")
        
        if n_or_e == 'n':
            c_or_d = input('Is the attribute to be visualized continuous or discrete: ').lower()
            if c_or_d == 'continuous':
                self.visualize_c(attrName)
            elif c_or_d == 'discrete':
                self.visualize_d(attrName)
            else:
                raise NameError("Your input was not recognized. Please enter one of the following: \ncontinuous \tdiscrete")
        
        else:
            self.edge_visualize(attrName)

    
    def export(self, edgefile=None, nodefile=None, delimiter='\t'):
        if edgefile == None:
            edgefile = input('Outprefix for edge file: ') + '.txt'
        
        if nodefile == None:
            nodefile = input('Outprefix for node file: ') + '.txt'
        
        with open(edgefile, 'w') as ef:
            edge_header = self.make_header('e')
            s = ""
            for h in edge_header:
                s+= str(h) + delimiter
            s = s[:-len(delimiter)] + '\n'
            ef.write(s)
            
            for e in self.edges:
                s = ""
                for h in edge_header:
                    entry = e.get(h)
                    s+= str(entry) + delimiter
                s = s[:-len(delimiter)] + '\n'
                ef.write(s)
        
        with open(nodefile, 'w') as nf:
            node_header = self.make_header('n')
            s = ""
            for h in node_header:
                s += str(h) + delimiter
            s = s[:-len(delimiter)] + '\n'
            nf.write(s)
            
            for n in self.nodes:
                s = ""
                for h in node_header:
                    entry = n.get(h)
                    s+= str(entry) + delimiter
                s = s[:-len(delimiter)] + '\n'
                nf.write(s)
        return


    #export helper method
    def make_header(self, n_or_e):
        header = []
        if n_or_e == 'e':
            header.append('source')
            header.append('target')
            for h in self.edge_dir:
                if h.lower() not in ['source', 'target', 'id']:
                    header.append(str(h))
        
        elif n_or_e == 'n':
            header.append('ID')
            for h in self.node_dir:
                if h.lower() != 'id':
                    header.append(str(h))
        
        else:
            raise ValueError
        
        return header


    ###############################
    #visualize helper methods######
    ###############################

    def edge_visualize(self, attrName):
        c_or_d = input('Is the attribute to be visualized continuous or discrete: ').lower()
        if c_or_d == 'continuous':
            self.edge_c(attrName)
        elif c_or_d == 'discrete':
            self.edge_d(attrName)
        else:
            raise NameError("Your input was not recognized. Please enter one of the following: \ncontinuous \tdiscrete")
    
    def edge_c(self, attrName):
        GS_attr = input('What GraphSpace visual attribute would you like to visualize by? Please enter one of the following: \nwidth \tline_color\n>>> ').lower()
        if GS_attr == 'width':
            self.scaleEdgeWidth(attrName)
        elif GS_attr == 'line_color':
            color1 = parse_RGB_input('Gradient Color 1 (input as an RGB vector e.g. [255,0,0]): ')
            color2 = parse_RGB_input('Gradient Color 2 (input as an RGB vector e.g. [0,255,0]): ')
            self.scaleGradient(attrName, color1, color2, GS_attr, n_or_e='e')

    def scaleEdgeWidth(self, attrName):
        max_size = int(input("Maximum edge width: "))
        min_size = 2
        normDict = self.normEdgeAttr(attrName)
        if max_size < min_size:
            max_size = min_size
        
        diff = max_size - min_size
        
        size_dict = {}
        
        for e in normDict:
            if math.isnan(normDict[e]):
                size_dict[e] = None
            else:
                size_dict[e] = min_size + diff*normDict[e] 
        self.installEdgeAttr('__width__',size_dict)
        self.GSedgeAttrInstall('width')
            
    def edge_d(self, attrName):
        GS_attr = input('What GraphSpace visual attribute would you like to visualize by? Please enter one of the following: \nline_color \tline_style\n>>> ').lower()
        if GS_attr == 'line_color':
            self.discrete_color(attrName, 'line_color', 'e')
        elif GS_attr == 'line_style':
            attr_dict, group_dict = self.discretizeAttr(attrName,n_or_e='e')
            GS_dict = {}
            for g in group_dict:
                if g == None:
                    continue
                style = input("Line style for group '" + str(g) + "' (choose from [solid, dotted, dashed]) (enter 'quit' to cancel): ")
                if style == 'quit':
                    return
                if style not in ['solid', 'dotted', 'dashed']:
                    raise NameError("Please choose from one of the styles on the list.")
                for e in group_dict[g]:
                    GS_dict[e] = style 
                    
            self.installEdgeAttr('__line_style__', GS_dict)
            self.GSedgeAttrInstall('line_style')
        else:
            raise NameError("The GraphSpace attribute you entered was not recognized. Please enter one of the following: \nline_color \tline_style \t shape")
    
    #continuous
    def visualize_c(self, attrName):
        GS_attr = input('What GraphSpace visual attribute would you like to visualize by? Please enter one of the following: \nbackground_color \tborder_color \tbackground_blacken \tsize \n>>> ').lower()
        if GS_attr in ["background_color", "border_color", "background_blacken"]:
            self.continuous_color(attrName, GS_attr)
        elif GS_attr == 'size':
            self.scaleBySize(attrName)
        else:
            raise NameError("The GraphSpace attribute you entered was not recognized. Please enter one of the following: \nbackground_color \tborder_color \tbackground_blacken \tsize")

    def continuous_color(self, attrName, GS_attr):
        if GS_attr in ["background_color", "border_color"]:
            color1 = parse_RGB_input('Gradient Color 1 (input as an RGB vector e.g. [255,0,0]): ')
            color2 = parse_RGB_input('Gradient Color 2 (input as an RGB vector e.g. [0,255,0]): ')
            self.scaleGradient(attrName, color1, color2, GS_attr)
        
        elif GS_attr == "background_blacken":
            self.scaleBlacken(attrName)
            

    def scaleGradient(self, attrName, color1, color2, GS_attr, n_or_e='n', loud=False):
        color_dict = {}
        working_group = self.check_nore(n_or_e)
        
        normDict = self.normByAttr(attrName, n_or_e, loud)
        
        for x in working_group:
            color_dict[x.get('ID',loud)] = getGColor(color1,color2,normDict[x.get('ID',loud)])
        
        if n_or_e == 'n':
            if '__' + GS_attr + '__' not in self.node_dir:
                self.installNodeAttr('__' + GS_attr + '__', color_dict, loud)
            else:
                self.putNodeAttrs('__' + GS_attr + '__', color_dict, loud)
            self.GSnodeAttrInstall(GS_attr, loud)
        
        elif n_or_e == 'e':
            if '__' + GS_attr + '__' not in self.edge_dir:
                self.installEdgeAttr('__' + GS_attr + '__', color_dict, loud)
            else:
                self.putEdgeAttrs('__' + GS_attr + '__', color_dict, loud)
            self.GSedgeAttrInstall(GS_attr, loud)

    
    def scaleBlacken(self, attrName):
        #not tested yet
        b_w_both = restricted_input("Would you like to blacken, whiten, or both? Please enter one of the following: \nblacken\twhiten\tboth\n>>> ",['blacken','whiten','both']).lower()
        if b_w_both not in ['blacken','whiten','both']:
            raise NameError("Please enter blacken, whiten, or both.")
        
        normDict = self.normByAttr(attrName, 'n')
        
        
        if b_w_both == 'blacken':
            i = restricted_input("Should lower values for attribute " + str(attrName) + " be more black or less black? Please input: \n1 for more black\t2 for less black\n>>> ",['1','2'])
            if i == 1:
                for k in normDict:
                    normDict[k] = (normDict[k] - 1) * -1
            else:
                #then the normalized dictionary in its current form is appropriate, so do nothing
                pass
                
            
        elif b_w_both == 'whiten':
            i = restricted_input("Should lower values for attribute " + str(attrName) + " be more white or less white? Please input: \n1 for more white\t2 for less white\n>>> ",['1','2'])
            if i == 1:
                for k in normDict:
                    normDict[k] = normDict[k] - 1
            else:
                for k in normDict:
                    normDict[k] = normDict[k] * -1
            
        elif b_w_both == 'both':
            i = restricted_input("Should lower values for attribute " + str(attrName) + " be black or white? Please input one of the following:\nblack\t\white\n>>> ",['black','white'])
            if i == 'white':
                for k in normDict:
                    normDict[k] = (normDict[k] - 0.5) * 2
            else:
                for k in normDict:
                    normDict[k] = ((normDict[k] * -1) + 0.5) * 2
        
        self.installNodeAttr('__background_blacken__', normDict)
        self.GSnodeAttrInstall('background_blacken')
        
        
            
    def scaleBySize(self, attrName):
        max_size = int(input("Maximum node size: "))
        min_size = int(input("Minimum node size: "))
        diff = max_size - min_size
        norm_dict = self.normNodeAttr(attrName)
        
        size_dict = {}
        
        for n in norm_dict:
            size_dict[n] = min_size + (diff * norm_dict[n])
        
        self.installNodeAttr('__height__', size_dict)
        self.installNodeAttr('__width__', size_dict)
        self.GSnodeAttrInstall('height')
        self.GSnodeAttrInstall('width')    
    
    
    #discrete
    
    def visualize_d(self,attrName):
        GS_attr = input('What GraphSpace visual attribute would you like to visualize by? Please enter one of the following: \nbackground_color \tborder_color \tshape \n>>> ').lower()
        if GS_attr in ["background_color", "border_color"]:
            self.discrete_color(attrName, GS_attr)
        elif GS_attr == 'shape':
            self.discrete_shape(attrName)
        else:
            raise NameError("The GraphSpace attribute you entered was not recognized. Please enter one of the following: \nbackground_color \tborder_color \t shape")    
    
    
    def discrete_color(self, attrName, GS_attr, n_or_e='n'):
        m_or_a = input("Manual or Automatic color picking scheme: ")
        working_group = self.check_nore(n_or_e)
        
        disc_dict, group_dict = self.discretizeAttr(attrName,n_or_e)
        GS_dict = {}
        
        if m_or_a.lower() == 'automatic':
            for x in working_group:
                GS_dict[x.get('ID')] = discrete_coloring(disc_dict[x.get('ID')])
        
        elif m_or_a.lower() == 'manual':
            for g in group_dict:
                if g == None:
                    continue
                color = parse_RGB_input("Color for group \'" + str(g) + "\' (RGB vector e.g. [255,0,0]) (type 'quit' to cancel): ")
                if color == 'quit':
                    return
                for x in group_dict[g]:
                    GS_dict[x] = vector_to_RGB(color)
        
        else:
            raise NameError("Please enter either manual or automatic.")
        
        if n_or_e == 'n':
            self.installNodeAttr('__'+GS_attr+'__', GS_dict)
            self.GSnodeAttrInstall(GS_attr)
        elif n_or_e == 'e':
            self.installEdgeAttr('__'+GS_attr+'__', GS_dict)
            self.GSedgeAttrInstall(GS_attr)
    
    def discrete_shape(self, attrName):
        m_or_a = input("Manual or Automatic shape picking: ")
        
        attr_dict, group_dict = self.discretizeAttr(attrName)
        GS_dict = {}
        
        if m_or_a.lower() == 'automatic':
            for n in self.nodes:
                GS_dict[n.get('ID')] = pick_shape(attr_dict[n.get('ID')])
        
        elif m_or_a.lower() == 'manual':
            for g in group_dict:
                if g == None:
                    continue
                shape = input("Shape for group '" + str(g) + "' (choose from " + str(shape_ls) + ") (enter 'quit' to cancel): ")
                if shape == 'quit':
                    return
                if shape not in shape_ls:
                    raise NameError("Please choose from one of the shapes on the list.")
                for n in group_dict[g]:
                    GS_dict[n] = shape
        else:
            raise NameError("Please enter either manual or automatic.")
        
        self.installNodeAttr('__shape__', GS_dict)
        self.GSnodeAttrInstall('shape')
    
    ########################################################
    #INFRASTRUCTURE METHODS (not for user)##################
    ########################################################
    
    def __init__(self, nodes, edges, isDirected):
        self.nodes = nodes
        self.edges = edges
        self.isDirected = isDirected
        
        self.init_dirs()
        
        self.GSnodeAttrs = self.initGSnodeAttrs()
        self.GSedgeAttrs = self.initGSedgeAttrs()
        
        self.GSnodeDir = set()
        self.GSedgeDir = set()
        self.init_GS_dirs()
        
        if isDirected:
            t_arrow_shape = 'triangle'
        else:
            t_arrow_shape = 'none'
        
        self.GSnodeDefaults = dict([('background_color','#ffff66'),('height',60),('width',60),('shape','ellipse'),('background_blacken',0),('background_opacity',1),('border_width',3),('border_style','solid'),('border_color','black'),('border_opacity',1),('color','#000000'),('text_transform','none'),('text_halign','center'),('text_valign','center')])
        self.GSedgeDefaults = dict([('line_color','#000000'),('line_style','solid'),('mid_source_arrow_color','#000000'),('mid_source_arrow_shape','none'),('mid_source_arrow_fill','filled'),('source_arrow_color','#000000'),('source_arrow_shape','none'),('source_arrow_fill','filled'),('target_arrow_color','#000000'),('target_arrow_shape',t_arrow_shape),('target_arrow_fill','filled'),('mid_target_arrow_color','#000000'),('mid_target_arrow_shape','none'),('mid_target_arrow_fill','filled')])
        

        

    def init_dirs(self):
        self.edge_dir = set(dir(self.edges[0]))
        self.node_dir = set(dir(self.nodes[0]))

    def init_GS_dirs(self):
        for s in self.edge_dir:
            if len(s) >= 2 and s[0:2] == '__' and s[-2:] == '__':
                self.GSedgeDir.add(s[2:-2])
        for s in self.node_dir:
            if len(s) >= 2 and s[0:2] == '__' and s[-2:] == '__':
                self.GSnodeDir.add(s[2:-2])
        self.GSattrsUpdate()


    
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
    
    def newNodeAttr(self,attrName,loud=False):
        #helper function for installNodeAttr
        #installs attrName in the directory of each node in the graph.
        for n in self.nodes:
            n.newAttr(attrName,loud)
        self.node_dir.add(attrName)
    
    
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
    
    def newEdgeAttr(self,attrName,loud=False):
        for e in self.edges:
            e.newAttr(attrName,loud)
        self.edge_dir.add(attrName)
    
    
    
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
            try:
                x.put(attrName, attrDict[x.get('ID')])
            except KeyError:
                #if attrDict doesn't mention one of the objects in the working group, we want it to leave already set values the way they are, and have not yet set values be set to None
                if attrName in x.d.keys():   #this violates an abstraction barrier but it's okay just this once right?
                    pass
                else:
                    x.put(attrName, None)
                if loud:
                    raise UserWarning("The given attribute dictionary did not contain " + str(x.__class__.__name__) + " " + str(x.get('ID')) + ". If attribute " + str(attrName) + " was already set, it was left alone. If it wasn't set, it was set to None.")
        
    def putNodeAttrs(self, attrName, attrDict, loud=False):
        self.putAttrs(attrName,attrDict,'n',loud)
    
    def putEdgeAttrs(self, attrName, attrDict, loud=False):
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
        d = {}
        working_group = self.check_nore(n_or_e)
        
        for x in working_group:
            d[x.get('ID')] = float('nan')
        
        all_bools = True
        for x in working_group:
            if x.get(attrName) not in [True, False, None]:
                all_bools = False
        if all_bools:
            for x in working_group:
                if x.get(attrName) == True:
                    d[x.get('ID')] = 1
                elif x.get(attrName) == False:
                    d[x.get('ID')] = 0
                else:
                    d[x.get('ID')] = float('nan')
                
                    
        
        def key_func(x):
            if type(x.get(attrName)) not in [float, int]:
                return float('nan')
            else:
                return x.get(attrName)
        
        nums = [key_func(x) for x in working_group]
        
        biggest = numpy.nanmax(nums)
        smallest = numpy.nanmin(nums)
        
        def normalizer(v, my_max, my_min):
            if check_float(v):
                norm = (v - my_min) / float(my_max - my_min)
            else:
                norm = float('nan')
            return norm
        
        for x in working_group:
            if x.get(attrName,loud) != None:
                d[x.get('ID')] = normalizer(x.get(attrName), biggest, smallest)
        
        return d

    
    def discretizeAttr(self, attrName, n_or_e='n'):
        working_group = self.check_nore(n_or_e)
        group_dict = {} #keys are categories, values are lists of nodes
        attr_dict = {} #keys are nodes, values are categories
        for x in working_group:
            current = x.get(attrName)
            if current not in group_dict:
                group_dict[current] = [x.get('ID')]
            else:
                group_dict[current].append(x.get('ID'))
        i = 0
        for g in group_dict:
            if g == None:
                for x in group_dict[g]:
                    attr_dict[x] = None
            else:
                for x in group_dict[g]:
                    attr_dict[x] = i
                i += 1
        return attr_dict, group_dict    

    def set_to_boolDict(self,s):
        #many graph analysis algorithms return a set of nodes instead of a dictionary, but dictionaries fit better into the framework of this package
        #this method converts that set to a dictionary of booleans that details which nodes are in the set and which aren't
        node_d = {}
        edge_d = {}
        for n in self.nodes:
            node_d[n.get('ID')] = False
        
        for e in self.edges:
            edge_d[e.get('ID')] = False
            
        for item in s:
            if item in node_d:
                node_d[item] = True
        
        return node_d

    def get_adj_ls(self):
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
        
    def defaultizeNodes(self):
        to_be_added = set(self.GSnodeDefaults.keys()) - self.GSnodeDir
        to_be_looked = self.GSnodeDir
        d = dict(self.GSnodeAttrs)
        
        for GS_attr in to_be_added:
            for n in self.nodes:
                d[n.get('ID')][GS_attr] = self.GSnodeDefaults[GS_attr]
        
        for GS_attr in to_be_looked:
            if d[n.get('ID')][GS_attr] == None:
                d[n.get('ID')][GS_attr] = self.GSnodeDefaults[GS_attr]
        
        return d
    
    def defaultizeEdges(self):
        to_be_added = set(self.GSedgeDefaults.keys()) - self.GSedgeDir
        to_be_looked = self.GSedgeDir
        d = dict(self.GSedgeAttrs)
        
        for GS_attr in to_be_added:
            for e in self.edges:
                d[e.get('source')][e.get('target')][GS_attr] = self.GSedgeDefaults[GS_attr]
        
        for GS_attr in to_be_looked:
            for e in self.edges:
                if d[e.get('source')][e.get('target')][GS_attr] == None:
                    d[e.get('source')][e.get('target')][GS_attr] = self.GSedgeDefaults[GS_attr]
        
        return d
    

    
    def uploadGraph(self, title=None, graphID=None, desc=None, tags=None):
        self.GSattrsUpdate()
        json_filename = 'graphspace_upload.json'
        user = input("Graphspace username: ")
        pw = getpass.getpass("Graphspace password: ")
        if title == None:
            title = input("Graph title: ")
        if graphID == None:
            graphID = input("Graph ID: ")
        if desc == None:
            desc = input("Graph description: ")
        if tags == None:
            tag_str = input("Graph tags (separated by comma): ")
            tags = tag_str.strip().split(',')
        
        if 'quit' in [title,graphID,desc,tag_str]:
            return
        
        n_ls = [x.get('ID') for x in self.nodes]
        
        e_ls = []
        for e in self.edges:
            e_ls.append([e.get('source'), e.get('target')])
        
        GS_nodes = self.defaultizeNodes()
        GS_edges = self.defaultizeEdges()
        
        try:
            data = json_utils.make_json_data(n_ls, e_ls, GS_nodes, GS_edges, title, desc, tags)
            json_utils.write_json(data,json_filename)
            graphspace_utils.postGraph(graphID, json_filename, user, pw)
        except Exception as e:
            print(e)
            
        
    ###############################################################
    #SCALABILITY HELPER METHODS (not for user)#####################
    ###############################################################
    
    #except this one is a user method idk
    def scaleGradientByNodeAttr(self, color1, color2, attrName, loud=False):
        normDict = self.normNodeAttr(attrName,loud)
        self.getNodeGradient(color1,color2,normDict,loud)
    
    def getNodeGradient(self, color1, color2, normDict, loud=False):
        color_dict = {}
        for n in self.nodes:
            color_dict[n.get('ID',loud)] = getGColor(color1,color2,normDict[n.get('ID',loud)]) #not sure how this handles None or nan yet, I'll figure out those corner cases later on.
        
        if '__background_color__' not in self.node_dir:
            self.installNodeAttr('__background_color__',color_dict,loud)
        else:
            self.putNodeAttrs('__background_color__',color_dict,loud)
        self.GSnodeAttrInstall('background_color',loud)
        
    
    ##################################################
    #GRAPH ANALYSIS METHODS###########################
    ##################################################
    
    def getNodeDegree(self,loud=False):
        adj_ls = self.get_adj_ls()
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
                alg = getattr(nx, algorithmName)
                result_dict = alg(self.nx_graph)
            except AttributeError:
                print("Networkx algorithm: " + str(algorithmName) + " was not found.")
            
            working_group = self.check_nore(n_or_e)
            
            
            
            if n_or_e == 'n':
                self.installNodeAttr('nx_'+algorithmName, result_dict, loud)
            else:
                self.installEdgeAttr('nx_'+algorithmName, result_dict, loud)

                
    

    
    #####################################################################################
    #MATPLOTLIB HOOKUP (ONLY HAPPENS IF MATPLOTLIB IMPORT WAS SUCCESSFUL)################
    #####################################################################################
    
    if matplotlib_import:
        def plot_histogra(self, attrName, loud=False):
            pass
            
    
    
    
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
    
    def delete(self, attrName):
        self.dir_set = self.dir_set - set([attrName])
        self.d.pop(attrName)
    
    def __dir__(self):
        #gives the directory in list form.
        #this is magic class syntax. access this method via the Python inbuilt function dir()
        #for example, if you made a node whose variable name is a, then to see the directory you would give dir(a) in python interactive.
        return set_to_list(self.dir_set)

        
class Node(GenericDynamicObject):
    #Nodes are instantiated using a GenericDynamicObject initialized with an ID.
    def __init__(self, ID):
        self.d = {}
        self.dir_set = set()
        self.newAttr('ID')
        self.put('ID', ID)

    def __str__(self):
        s = str(self.get('ID')) + ': ' + str(self.d)
        return s

class Edge(GenericDynamicObject):
    #Edges are instantiated using a GenericDynamicObject initialized with a source and target (arbitrary if undirected), and optionally a weight and direction.
    #All edges have 'source' 'target' and 'ID' in their directory by default. 
    #If the edge is not directed, 'source' and 'target' are determined by alphabetization. This also factors into the 'ID' attribute.
    #For edges, 'ID' is a string composed of the source string and the target string, delimited by '_;_'.
    def __init__(self, s, t, directed=False):
        self.d = {}
        self.dir_set = set()
        self.newAttr('source')
        self.newAttr('target')
        self.newAttr('ID')
        
        if directed:
            self.put('source', s)
            self.put('target', t)
            self.put('ID',str(s)+"_;_"+str(t))
            
        else:      #if the edges are not directed, then the source and target are determined by alphabetical order (just for the sake of consistency)
            if max(str(s),str(t)) == str(s):
                first = s
                second = t
            else:
                first = t
                second = s
            self.put('source',first)
            self.put('target',second)
            self.put('ID',str(first)+"_;_"+str(second))
    
    def __str__(self):
        s = '(' + str(self.get('source')) + ', ' + str(self.get('target')) + '): ' + str(self.d)
        return s


def discrete_coloring(n):
    if n == None:
        return None
    if n > 1023:
        raise ValueError
    color_ls = ["#FFFF00", "#1CE6FF", "#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059",
        "#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43", "#8FB0FF", "#997D87",
        "#5A0007", "#809693", "#FEFFE6", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53", "#FF2F80",
        "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
        "#DDEFFF", "#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F",
        "#372101", "#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99", "#001E09",
        "#00489C", "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
        "#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",
        "#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81",
        "#575329", "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00",
        "#7900D7", "#A77500", "#6367A9", "#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700",
        "#549E79", "#FFF69F", "#201625", "#72418F", "#BC23FF", "#99ADC0", "#3A2465", "#922329",
        "#5B4534", "#FDE8DC", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
        "#83AB58", "#001C1E", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66", "#222800",
        "#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#1E0200", "#5B4E51",
        "#C895C5", "#320033", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94", "#7ED379", "#012C58",
        "#7A7BFF", "#D68E01", "#353339", "#78AFA1", "#FEB2C6", "#75797C", "#837393", "#943A4D",
        "#B5F4FF", "#D2DCD5", "#9556BD", "#6A714A", "#001325", "#02525F", "#0AA3F7", "#E98176",
        "#DBD5DD", "#5EBCD1", "#3D4F44", "#7E6405", "#02684E", "#962B75", "#8D8546", "#9695C5",
        "#E773CE", "#D86A78", "#3E89BE", "#CA834E", "#518A87", "#5B113C", "#55813B", "#E704C4",
        "#00005F", "#A97399", "#4B8160", "#59738A", "#FF5DA7", "#F7C9BF", "#643127", "#513A01",
        "#6B94AA", "#51A058", "#A45B02", "#1D1702", "#E20027", "#E7AB63", "#4C6001", "#9C6966",
        "#64547B", "#97979E", "#006A66", "#391406", "#F4D749", "#0045D2", "#006C31", "#DDB6D0",
        "#7C6571", "#9FB2A4", "#00D891", "#15A08A", "#BC65E9", "#FFFFFE", "#C6DC99", "#203B3C",
        "#671190", "#6B3A64", "#F5E1FF", "#FFA0F2", "#CCAA35", "#374527", "#8BB400", "#797868",
        "#C6005A", "#3B000A", "#C86240", "#29607C", "#402334", "#7D5A44", "#CCB87C", "#B88183",
        "#AA5199", "#B5D6C3", "#A38469", "#9F94F0", "#A74571", "#B894A6", "#71BB8C", "#00B433",
        "#789EC9", "#6D80BA", "#953F00", "#5EFF03", "#E4FFFC", "#1BE177", "#BCB1E5", "#76912F",
        "#003109", "#0060CD", "#D20096", "#895563", "#29201D", "#5B3213", "#A76F42", "#89412E",
        "#1A3A2A", "#494B5A", "#A88C85", "#F4ABAA", "#A3F3AB", "#00C6C8", "#EA8B66", "#958A9F",
        "#BDC9D2", "#9FA064", "#BE4700", "#658188", "#83A485", "#453C23", "#47675D", "#3A3F00",
        "#061203", "#DFFB71", "#868E7E", "#98D058", "#6C8F7D", "#D7BFC2", "#3C3E6E", "#D83D66",
        "#2F5D9B", "#6C5E46", "#D25B88", "#5B656C", "#00B57F", "#545C46", "#866097", "#365D25",
        "#252F99", "#00CCFF", "#674E60", "#FC009C", "#92896B", "#1E2324", "#DEC9B2", "#9D4948",
        "#85ABB4", "#342142", "#D09685", "#A4ACAC", "#00FFFF", "#AE9C86", "#742A33", "#0E72C5",
        "#AFD8EC", "#C064B9", "#91028C", "#FEEDBF", "#FFB789", "#9CB8E4", "#AFFFD1", "#2A364C",
        "#4F4A43", "#647095", "#34BBFF", "#807781", "#920003", "#B3A5A7", "#018615", "#F1FFC8",
        "#976F5C", "#FF3BC1", "#FF5F6B", "#077D84", "#F56D93", "#5771DA", "#4E1E2A", "#830055",
        "#02D346", "#BE452D", "#00905E", "#BE0028", "#6E96E3", "#007699", "#FEC96D", "#9C6A7D",
        "#3FA1B8", "#893DE3", "#79B4D6", "#7FD4D9", "#6751BB", "#B28D2D", "#E27A05", "#DD9CB8",
        "#AABC7A", "#980034", "#561A02", "#8F7F00", "#635000", "#CD7DAE", "#8A5E2D", "#FFB3E1",
        "#6B6466", "#C6D300", "#0100E2", "#88EC69", "#8FCCBE", "#21001C", "#511F4D", "#E3F6E3",
        "#FF8EB1", "#6B4F29", "#A37F46", "#6A5950", "#1F2A1A", "#04784D", "#101835", "#E6E0D0",
        "#FF74FE", "#00A45F", "#8F5DF8", "#4B0059", "#412F23", "#D8939E", "#DB9D72", "#604143",
        "#B5BACE", "#989EB7", "#D2C4DB", "#A587AF", "#77D796", "#7F8C94", "#FF9B03", "#555196",
        "#31DDAE", "#74B671", "#802647", "#2A373F", "#014A68", "#696628", "#4C7B6D", "#002C27",
        "#7A4522", "#3B5859", "#E5D381", "#FFF3FF", "#679FA0", "#261300", "#2C5742", "#9131AF",
        "#AF5D88", "#C7706A", "#61AB1F", "#8CF2D4", "#C5D9B8", "#9FFFFB", "#BF45CC", "#493941",
        "#863B60", "#B90076", "#003177", "#C582D2", "#C1B394", "#602B70", "#887868", "#BABFB0",
        "#030012", "#D1ACFE", "#7FDEFE", "#4B5C71", "#A3A097", "#E66D53", "#637B5D", "#92BEA5",
        "#00F8B3", "#BEDDFF", "#3DB5A7", "#DD3248", "#B6E4DE", "#427745", "#598C5A", "#B94C59",
        "#8181D5", "#94888B", "#FED6BD", "#536D31", "#6EFF92", "#E4E8FF", "#20E200", "#FFD0F2",
        "#4C83A1", "#BD7322", "#915C4E", "#8C4787", "#025117", "#A2AA45", "#2D1B21", "#A9DDB0",
        "#FF4F78", "#528500", "#009A2E", "#17FCE4", "#71555A", "#525D82", "#00195A", "#967874",
        "#555558", "#0B212C", "#1E202B", "#EFBFC4", "#6F9755", "#6F7586", "#501D1D", "#372D00",
        "#741D16", "#5EB393", "#B5B400", "#DD4A38", "#363DFF", "#AD6552", "#6635AF", "#836BBA",
        "#98AA7F", "#464836", "#322C3E", "#7CB9BA", "#5B6965", "#707D3D", "#7A001D", "#6E4636",
        "#443A38", "#AE81FF", "#489079", "#897334", "#009087", "#DA713C", "#361618", "#FF6F01",
        "#006679", "#370E77", "#4B3A83", "#C9E2E6", "#C44170", "#FF4526", "#73BE54", "#C4DF72",
        "#ADFF60", "#00447D", "#DCCEC9", "#BD9479", "#656E5B", "#EC5200", "#FF6EC2", "#7A617E",
        "#DDAEA2", "#77837F", "#A53327", "#608EFF", "#B599D7", "#A50149", "#4E0025", "#C9B1A9",
        "#03919A", "#1B2A25", "#E500F1", "#982E0B", "#B67180", "#E05859", "#006039", "#578F9B",
        "#305230", "#CE934C", "#B3C2BE", "#C0BAC0", "#B506D3", "#170C10", "#4C534F", "#224451",
        "#3E4141", "#78726D", "#B6602B", "#200441", "#DDB588", "#497200", "#C5AAB6", "#033C61",
        "#71B2F5", "#A9E088", "#4979B0", "#A2C3DF", "#784149", "#2D2B17", "#3E0E2F", "#57344C",
        "#0091BE", "#E451D1", "#4B4B6A", "#5C011A", "#7C8060", "#FF9491", "#4C325D", "#005C8B",
        "#E5FDA4", "#68D1B6", "#032641", "#140023", "#8683A9", "#CFFF00", "#A72C3E", "#34475A",
        "#B1BB9A", "#B4A04F", "#8D918E", "#A168A6", "#813D3A", "#425218", "#DA8386", "#776133",
        "#563930", "#8498AE", "#90C1D3", "#B5666B", "#9B585E", "#856465", "#AD7C90", "#E2BC00",
        "#E3AAE0", "#B2C2FE", "#FD0039", "#009B75", "#FFF46D", "#E87EAC", "#DFE3E6", "#848590",
        "#AA9297", "#83A193", "#577977", "#3E7158", "#C64289", "#EA0072", "#C4A8CB", "#55C899",
        "#E78FCF", "#004547", "#F6E2E3", "#966716", "#378FDB", "#435E6A", "#DA0004", "#1B000F",
        "#5B9C8F", "#6E2B52", "#011115", "#E3E8C4", "#AE3B85", "#EA1CA9", "#FF9E6B", "#457D8B",
        "#92678B", "#00CDBB", "#9CCC04", "#002E38", "#96C57F", "#CFF6B4", "#492818", "#766E52",
        "#20370E", "#E3D19F", "#2E3C30", "#B2EACE", "#F3BDA4", "#A24E3D", "#976FD9", "#8C9FA8",
        "#7C2B73", "#4E5F37", "#5D5462", "#90956F", "#6AA776", "#DBCBF6", "#DA71FF", "#987C95",
        "#52323C", "#BB3C42", "#584D39", "#4FC15F", "#A2B9C1", "#79DB21", "#1D5958", "#BD744E",
        "#160B00", "#20221A", "#6B8295", "#00E0E4", "#102401", "#1B782A", "#DAA9B5", "#B0415D",
        "#859253", "#97A094", "#06E3C4", "#47688C", "#7C6755", "#075C00", "#7560D5", "#7D9F00",
        "#C36D96", "#4D913E", "#5F4276", "#FCE4C8", "#303052", "#4F381B", "#E5A532", "#706690",
        "#AA9A92", "#237363", "#73013E", "#FF9079", "#A79A74", "#029BDB", "#FF0169", "#C7D2E7",
        "#CA8869", "#80FFCD", "#BB1F69", "#90B0AB", "#7D74A9", "#FCC7DB", "#99375B", "#00AB4D",
        "#ABAED1", "#BE9D91", "#E6E5A7", "#332C22", "#DD587B", "#F5FFF7", "#5D3033", "#6D3800",
        "#FF0020", "#B57BB3", "#D7FFE6", "#C535A9", "#260009", "#6A8781", "#A8ABB4", "#D45262",
        "#794B61", "#4621B2", "#8DA4DB", "#C7C890", "#6FE9AD", "#A243A7", "#B2B081", "#181B00",
        "#286154", "#4CA43B", "#6A9573", "#A8441D", "#5C727B", "#738671", "#D0CFCB", "#897B77",
        "#1F3F22", "#4145A7", "#DA9894", "#A1757A", "#63243C", "#ADAAFF", "#00CDE2", "#DDBC62",
        "#698EB1", "#208462", "#00B7E0", "#614A44", "#9BBB57", "#7A5C54", "#857A50", "#766B7E",
        "#014833", "#FF8347", "#7A8EBA", "#274740", "#946444", "#EBD8E6", "#646241", "#373917",
        "#6AD450", "#81817B", "#D499E3", "#979440", "#011A12", "#526554", "#B5885C", "#A499A5",
        "#03AD89", "#B3008B", "#E3C4B5", "#96531F", "#867175", "#74569E", "#617D9F", "#E70452",
        "#067EAF", "#A697B6", "#B787A8", "#9CFF93", "#311D19", "#3A9459", "#6E746E", "#B0C5AE",
        "#84EDF7", "#ED3488", "#754C78", "#384644", "#C7847B", "#00B6C5", "#7FA670", "#C1AF9E",
        "#2A7FFF", "#72A58C", "#FFC07F", "#9DEBDD", "#D97C8E", "#7E7C93", "#62E674", "#B5639E",
        "#FFA861", "#C2A580", "#8D9C83", "#B70546", "#372B2E", "#0098FF", "#985975", "#20204C",
        "#FF6C60", "#445083", "#8502AA", "#72361F", "#9676A3", "#484449", "#CED6C2", "#3B164A",
        "#CCA763", "#2C7F77", "#02227B", "#A37E6F", "#CDE6DC", "#CDFFFB", "#BE811A", "#F77183",
        "#EDE6E2", "#CDC6B4", "#FFE09E", "#3A7271", "#FF7B59", "#4E4E01", "#4AC684", "#8BC891",
        "#BC8A96", "#CF6353", "#DCDE5C", "#5EAADD", "#F6A0AD", "#E269AA", "#A3DAE4", "#436E83",
        "#002E17", "#ECFBFF", "#A1C2B6", "#50003F", "#71695B", "#67C4BB", "#536EFF", "#5D5A48",
        "#890039", "#969381", "#371521", "#5E4665", "#AA62C3", "#8D6F81", "#2C6135", "#410601",
        "#564620", "#E69034", "#6DA6BD", "#E58E56", "#E3A68B", "#48B176", "#D27D67", "#B5B268",
        "#7F8427", "#FF84E6", "#435740", "#EAE408", "#F4F5FF", "#325800", "#4B6BA5", "#ADCEFF",
        "#9B8ACC", "#885138", "#5875C1", "#7E7311", "#FEA5CA", "#9F8B5B", "#A55B54", "#89006A",
        "#AF756F", "#2A2000", "#7499A1", "#FFB550", "#00011E", "#D1511C", "#688151", "#BC908A",
        "#78C8EB", "#8502FF", "#483D30", "#C42221", "#5EA7FF", "#785715", "#0CEA91", "#FFFAED",
        "#B3AF9D", "#3E3D52", "#5A9BC2", "#9C2F90", "#8D5700", "#ADD79C", "#00768B", "#337D00",
        "#C59700", "#3156DC", "#944575", "#ECFFDC", "#D24CB2", "#97703C", "#4C257F", "#9E0366",
        "#88FFEC", "#B56481", "#396D2B", "#56735F", "#988376", "#9BB195", "#A9795C", "#E4C5D3",
        "#9F4F67", "#1E2B39", "#664327", "#AFCE78", "#322EDF", "#86B487", "#C23000", "#ABE86B",
        "#96656D", "#250E35", "#A60019", "#0080CF", "#CAEFFF", "#323F61", "#A449DC", "#6A9D3B",
        "#FF5AE4", "#636A01", "#D16CDA", "#736060", "#FFBAAD", "#D369B4", "#FFDED6", "#6C6D74",
        "#927D5E", "#845D70", "#5B62C1", "#2F4A36", "#E45F35", "#FF3B53", "#AC84DD", "#762988",
        "#70EC98", "#408543", "#2C3533", "#2E182D", "#323925", "#19181B", "#2F2E2C", "#023C32",
        "#9B9EE2", "#58AFAD", "#5C424D", "#7AC5A6", "#685D75", "#B9BCBD", "#834357", "#1A7B42",
        "#2E57AA", "#E55199", "#316E47", "#CD00C5", "#6A004D", "#7FBBEC", "#F35691", "#D7C54A",
        "#62ACB7", "#CBA1BC", "#A28A9A", "#6C3F3B", "#FFE47D", "#DCBAE3", "#5F816D", "#3A404A",
        "#7DBF32", "#E6ECDC", "#852C19", "#285366", "#B8CB9C", "#0E0D00", "#4B5D56", "#6B543F",
        "#E27172", "#0568EC", "#2EB500", "#D21656", "#EFAFFF", "#682021", "#2D2011", "#DA4CFF",
        "#70968E", "#FF7B7D", "#4A1930", "#E8C282", "#E7DBBC", "#A68486", "#1F263C", "#36574E",
        "#52CE79", "#ADAAA9", "#8A9F45", "#6542D2", "#00FB8C", "#5D697B", "#CCD27F", "#94A5A1",
        "#790229", "#E383E6", "#7EA4C1", "#4E4452", "#4B2C00", "#620B70", "#314C1E", "#874AA6",
        "#E30091", "#66460A", "#EB9A8B", "#EAC3A3", "#98EAB3", "#AB9180", "#B8552F", "#1A2B2F",
        "#94DDC5", "#9D8C76", "#9C8333", "#94A9C9", "#392935", "#8C675E", "#CCE93A", "#917100",
        "#01400B", "#449896", "#1CA370", "#E08DA7", "#8B4A4E", "#667776", "#4692AD", "#67BDA8",
        "#69255C", "#D3BFFF", "#4A5132", "#7E9285", "#77733C", "#E7A0CC", "#51A288", "#2C656A",
        "#4D5C5E", "#C9403A", "#DDD7F3", "#005844", "#B4A200", "#488F69", "#858182", "#D4E9B9",
        "#3D7397", "#CAE8CE", "#D60034", "#AA6746", "#9E5585", "#BA6200"]
    return color_ls[n]
