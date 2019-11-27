#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.viewjs as vjs
import nysol.util.mtemp as mtemp







def mnetpie(
	ei,ni,ef,nf,o,
	nodeSizeFld=None,nodeTipsFld=None,nodeColorFld=None,
	edgeWidthFld=None,edgeColorFld=None,
	pieDataFld=None,pieTipsFld=None,picFld=None,
	undirect=False,offline=False):


	#ei:edge file
	#ef:egfile
	if type(ef) is str:
			ef = ef.split(',')
	if len(ef) != 2 :
		raise Exception("ef= takes just two field names")


	if not ( ( pieDataFld == None and pieTipsFld == None ) or ( pieDataFld != None and pieTipsFld != None ) ) :
		raise Exception("pieDataFld= pieTipsFld= are necessary at the same time")

	if picFld != None and pieDataFld != None :
		raise Exception("picFld= cannot be specified with pieDataFld= pieTipsFld=")

	if nodeColorFld != None :
		if picFld != None or pieDataFld != None or pieTipsFld != None :
			raise Exception("nodeColorFld= cannot be specified with pieDataFld= pieTipsFld= picFld=")


	if pieDataFld != None and pieTipsFld != None :
		caseNo = 1
	elif picFld != None :
		caseNo = 2
	else:
		caseNo = 0 		

	tempW	= mtemp.Mtemp()

	xxnode = tempW.file()

	nodefld =[]
	nodedmy1 =[]
	nodedmy2 =[]

	nodefld.append("%s:node"%(nf))	
	if nodeSizeFld != None : 
		nodefld.append("%s:nodesize"%(nodeSizeFld))
	else:
		nodedmy1.append("nodesize")
		nodedmy2.append("50")

	if nodeTipsFld != None :
		nodefld.append("%s:nodeT"%(nodeTipFld))
	else:
		nodedmy1.append("nodeT")
		nodedmy2.append("")
		
	if nodeColorFld != None :
		nodefld.append("%s:nodeClr"%(nodeColorFld))
	else:
		nodedmy1.append("nodeClr")
		nodedmy2.append("skyblue")

	if caseNo == 1 :
		nodefld.append("%s:pieD"%(pieDataFld))
		nodefld.append("%s:pieT"%(pieTipsFld))
	elif caseNo == 2 :
		nodefld.append("%s:pic"%(picFld))
	else:
		nodedmy1.append("pic")
		nodedmy2.append("")

	f1 = None
	f1 <<= nm.mcut(i=ni,f=nodefld) 
	if len(nodedmy1) != 0 :
		f1 <<= nm.msetstr(a=nodedmy1 ,v=nodedmy2)
	
	if caseNo == 1 :
		f1 <<= nm.mshare(k="node",f="pieD:pieDS")
		f1 <<= nm.mnumber(k="node",a="nodeid",B=True)

		f2 = nm.muniq(k="pieT",i=f1)
		f2 <<= nm.mnumber(q=True,a="pieTno")
		f2 <<= nm.mjoin(k="pieT",f="pieTno",i=f1).iredirect("m")
		f2 <<= nm.msortf(f="nodeid%n,pieTno%n",o=xxnode)
	else:
		f2 = nm.mnumber(a="nodeid%n",q=True,i=f1,o=xxnode)

	f2.run()

	xxedge = tempW.file()
	# MAKE EDGE DATA 
	edgefld  = []
	edgedmy1 = []
	edgedmy2 = []
	edgefld.append("%s:edgeS"%(ef[0]))
	edgefld.append("%s:edgeE"%(ef[1]))

	if edgeWidthFld != None:
		edgefld.append ("%s:edgesize"%(edgeWidthFld))
	else:
		edgedmy1.append("edgesize")
		edgedmy2.append("1")

	if edgeColorFld != None :
		edgefld.append("%s:edgecolor"%(edgeColorFld))
	else:
		edgedmy1.append("edgecolor")
		edgedmy2.append("black")

	f3 = None
	f3 <<= nm.mcut(i=ei,f=edgefld)
	if len(edgedmy1)!=0 :
		f3 <<= nm.msetstr(a=edgedmy1, v=edgedmy2)

	f3 <<= nm.mnumber(a="preNo",q=True)
	f3 <<= nm.mbest(k="edgeS,edgeE",s="preNo%nr")
	f3 <<= nm.mnumber(s="preNo%n",a="edgeID")
	f3 <<= nm.mjoin(k="edgeS",K="node" ,f="nodeid:edgeSid",m=xxnode)
	f3 <<= nm.mjoin(k="edgeE",K="node",f="nodeid:edgeEid", m=xxnode)
		
	#双方向チェック一応
	f4 =None
	f4 <<= nm.mfsort(i=f3,f="edgeS,edgeE")
	f4 <<= nm.mcount(k="edgeS,edgeE",a="edgecnt")
	f4 <<= nm.mselnum(c="[2,]",f="edgecnt")
	f4 <<= nm.msetstr(a="biflg",v=1)
	f4 <<= nm.mjoin(k="edgeID",f="biflg",n=True,i=f3).iredirect("m")
	f4 <<= nm.msortf(f="edgeID%n",o=xxedge)
	f4.run()

	gdata="{\"nodes\":["
	if caseNo == 1 :
		nodedatastk = []
		nodedatas =""		
		for val,top,bot in nm.readcsv(xxnode).getline(k="nodeid" , otype='dict',q=True):
			name = val["node"]
			r = val["nodesize"]
			title = val["nodeT"]
			if top :
				nodedatas ="{\"name\":\"%s\",\"title\":\"%s\",\"r\":%s,\"node\":["%(name,title,r) 

			pieTno = val["pieTno"]
			pieT = val["pieT"]
			pieDS = val["pieDS"]
			nodedatas += "{\"group\":%s,\"color\":%s,\"value\":%s,\"title\":\"%s\"}"%(pieTno,pieDS,pieDS,pieT)

			if bot :
				nodedatas += "]}"
				nodedatastk.append( nodedatas)
				nodedatas =""
			else:
				nodedatas += ","
				
		gdata += ",".join(nodedatastk)

	else:
		nodedatastk = []
		for val in nm.readcsv(xxnode).getline(otype='dict'):
			name = val["node"]
			r = val["nodesize"]
			title = val["nodeT"]
			pic = val["pic"]
			nclr = val["nodeClr"]
			nodedatas = "{\"name\":\"%s\",\"title\":\"%s\",\"pic\":\"%s\",\"color\":\"%s\",\"r\":%s}"%(name,title,pic,nclr,r)
			nodedatastk.append (nodedatas)

		gdata += ",".join(nodedatastk)

	gdata += "],\"links\": ["

	edgedatastk = []
	for val in nm.readcsv(xxedge).getline(otype='dict'):
		es = val["edgeSid"]
		et = val["edgeEid"]
		esize = val["edgesize"]
		ecolor = val["edgecolor"]
		edgedatas = "{\"source\":%s,\"target\":%s,\"length\":500,\"ewidth\":%s,\"color\":\"%s\"}"%(es,et,esize,ecolor)
		edgedatastk.append(edgedatas)

	gdata += ','.join(edgedatastk)

	gdata += "]}"

	direct = ".attr('marker-end','url(#arrowhead)')"
	if undirect :
		direct = ""

	nodeTemplate ='''
    node
			.append("circle")
			.attr("r",function(d){return d.r/4;})
			.attr("fill", function(d){return d.color;})
			.append("title")
			.text(function(d){return d.title;})
	'''
	nodemakeTemplate ='''
	for(var i=0 ; i< graph.nodes.length;i++){
		graph.nodes[i].id = i
	}
	'''

	if pieDataFld != None :
		nodeTemplate =''' 
    node.selectAll("path")
        .data( function(d, i){
          return pie(d.node);
				})
        .enter()
        .append("svg:path")
        .attr("d", arc)
        .attr("fill", function(d, i) {
					return color(d.data.group);
				})
				.append("title")
				.text(function(d){{return d.data.title;}})

        node.append("circle")
				.attr("r",function(d){{return d.r/4;}})
				.attr({
					'fill': 'white'
				})
				.append("title")
				.text(function(d){{return d.title;}});
		'''
		nodemakeTemplate ='''
			for(var i=0 ; i< graph.nodes.length;i++){
			var r = graph.nodes[i].r
			for(var j=0 ; j< graph.nodes[i].node.length;j++){
				graph.nodes[i].node[j]['r'] = r
			}
			graph.nodes[i].id = i
		}
		'''
	elif picFld !=None:
		nodeTemplate ='''
    node
			.append("image")
			.attr("height",function(d){return d.r;})
			.attr("width",function(d){return d.r;})
			.attr("x",function(d){return -1 * d.r/2; })
			.attr("y",function(d){return -1 * d.r/2; })
			.attr("xlink:href",function(d){return d.pic; })
			.append("title")
			.text(function(d){return d.title;})
		'''
	
	d3js_str="<script type='text/javascript' src='http://d3js.org/d3.v3.min.js'></script>"

	if offline :
		d3js_str = "<script>%s<script>"%(vjs.ViewJs.d3jsMin())


	outTemplate ='''
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	{d3js_str}
  <style></style>
</head>
<body>
<script type="text/javascript">
	var graph = {gdata} ;

  var width = 4000,
      height = 3000;

	var color = d3.scale.category10();
    
	{nodemakeTemplate};

	for(var i=0 ; i< graph.links.length;i++){{
		graph.links[i].id = i
	}}

	var pie = d3.layout.pie()
        .sort(null)
        .value(function(d) {{ return d.value; }});

	var arc = d3.svg.arc()
       	.outerRadius( function(d){{ return d.data.r ; }})
        .innerRadius( function(d){{ return d.data.r/2 ; }} );
		
	var svg = d3.select("body").append("svg")
		.attr("width", width)
		.attr("height", height);

	d3.select("svg").append('defs').append('marker')
		.attr({{'id':'arrowhead',
						'viewBox':'-0 -5 10 10',
						'refX':30,
						'refY':0,
						'orient':'auto-start-reverse',
						'markerWidth':5,
						'markerHeight':5,
						'xoverflow':'visible'}})
		.append('path')
		.attr('d', 'M 0,-5 L 10 ,0 L 0,5')
		.attr('fill', '#999')
		.style('stroke','none');
            
	var g = svg.append("g");
	var node = g.selectAll(".node");
	var link = g.selectAll(".link");
	nodes = graph.nodes
  links = graph.links

	var force = 
		d3.layout.force()
			.linkDistance(200)
			.linkStrength(3.5)
      .charge(-3500)
			.gravity(0.1)
			.friction(0.95)
      .size([width, height])
			.on("tick", function() {{
				link
					.attr("x1", function(d) {{ return d.source.x; }})
					.attr("y1", function(d) {{ return d.source.y; }})
					.attr("x2", function(d) {{ return d.target.x; }})
					.attr("y2", function(d) {{ return d.target.y; }});

				node
					.attr("x", function(d) {{ return d.x; }})
					.attr("y", function(d) {{ return d.y; }})
					.attr("transform", function(d) {{ return "translate(" + d.x + "," + d.y + ")"}});	
	    }});


		node = node.data(nodes, function( d ) {{ return d.id; }} );
		link = link.data(links, function( d ) {{ return d.id; }} );


    link
      .enter()
      .append("line")
      .attr("class", "link")
			.style("stroke", function( d ) {{ return d.color; }} )
			.style("stroke-width", function( d ) {{ return d.ewidth; }})
			{direct}


    node
    	.enter()
			.append("g")
      .attr("class", "node")
			.style({{}})
			.call(force.drag)
			.on("contextmenu", function(nd) {{
					d3.event.preventDefault();
					force.stop()
				 	nodes.splice( nd.index, 1 );
					links = links.filter(function(nl) {{
						return nl.source.index != nd.index && nl.target.index != nd.index;					
					}});
					node = node.data(nodes, function( d ) {{ return d.id; }} );
					node.exit().remove();
					link = link.data( links, function( d ) {{ return d.id; }} );
					link.exit().remove();
			    force.nodes(nodes)
      	   .links(links)
        	 .start();
				}});  
	
		{nodeTemplate}


    node
      .append("text")
      .attr("text-anchor", "middle")
			.style("stroke", "black")
      .text(function(d) {{ return d.name; }});

    force.nodes(nodes)
         .links(links)
         .start();


</script>
</body>
</html>
	'''.format(d3js_str=d3js_str,gdata=gdata,nodemakeTemplate=nodemakeTemplate,direct=direct,nodeTemplate=nodeTemplate)

	html = sys.stdout
	if not o ==  None :
		html = open(o,"w")

	html.write(outTemplate)

	if not o == None :
		html.close()



if __name__ == '__main__':

#i,o,v,f,k=None,title=None,height=None,width=None,cc=None,footer=None):
#	"ei=","ni=","ef=","nf=","o=",
#	"nodeSizeFld=","pieDataFld=","pieTipsFld=",
#	"nodeTipsFld=","picFld=","nodeColorFld=",
#	"edgeWidthFld=","edgeColorFld=",
#	"--help","-undirect","-offline"
	mnetpie("edge.csv","node.csv","source,target","name","./out1.html" )
	mnetpie("edge.csv","nodepie.csv","source,target","name","./out2.html",nodeSizeFld="size",pieDataFld="pied",pieTipsFld="piet" )
	mnetpie("edge.csv","nodepic.csv","source,target","name","./out3.html",nodeSizeFld="size",picFld="pic" )
	mnetpie("edge.csv","nodepic.csv","source,target","name","./out4.html",picFld="pic" )

	mnetpie("edge.csv","node.csv","source,target","name","./out5.html",nodeSizeFld="size",nodeColorFld="color",edgeColorFld="color" )


#ni=node.csv nf=name nodeSizeFld=size ei=edge.csv ef=source,target o=xxxa.html  nodeSizeFld=size nodeColorFld=color edgeColorFld=color


