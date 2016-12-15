# Mission Control
An Open Source Usability Package for GraphSpace in Python


##############
#QuickStart  #
##############
Mission Control is designed to be used in the frame of a Python interactive session. You must use Python 3 for Mission Control to work
properly. If you want to add your own data attributes to a graph, the best way is to set up your own Python file which does the data
analysis for you and compiles it into a dictionary. Then the visualization can be done in an interactive session from that script. 

This quickstart guide will take you through the core commands of Mission Control. First, set up a script with the following commands:

from missionControl import *

g = parse(edgefile='example_edges.txt', nodefile='example_nodes.txt') 
\#this returns a Graph object constructed out of the data from the given files. The example files are formatted properly.
#the delimiter can be changed using the delimiter argument (defaults to '\t')
#Your files should include a line 1 header detailing the names of the data attributes of
#the file. An edgefile header must start with 'source' followed by 'target' followed optionally by other data attributes (separated by
#delimiter). A nodefile header must start with 'ID' followed optionally by other data attributes.

#If you want to do your own analysis on the example files, construct a dictionary whose keys are either node or edge IDs
#(an edge ID is a string that looks like this: 'node1_;_node2' where node1 and 2 are in alphabetical order if the graph is undirected. 
#This will be changed to a more graceful representation in future iterations of the package.
#I've constructed an example of code that creates a properly formatted dictionary below.
#The example supposes that you have some way of designating which data point goes to the appropriate node,
#represented here through object notation.

d = {}
for n in nodes:
    d[n.id] = n.data
#NOTE: THESE 3 LINES OF CODE WILL NOT WORK IF YOU PUT THEM IN A SCRIPT, IT REPRESENTS CUSTOMIZED ANALYSIS THAT WOULD BE DONE SEPARATELY.

#from here it's a simple matter to do the rest of the process in an interactive session. Simply:
g.nodeInstall('my data attribute',d)
#THIS ALSO WON'T WORK UNLESS YOU'VE CONSTRUCTED YOUR OWN DICTIONARY ACCORDING TO THE GUIDELINES ABOVE
#FOR EXPERIMENTING WITH VISUALIZATION THAT DOESN'T REQUIRE CONSTRUCTING YOUR OWN DICTIONARY, KEEP READING BELOW


#and from there we can pattern a GraphSpace visual attribute after the given data attribute:
g.visualize('my data attribute')
#a rudimentary UI will ask you how you want to visualize the data. Support for inputting this information through the arguments
#will be included in a future iteration of the package.


#then we upload to GraphSpace. 
g.upload()
#The specifics of this are also handled by a rudimentary UI



#And there you have it. My example files include a few data attributes that you can play around with. Try:
g.visualize('Team')
g.visualize('Random 0-50')
g.visualize('Node Degree')
g.visualize('weight')

#if you're ever wondering what's in the graph currently, use the display command:
g.display()
g.display('nodes')
g.display('edges')





##############################################################################################
#Those are the main important commands, but here's a quick guide to the remainder of the API.#
#For more detailed documentation, see missionControl.py                                      #
##############################################################################################


#if you ever want to remove an attribute from the graph, use the remove command:
g.remove('__background_color__')
g.remove('Team')

#if you ever want to save a Mission Control session so that the graph and data attributes are immediately replicable, use export
g.export()

#if you ever want to change the default visual attributes of the graph, use the default command:
g.default('background_color','#ffffff')
g.default() #shows the current default settings
#note that visual attributes patterned after a data attribute with None as an entry will take on the default settings


#if you ever want to get data out of the Graph, use nodeGet and/or edgeGet
g.nodeGet('Team') #returns a dictionary describing the Team of each node.
g.edgeGet('weight')













This package is built on top of a Utils package created by Anna Ritz for her Biology 331 class. Mission Control relies on the following base to function:

- `json_utils.py` contains functions to write an annotated graph to a text file in [JSON](http://www.json.org/) format readable by GraphSpace.
- `graphspace_utils.py` contains [curl commands](https://curl.haxx.se/docs/manpage.html) to post the JSON file to GraphSpace.

Auto-generated documentation is available on the [Bio331 website](http://www.reed.edu/biology/courses/bio331/) under [Support Code](http://www.reed.edu/biology/courses/bio331/supportcode/index).

## GraphSpace

GraphSpace was originally developed at Virginia Tech.  It is available at (www.graphspace.org) and the source code is available on the [GitHub Page](https://github.com/Murali-group/GraphSpace).
