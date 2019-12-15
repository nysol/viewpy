#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.viewjs as vjs
import nysol.util.mtemp as mtemp
import json

def msankey(i,o,v,f,title="",h=500,w=960,nl=False,T=None):

	# f= 2 fld
	if type(f) is str:
		ff = f.split(',')
	elif type(f) is list:
		ff = f
	else :	
		raise TypeError("f= unsupport " + str(type(k)) )

	if len(ff) < 2:
		raise TypeError("f= takes just two field names")


	if T != None:
		import re
		os.environ["KG_TmpPath"] = re.sub(r'/$', "", T)

	if h==None:
		h=500

	if w==None:
		w=960

	if title==None:
		title = ""

	tempW	= mtemp.Mtemp()
	nodef = tempW.file() 
	edgef = tempW.file() 
	
	ef1 = ff[0] 
	ef2 = ff[1]
	ev = v

	iFile = i
	oFile = o
	
	f0 =   nm.mcut(i=iFile,f="%s:nodes"%(ef1))
	f1 =   nm.mcut(i=iFile,f="%s:nodes"%(ef2))
	f2 = None
	f2 <<= nm.muniq(i=[f0,f1],k="nodes")
	f2 <<= nm.mnumber(s="nodes",a="num",o=nodef)
	f2.run()
	
	f3 = None
	f3 <<= nm.mcut(f="%s:nodes1,%s:nodes2,%s"%(ef1,ef2,ev),i=iFile)
	f3 <<= nm.mjoin(k="nodes1",K="nodes",m=nodef,f="num:num1")
	f3 <<= nm.mjoin(k="nodes2",K="nodes",m=nodef,f="num:num2")
	f3 <<= nm.mcut(f="num1,num2,%s"%(ev))
	f3 <<= nm.msortf(f="num1%n,num2%n",o=edgef)
	f3.run()

	wk=[]
	nodeL=[]

	for flds in nm.readcsv(nodef).getline(otype='dict'):
		nodeL.append({"name":flds['nodes']} )
	
	nodes = json.JSONEncoder().encode(nodeL)
		
	linkL=[]
	for flds in nm.readcsv(edgef).getline(otype='dict',dtype={"num1":"int","num2":"int",ev:"int"}):
		linkL.append({"source":flds["num1"],"target":flds["num2"],"value":flds[ev]})
	
	links = json.JSONEncoder().encode(linkL)

	nolabel=""
	if nl :
		nolabel="font-size: 0px;" 

	html = sys.stdout
	if not oFile ==  None :
		html = open(oFile,"w")


	outTemplate ='''
<!DOCTYPE html>
<html class="ocks-org do-not-copy">
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{
    font: 10px sans-serif;
}}
svg {{
    padding: 10px 0 0 10px;
}}
.arc {{
    stroke: #fff;
}}
#tooltip {{
position: absolute;
width: 150px;
height: auto;
padding: 10px;
background-color: white;
-webkit-border-radius: 10px;
-moz-border-radius: 10px;
border-radius: 10px;
-webkit-box-shadow: 4px 4px 10px rgba(0,0,0,0.4);
-moz-box-shadow: 4px 4px 10px rgba(0,0,0,0.4);
box-shadow: 4px 4px 10px rgba(0,0,0,0.4);
pointer-events: none;
}}
#tooltip.hidden {{
display: none;
}}
#tooltip p {{
margin: 0;
font-family: sans-serif;
font-size: 10px;
line-height: 14px;
}}
#chart {{
height: 500px;
}}
.node rect {{
    cursor: move;
    fill-opacity: .9;
    shape-rendering: crispEdges;
}}
.node text {{
    pointer-events: none;
    text-shadow: 0 1px 0 #fff;
    {nolabel}
}}
.link {{
    fill: none;
    stroke: #000;
    stroke-opacity: .2;
}}
.link:hover {{
    stroke-opacity: .5;
}}
</style>
<body>
<h1>{title}</h1>
<p id="chart">
<script>
	{d3js_str}
	d3.sankey = function() {{
		var sankey = {{}},
		nodeWidth = 24,
		nodePadding = 8,
		size = [1, 1],
		nodes = [],
		links = [];

		sankey.nodeWidth = function(_) {{
			if (!arguments.length) return nodeWidth;
			nodeWidth = +_;
			return sankey;
		}};

		sankey.nodePadding = function(_) {{
			if (!arguments.length) return nodePadding;
			nodePadding = +_;
			return sankey;
		}};

		sankey.nodes = function(_) {{
			if (!arguments.length) return nodes;
			nodes = _;
			return sankey;
		}};
		sankey.links = function(_) {{
			if (!arguments.length) return links;
			links = _;
			return sankey;
		}};
		sankey.size = function(_) {{
			if (!arguments.length) return size;
			size = _;
			return sankey;
		}};
	
		sankey.layout = function(iterations){{
			computeNodeLinks();
			computeNodeValues();
			computeNodeBreadths();
			computeNodeDepths(iterations);
			computeLinkDepths();
			return sankey;
		}};

		sankey.relayout = function() {{
			computeLinkDepths();
			return sankey;
		}};

		sankey.link = function() {{
			var curvature = .5;
			function link(d) {{
				var x0 = d.source.x + d.source.dx,
				x1 = d.target.x,
				xi = d3.interpolateNumber(x0, x1),
				x2 = xi(curvature),
				x3 = xi(1 - curvature),
				y0 = d.source.y + d.sy + d.dy / 2,
				y1 = d.target.y + d.ty + d.dy / 2;
				return "M" + x0 + "," + y0
				+ "C" + x2 + "," + y0
				+ " " + x3 + "," + y1
				+ " " + x1 + "," + y1;
			}}
			link.curvature = function(_) {{
				if (!arguments.length) return curvature;
				curvature = +_;
				return link;
			}};
			return link;
		}};

		// Populate the sourceLinks and targetLinks for each node.
		// Also, if the source and target are not objects, assume they are indices.
		function computeNodeLinks() {{
			nodes.forEach(function(node) {{
				node.sourceLinks = [];
				node.targetLinks = [];
			}});

			links.forEach(function(link) {{
				var source = link.source,
				target = link.target;
				if (typeof source === "number") source = link.source = nodes[link.source];
				if (typeof target === "number") target = link.target = nodes[link.target];
				source.sourceLinks.push(link);
				target.targetLinks.push(link);
			}});
		}}

		// Compute the value (size) of each node by summing the associated links.
		function computeNodeValues() {{
			nodes.forEach( function(node) {{
				node.value = Math.max(d3.sum(node.sourceLinks, value),d3.sum(node.targetLinks, value));
			}} );
 		}}
 		
		// Iteratively assign the breadth (x-position) for each node.
		// Nodes are assigned the maximum breadth of incoming neighbors plus one;
		// nodes with no incoming links are assigned breadth zero, while
		// nodes with no outgoing links are assigned the maximum breadth.
		function computeNodeBreadths() {{
			var remainingNodes = nodes,
					nextNodes,
					x = 0;
			while (remainingNodes.length) {{
				nextNodes = [];
				remainingNodes.forEach(function(node) {{
					node.x = x;
					node.dx = nodeWidth;
					node.sourceLinks.forEach(function(link) {{
						nextNodes.push(link.target);
					}});
				}});
				remainingNodes = nextNodes;
				++x;
			}}
			//
			moveSinksRight(x);
			scaleNodeBreadths((width - nodeWidth) / (x - 1));
		}}
		
		function moveSourcesRight() {{
			nodes.forEach(function(node) {{
				if (!node.targetLinks.length) {{
					node.x = d3.min(node.sourceLinks, function(d) {{ return d.target.x; }} ) - 1;
				}}
			}});
		}}
	
		function moveSinksRight(x) {{
			nodes.forEach(function(node) {{
				if (!node.sourceLinks.length) {{
					node.x = x - 1;
				}}
			}});
		}}

		function scaleNodeBreadths(kx) {{
			nodes.forEach(function(node) {{
				node.x *= kx;
			}});
		}}



		function computeNodeDepths(iterations) {{
			var nodesByBreadth = d3.nest()
													.key(function(d) {{ return d.x; }})
													.sortKeys(d3.ascending)
													.entries(nodes)
													.map(function(d) {{ return d.values; }});
                                                                
			//
			initializeNodeDepth();
			resolveCollisions();

			for (var alpha = 1; iterations > 0; --iterations){{
				relaxRightToLeft(alpha *= .99);
				resolveCollisions();
				relaxLeftToRight(alpha);
				resolveCollisions();
			}}
                                                                
			function initializeNodeDepth() {{
				var ky = d3.min(nodesByBreadth, function(nodes) {{
					return (size[1] - (nodes.length - 1) * nodePadding) / d3.sum(nodes, value);
				}});
				nodesByBreadth.forEach(function(nodes) {{
					nodes.forEach(function(node, i) {{
						node.y = i;
						node.dy = node.value * ky;
					}});
				}});
				links.forEach(function(link) {{
					link.dy = link.value * ky;
				}});
			}}
		
			function relaxLeftToRight(alpha) {{
				nodesByBreadth.forEach(function(nodes, breadth) {{
					nodes.forEach(function(node) {{
						if (node.targetLinks.length) {{
							var y = d3.sum(node.targetLinks, weightedSource) / d3.sum(node.targetLinks, value);
							node.y += (y - center(node)) * alpha;
						}}
					}});
				}});
			
				function weightedSource(link) {{
					return center(link.source) * link.value;
				}}
			}}
		
			function relaxRightToLeft(alpha) {{
				nodesByBreadth.slice().reverse().forEach(function(nodes){{
					nodes.forEach(function(node) {{
						if (node.sourceLinks.length) {{
							var y = d3.sum(node.sourceLinks, weightedTarget) / d3.sum(node.sourceLinks, value);
							node.y += (y - center(node)) * alpha;
						}}
					}});
				}});

				function weightedTarget(link) {{
					return center(link.target) * link.value;
				}}
			}}
		
			function resolveCollisions() {{
				
				nodesByBreadth.forEach(function(nodes) {{
					var node, dy, y0 = 0,
						n = nodes.length, i;
					// Push any overlapping nodes down.
					nodes.sort(ascendingDepth);
					for (i = 0; i < n; ++i) {{
						node = nodes[i];
						dy = y0 - node.y;
						if (dy > 0) node.y += dy;
						y0 = node.y + node.dy + nodePadding;
					}}
					// If the bottommost node goes outside the bounds, push it back up.
					dy = y0 - nodePadding - size[1];
					if (dy > 0) {{
						y0 = node.y -= dy;
						// Push any overlapping nodes back up.
						for (i = n - 2; i >= 0; --i) {{
							node = nodes[i];
							dy = node.y + node.dy + nodePadding - y0;
							if (dy > 0) node.y -= dy;
							y0 = node.y;
						}}
					}}
				}});
			}}
			function ascendingDepth(a, b) {{ return a.y - b.y; }}
		}}

		function computeLinkDepths() {{

			nodes.forEach(function(node) {{
				node.sourceLinks.sort(ascendingTargetDepth);
				node.targetLinks.sort(ascendingSourceDepth);
			}});
	
			nodes.forEach(function(node) {{
				var sy = 0, ty = 0;
				node.sourceLinks.forEach(function(link) {{
					link.sy = sy;
					sy += link.dy;
				}});
				node.targetLinks.forEach(function(link) {{
					link.ty = ty;
					ty += link.dy;
				}});
			}});
	
			function ascendingSourceDepth(a, b) {{
				return a.source.y - b.source.y;
			}}
			function ascendingTargetDepth(a, b) {{
				return a.target.y - b.target.y;
			}}
		}}
		
		function center(node){{
			return node.y + node.dy / 2;
		}}

		function value(link) {{
			return link.value;
		}}

		return sankey;
	}};
</script>

<script>
	var margin = {{top: 1, right: 1, bottom: 6, left: 1}},
			width = {width} - margin.left - margin.right,
			height = {height} - margin.top - margin.bottom;

	var formatNumber = d3.format(",.0f"),
			format = function(d) {{ return formatNumber(d) + " TWh"; }},
			color = d3.scale.category20();

	var svg = d3.select("#chart").append("svg")
  	  .attr("width", width + margin.left + margin.right)
    	.attr("height", height + margin.top + margin.bottom)
    	.append("g")
    	.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var sankey = d3.sankey()
    .nodeWidth(15)
    .nodePadding(10)
    .size([width, height]);

	var path = sankey.link();

	var nodes={nodes}
	var links={links}

	sankey
		.nodes(nodes)
		.links(links)
		.layout(32);
        
	var link = svg.append("g").selectAll(".link")
					.data(links)
					.enter().append("path")
					.attr("class", "link")
					.attr("d", path)
					.style("stroke-width", function(d) {{ return Math.max(1, d.dy); }})
					.sort(function(a, b) {{ return b.dy - a.dy; }});
        
	link.append("title")
			.text(function(d) {{ return d.source.name + " → " + d.target.name + "" + format(d.value); }});
        
	var node = svg.append("g").selectAll(".node")
					.data(nodes)
					.enter().append("g")
					.attr("class", "node")
					.attr("transform", function(d) {{ return "translate(" + d.x + "," + d.y + ")"; }})
					.call(
						d3.behavior.drag()
							.origin(function(d) {{ return d; }})
							.on("dragstart", function() {{ this.parentNode.appendChild(this); }})
							.on("drag", dragmove)
					);

	node.append("rect")
			.attr("height", function(d) {{ return d.dy; }})
			.attr("width", sankey.nodeWidth() )
			.style("fill", function(d) {{ return d.color = color(d.name.replace(/ .*/, "")); }})
			.style("stroke", function(d) {{ return d3.rgb(d.color).darker(2); }})
			.append("title")
			.text(function(d) {{ return d.name + "" + format(d.value); }});
        
	node.append("text")
			.attr("x", -6)
			.attr("y", function(d) {{ return d.dy / 2; }})
			.attr("dy", ".35em")
			.attr("text-anchor", "end")
			.attr("transform", null)
			.text(function(d) {{ return d.name; }})
			.filter(function(d) {{ return d.x < width / 2; }})
			.attr("x", 6 + sankey.nodeWidth())
			.attr("text-anchor", "start");
        
	function dragmove(d){{
		d3.select(this)
			.attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
		sankey.relayout();
		link.attr("d", path);
	}}
</script>
'''.format(title=title,nolabel=nolabel,d3js_str=vjs.ViewJs.d3jsMin(),nodes=nodes,links=links,width=w,height=h)


	html.write(outTemplate)

	if not oFile ==  None :
		html.close()


if __name__ == '__main__':

#i,o,v,f,k=None,title=None,height=None,width=None,cc=None,footer=None):


	msankey("/Users/nain/work/git/view/msankey/check/data/dat1.csv","./out0-1.html","val","node1,node2")
	msankey("/Users/nain/work/git/view/msankey/check/data/man.csv","./out1.html","val","node1,node2")
	msankey("/Users/nain/work/git/view/msankey/check/data/man.csv","./out2.html","val","node1,node2",title="タイトル")


