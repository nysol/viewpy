#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.viewjs as vjs
import nysol.util.mtemp as mtemp
import json
import xml.etree.ElementTree as ET 

class Pmml(object):

	_condmap = { 
		"lessOrEqual":"<=","greaterThan":">",
		"greaterOrEqual":">=","equal":"==",
		"notEqual":"!=","lessThan":"<" 
	}

	def condCKsub(self,xstr):
		notFlg = False

		cond_str = ""
		cond=[]
		
		bop = xstr.attrib['booleanOperator']
		if bop == "isIn" :
			for astr in xstr.findall("Array"):
				for astrs in astr.text.split(" "):
					cond.append(re.sub( r'"$' , "",re.sub(r'^"', "",astrs)))

			cond_str = "{"+",".join(cond)+"}"

		elif bop == "isNotIn" :
			cond_str = "else"

		return cond_str

	def condCK(self,xstr):

		cond_str =""
		if xstr.find("SimplePredicate") != None :

			con = xstr.find("SimplePredicate")
			if not con.attrib['operator'] in Pmml._condmap:
				raise ( ValueError("UNKNOW FORMAT (%s)"%(con.attrib['operator'])))

			cond_str = " %s %s"%(Pmml._condmap[con.attrib['operator']],con.attrib['value'])

		elif xstr.find("SimpleSetPredicate") != None:

			cond_str = self.condCKsub(xstr.find("SimpleSetPredicate"))

		elif xstr.find("CompoundPredicate") != None :

			if xstr.find("CompoundPredicate").attrib["booleanOperator"] == "surrogate" :

				for x in xstr.find("CompoundPredicate").iter():

					if x.tag == "SimplePredicate" :

						if not x.attrib['operator'] in Pmml._condmap :
							raise ( ValueError("UNKNOW FORMAT (%s)"%(x.attrib['operator'])))

						cond_str = " %s %s"%(_condmap[x.attrib['operator']],x.attrib['value'])

						return cond_str 

					elif x.tag == "SimpleSetPredicate" :
						cond_str = self.condCKsub(x)
						return cond_str 
			else:
				raise( ValurError("UNKNOW FORMAT ($s)"%(xstr.find('CompoundPredicate').attrib['booleanOperator'])))

		elif xstr.find("Extension") != None :

			for ext in xstr.findall("Extension"):

				if ext.find("SimplePredicate") !=None:
					con = ext.find("SimplePredicate")
					val =[]
					if con.attrib['operator'] == "notcontain" :
						cond_str = "else"

					elif con.attrib['operator'] == "contain" :
						for idx in con.findall("index") :
							val.append(idx.attrib['value'])

						cond_str = "".join(val)
		
		return cond_str		


	def getFld(self,chd):
		fld = ""
		if chd.find("CompoundPredicate") != None:
			for x in chd.find("CompoundPredicate").iter():
				if x.attrib['field'] :
					fld = x.attrib['field']
					break

		elif chd.find("SimplePredicate") != None :
			fld =chd.find("SimplePredicate").attrib['field']

		elif chd.find("SimpleSetPredicate") != None :
			fld =chd.find("SimpleSetPredicate").attrib['field']

		elif chd.find("Extension") != None:
			for ext in chd.findall("Extension"):
				if ext.find("SimplePredicate") != None:
					fld = ext.find("SimplePredicate").attrib['field']
					break

		return fld


	def setAlpha(self,xstr):

		al_se1 = al_min = al = -1
		for sc in xstr.findall('Extension'):
			ename = sc.attrib['name']
			if ename == "1SE alpha" :
				al_se1 = float(sc.attrib['value'])
			elif ename == "min alpha" :
				al_min = float(sc.attrib['value'])
			elif ename == "alpha" :
				al = float(sc.attrib['value'])

		if self.alpha == "min" :
			if al_min == -1 :
				raise ValueError("can not use alpha=min or alpha=1se in this model")
			self.alpha = al_min

		elif self.alpha == "se1" :
			if al_se1 == -1 : 
				raise ValueError("can not use alpha=min or alpha=1se in this model" )
			self.alpha = al_se1

		elif self.alpha == None :
			if al==-1 :
				self.alpha = al_min 
			else:
			 self.alpha = al 

		else:
			self.alpha = float(self.alpha)

	def getSchem(self,xstr):

		for sc in xstr.findall("MiningField") :
			mfld =sc.attrib['name']
			idx = []
			if sc.find("Extension") != None :
				# idx最大値計算
				idxmax = 0 
				for aidx in sc.find("Extension").findall("alphabetIndex"):
					if int(aidx.attrib['index']) > idxmax:
						idxmax = int(aidx.attrib['index'])
				if idxmax>0	:
					idx = [None] * (idxmax+1)

				for aidx in sc.find("Extension").findall("alphabetIndex"):
					idxno = int(aidx.attrib['index'])
					if idx[idxno] == None :
						idx[idxno] =[] 
					idx[idxno].append( aidx.attrib['alphabet'])

				self.pidx[mfld] = idx
				
	def nodeDiv(self,xstr):

		score = {}
		scal  = 0.0
		smax  = 0.0
		c_p   = 0.0

		for sc in xstr.findall("ScoreDistribution") :
			score[sc.attrib['value']] = sc.attrib['recordCount'] 
			scal = scal + float(sc.attrib['recordCount'])
			if float(sc.attrib['recordCount']) > smax  :
				smax = float(sc.attrib['recordCount'])	 
				
		if self.scoreMin == None or self.scoreMin > scal :
			self.scoreMin = scal
			
		if self.scoreMax == None or self.scoreMax < scal :
			self.scoreMax = scal 

		if xstr.find("Extension") != None :
			if xstr.find("Extension").attrib['name'] == "complexity penalty" :
				c_p = float(xstr.find("Extension").attrib['value'])
			
		#リーフ処理		
		if xstr.find("Node") == None or c_p < self.alpha :
			id = self.ncount
			self.ncount += 1 
			self.nodes.append({"label":self.condCK(xstr),"id":str(id),"nodeclass":"type-leaf","score":score,"scal":smax})
			return id

		id = self.ncount
		self.ncount += 1 
		
		fld = ""
		for child in xstr.findall("Node"):
			toId = self.nodeDiv(child)
			fld  = self.getFld(child)
			self.edges.append( { "source":str(id) ,"target":str(toId),"id":"%d-%d"%(id,toId) } )

		#lbl= "<table><tr><td align='center'>#{condCK(xstr)}<br/></td></tr><tr><td><br/></td></tr><tr><td align='center'>#{fld}<br/></td></tr></table>"
		lbl = "%s@%s"%(self.condCK(xstr),fld)
		self.nodes.append( { "label":lbl ,"id":str(id) ,"nodeclass":"type-node","score":score ,"scal":smax} )

		return id


	def __init__(self,fn,alpha):
		self.alpha = alpha
		xmlrt = ET.parse(fn).getroot()
		self.timestamp = xmlrt.find("Header").find("Timestamp").text
		self.dd = []
		for ddlist in xmlrt.find("DataDictionary").iter("DataField"):
			self.dd.append(ddlist.attrib['name'])

		self.nodes = []
		self.edges = []
		self.pidx = {}
		self.scoreMin = None
		self.scoreMax = None
		self.ncount = 0
		self.setAlpha(xmlrt.find("TreeModel"))
		self.getSchem(xmlrt.find("TreeModel").find("MiningSchema"))
		self.nodeDiv (xmlrt.find("TreeModel").find("Node") )

	def nodeList(self,barFLG=False):
		strl=[]
		for val in self.nodes :
			c_str=[]
			scal =0.0
			for k,v in val["score"].items():
				c_str.append( "{name:\"%s\",csvValue:\"%s\",smax:\"%s\"}"%(k,v,val['scal'])	)
				scal += float(v)

			if (self.scoreMax - self.scoreMin) == 0:
				size = "NaN"
			else:	
				size = float( scal - self.scoreMin ) / float( self.scoreMax - self.scoreMin ) + 1.0
			
			#str << "\t#{val['id']}:{label:\"#{val['label']}\",id:\"#{val['id']}\",nodeclass:\"#{val['nodeclass']}\",score:[#{c_str.join(',')}],sizerate:\"#{size}\"}"
			strl.append("\t%s:{label:\"%s\",id:\"%s\",nodeclass:\"%s\",score:[%s],sizerate:\"%s\"}"%(val['id'],val['label'],val['id'],val['nodeclass'],",".join(c_str),str(size)))

		return ",\n".join(strl)

	def edgeList(self):
		strl=[]
		for val in self.edges:
			strl.append( "\t{source:\"%s\",target:\"%s\",id:\"%s\"}"%(val['source'],val['target'],val['id']))

		return ",\n".join(strl)

	def legendList(self):
		strl=[]
		for k in self.nodes[0]["score"].keys():
			strl.append("\"%s\""%(k))
		return ",".join(strl)

	def indexList(self):
		strA=[]
		for k,v in self.pidx.items():
			strl=[]
			if v == None:
				continue
			
			for i in range(len(v)):
				if v[i] :
					strl.append( "\"%s\""%(','.join(v[i]))) 

			strA.append( "{name:\"%s\",val:[%s]}"%(k,','.join(strl)) )

		return ",\n".join(strA)


def mdtree(i,o,alpha=None,bar=False):

	iFile = i
	oFile = o
	pm =  Pmml(iFile,alpha)
	#nodedata=pm.nodeList(barflg)
	#edgedata=pm.edgeList
	#legenddata=pm.legendList
	#indexdata=pm.indexList
	#d_max = pm.data_max

	if bar :
		graph_dips ='''
		/*barグラフ挿入*/
	nodeEnter
		.append("g")
		.attr("class","bar")
		.selectAll(".arc").data(function(d) {{ return d.score; }})
		.enter()
		.append("rect")
		.attr("class", "arc")
		.attr("x", function(d,i){{ return -barSizeMaX/2+i*(barSizeMaX/legands.length)+rPading; }})
		.attr("y", function(d)  {{ return -(barSizeMaX/d.smax*d.csvValue-barSizeMaX/2); }})
		.attr("width", (barSizeMaX/legands.length-rPading*2))
		.attr("height", function(d) {{ return barSizeMaX/d.smax*d.csvValue; }})
		.style("fill", function(d,i){{ return dictColor(i); }})
		.on("mouseover", function(d) {{
			d3.select("#tooltip")
				.style("left", (d3.event.pageX+10) +"px")
				.style("top", (d3.event.pageY-10) +"px")
				.select("#value")
				.text( d.name + " : " + d.csvValue );
			d3.select("#tooltip").classed("hidden",false);
		}})
		.on("mouseout", function() {{
			d3.select("#tooltip").classed("hidden", true);
		}});
	function calSize(d){{}}
		''' 

	else:
		graph_dips ='''
	/*Pieグラフ挿入*/
	nodeEnter
		.append("g")
		.attr("class","pie")
		.selectAll(".arc").data(function(d) {{ return pie(d.score); }})
		.enter()
		.append("path")
		.attr("class", "arc")
		.attr("d", d3.svg.arc().outerRadius(radius))
		.style("fill", function(d,i) {{ return dictColor(i); }})
    .on("mouseover", function(d) {{
			d3.select("#tooltip")
				.style("left", (d3.event.pageX+10) +"px")
				.style("top", (d3.event.pageY-10) +"px")
				.select("#value")
				.text( d.data.name + " : " + d.data.csvValue );
			d3.select("#tooltip").classed("hidden",false);
		}})
		.on("mouseout", function(){{
			d3.select("#tooltip").classed("hidden", true);
    }});
	function calSize(d){{}}
		''' 

	html = sys.stdout
	if not oFile ==  None :
		html = open(oFile,"w")


	outTemplate ='''
	<html lang="ja">
	<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<style type="text/css">
	  p.title {{ border-bottom: 1px solid gray; }}
		g > .type-node > rect {{ stroke-dasharray: 10,5; stroke-width: 3px; stroke: #333; fill: white; }}
		g > .type-leaf > rect {{ stroke-width: 3px; stroke: #333; fill: white; }}
		.edge path {{  fill: none;  stroke: #333; stroke-width: 1.5px; }}
		svg >.legend > rect {{ stroke-width: 1px; stroke: #333; fill: none; }}
		svg > .pindex > .pindexL > rect {{ stroke-width: 1px; stroke: #333;  fill: none; }}

	#tooltip{{
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
  </style>
	</head>
	<body>
	<div id="attach">
  	<svg class="main-svg" id="svg-canvas" height="100000" width="100000"></svg>
	</div>
	<script>
	{dgreejs}

	/*--- dagre-d3-simple.js -----*/
	/*
 	*  Render javascript edges and nodes to the svg.  This method should be more
	*  convenient when data was serialized as json and node definitions would be duplicated
	*  if edges had direct references to nodes.  See state-graph-js.html for example.
	*/
	function renderJSObjsToD3(nodeData, edgeData, svgSelector) {{
		var nodeRefs = [];
		var edgeRefs = [];
		var idCounter = 0;

		edgeData.forEach(function(e){{
			edgeRefs.push({{
				source: nodeData[e.source],
				target: nodeData[e.target],
				label: e.label,
				id: e.id !== undefined ? e.id : (idCounter++ + "|" + e.source + "->" + e.target)
			}});
		}});
		
		// これ必要？
		for (var nodeKey in nodeData) {{
	    if (nodeData.hasOwnProperty(nodeKey)) {{
  	    var u = nodeData[nodeKey];
    	  if (u.id === undefined) {{
      	  u.id = nodeKey;
	      }}
  	    nodeRefs.push(u);
    	}}
		}}
		renderDagreObjsToD3({{ nodes: nodeRefs, edges: edgeRefs }}, svgSelector);
	}}

	/*
 	*  Render javscript objects to svg, as produced by  dagre.dot.
 	*/

	function renderDagreObjsToD3(graphData, svgSelector) 
	{{
		/* 描画用設定値 */
		var radius = 10.0; 		// 円グラフ最小半径
		var rPading = 2.0; 		// 円隙間サイズ
		var rectSize = radius*4.0+rPading*2.0; // 円格納枠サイズ
		var barSizeMaX = radius*4.0; // barサイズMAX
		var charH= 18.0; 			 // 文字高さ
		var legendSize = 16.0; // 凡例マーカーサイズ
		var tMaxX=0;  			// テーブル表示サイズX
		var tMaxY=0;	 			// テーブル表示サイズX
		var tPadding=2.0; 	// テーブル隙間サイズX
		var pie = d3.layout.pie() 
    	.sort(null)
    	.value(function(d) {{ return d.csvValue; }}); 

		/* ノードデータ,エッジデータ,描画場所*/
		var nodeData = graphData.nodes;
		var edgeData = graphData.edges;
		var svg = d3.select(svgSelector);
		
		// エッジ種類定義
		if (svg.select("#arrowhead").empty()) {{
			svg.append('svg:defs').append('svg:marker')
			.attr('id', 'arrowhead')
			.attr('viewBox', '0 0 10 10')
			.attr('refX', 8)
			.attr('refY', 5)
			.attr('markerUnits', 'strokewidth')
			.attr('markerWidth', 8)
			.attr('markerHeight', 5)
      .attr('orient', 'auto')
      .attr('style', 'fill: #333')
      .append('svg:path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 z');
		}}

		/* 描画領域初期化 */
		svg.selectAll("g").remove();	
  	var svgGroup = svg.append("g");

		/* ------------------------------- 
			ノード関係 
		------------------------------- */
		/* ノード領域追加 */
		var nodes = svgGroup
	    .selectAll("g .node")
  	  .data(nodeData);

		/* ノード 属性追加 cl	ass & id */
		var nodeEnter = nodes
    	.enter()
			.append("g")
			.attr("class", function (d) {{
			if (d.nodeclass) {{  return "node " + d.nodeclass; }} 
			else             {{  return "node"; }}
    }})
    .attr("id", function (d) {{
      return "node-" + d.id;
    }})
    
		/* 枠追加 */
  	nodeEnter.append("rect").attr("class", "body");

		/* ノードHEADラベル追加 */
		nodeEnter
			.append("text")
			.attr("class", "head")
			.attr("text-anchor", "middle")
			.text(function (d) {{
				var sp = d.label.split("@") ;
				return sp[0];
		}});

		/* ノードFOOTラベル追加 */
		nodeEnter
    	.append("text")
    	.attr("class", "foot")
    	.attr("text-anchor", "middle")
    	.text(function (d) {{
    		var sp = d.label.split("@") 
    		if(sp.length < 2){{ return ""; }} 
    		else						 {{ return sp[1];}}
    	}});

	  /* グラフ挿入 */
		{graph_dips}

		/* ノードサイズ設定*/
		var nodeSize = []
		nodes.selectAll("g text").each(function (d) {{
			if(nodeSize[d.id]==undefined){{
				nodeSize[d.id]=[rectSize,rectSize]
			}}
			var bbox = this.getBBox();
			nodeSize[d.id][1]+=charH 
			if(nodeSize[d.id][0]<bbox.width){{ nodeSize[d.id][0]=bbox.width }} 
		}})

		nodes
	    .each(function (d,i) {{
   	   d.width = nodeSize[i][0]; 
    	  d.height = nodeSize[i][1];
    	}});

		/* ------------------------------- 
			エッジ関係 
		------------------------------- */
		var edges = svgGroup
			.selectAll("g .edge")
			.data(edgeData);

		var edgeEnter = edges
			.enter()
			.append("g")
			.attr("class", "edge")
			.attr("id", function (d) {{ return "edge-" + d.id; }})

		edgeEnter
			.append("path")
			.attr("marker-end", "url(#arrowhead)");

		/* ------------------------------- 
			凡例関係 
		------------------------------- */
		var legandX=0; // 凡例表示サイズX
		var legandY=0; // 凡例表示サイズY

		var legend = svg.append("svg")
			.attr("class", "legend")
			.selectAll("g")
      .data(legands)
    	.enter().append("g")
      .attr("class","legandL")

  	legend
  		.append("rect")
			.attr("width" , legendSize)
			.attr("height", legendSize)
			.style("fill", function(d, i) {{ return dictColor(i); }});

	  legend.append("text")
      .attr("x", 20)
      .attr("y", 9)
      .attr("dy", ".35em")
      .text(function(d) {{ return d; }});

		svg.select("svg.legend")
			.append("text")
    	.attr("x", 0)
    	.attr("y", 9)
    	.attr("dy", ".35em")
			.text("Legend")

		svg.select("svg.legend")
		.each(function() {{
  	  dd=this.getBBox();
			tMaxX = dd.width;
			tMaxY = dd.height;
		}})
	
		svg.select("svg.legend")
			.selectAll("g.legandL")
			.each(function() {{
  	 		dd=this.getBBox();
  	 		if(legandX<dd.width){{ legandX = dd.width; }}
				legandY += dd.height;
				if(tMaxX<dd.width){{ tMaxX = dd.width; }}
			}})

		svg.select("svg.legend")
			.append("rect")
   		.attr("x", 0)
   		.attr("y", 18)
    	.attr("width" , legandX + tPadding*2)
    	.attr("height", legandY + tPadding*(legands.length+1))

		tMaxY += (charH+tPadding)*legands.length

		legend
			.attr("transform", function(d,i) {{
				return  "translate(0," + (charH+(charH+tPadding)*i+tPadding) + ")"; 
			}});

		/* ------------------------------- 
			パターンindex関係
		------------------------------- */
		var indexX_K =[]; // index表示サイズX_key
		var indexX_V =[]; // index表示サイズX_val
		var indexX_R =[]; // index表示サイズReal
		var indexY_S=[]; 		// index表示開始位置Y

		var iposY = tMaxY + (charH+tPadding)

  	var pindex = svg.append("svg")
      .attr("class", "pindex")
      .attr("y", iposY)
    	.selectAll("g")
      .data(ptnidxs)
    	.enter().append("g")
      .attr("class","pindexL")
		  .attr("id",(function(d,i) {{ return "a"+i; }}));

  	pindex
  		.append("text")
	  	.attr("class","name")
    	.text(function(d) {{ return d.name; }});

	  pindex
  		.append("text")
	 		.attr("class","headerK")
  		.text(function(d) {{ return "index";}});

	  pindex
		  .append("rect")
	 		.attr("class","headerK")

		pindex
  		.append("text")
	  	.attr("class","headerV")
    	.text(function(d) {{ return "alphabet";}});

	  pindex
	  	.append("rect")
	  	.attr("class","headerV")

		pindex
			.selectAll("g.pidx")
			.data(function(d){{return d.val}})
			.enter()
	  	.append("text")
	  	.attr("class","no")
    	.text(function(d,j) {{ return j+1 ;}});

		pindex
			.selectAll("g.pidx")
			.data(function(d){{ return d.val; }})
			.enter()
	  	.append("rect")
	  	.attr("class","no")

		pindex
			.selectAll("g.pidx")
			.data(function(d){{ return d.val}})
			.enter()
	  	.append("text")
	  	.attr("class","idx")
    	.text(function(d,j) {{ return d ;}});

		pindex
			.selectAll("g.pidx")
			.data(function(d){{ return d.val }})
			.enter()
	  	.append("rect")
	  	.attr("class","idx")

		//幅チェック
		var indexYT = (charH*2+tPadding);
		for(var i=0 ;i<ptnidxs.length;i++){{
			var indexX_KT = 0;
			var indexX_VT = 0;

			svg.select("svg.pindex")
				.selectAll("#a"+i)
				.selectAll("text.name")
				.each(function() {{
  				var dd=this.getBBox();
					if(tMaxX<dd.width){{ tMaxX = dd.width;}}
					indexX_R[i]=dd.width
				}})

			svg.select("svg.pindex")
				.selectAll("#a"+i)
				.selectAll("text.headerK")
				.each(function() {{
  	  		var dd=this.getBBox();
  	 			if(indexX_KT<dd.width){{ indexX_KT = dd.width;}}
				}})


			svg.select("svg.pindex")
				.selectAll("#a"+i)
				.selectAll("text.headerV")
				.each(function() {{
  		  	var dd=this.getBBox();
  		 		if(indexX_VT<dd.width){{ indexX_VT = dd.width;}}
				}})

			svg.select("svg.pindex")
				.selectAll("#a"+i)
				.selectAll("text.no")
				.each(function() {{
  	  		var dd=this.getBBox();
  	 			if(indexX_KT<dd.width){{ indexX_KT = dd.width;}}
				}})

			svg.select("svg.pindex")
				.selectAll("#a"+i)
				.selectAll("text.idx")
				.each(function() {{
  	  		var dd=this.getBBox();
  	 			if(indexX_VT<dd.width){{ indexX_VT = dd.width; }}
				}})

			indexX_K.push(indexX_KT)
			indexX_V.push(indexX_VT)
			
			if(indexX_R[i]<indexX_VT+indexX_KT+tPadding*2){{
				indexX_R[i]=indexX_VT+indexX_KT+tPadding*2
			}}
		
			if(tMaxX<indexX_R[i]){{ tMaxX = indexX_R[i]; }}
			indexY_S.push(indexYT)
			indexYT += (ptnidxs[i].val.length+3)*(charH+tPadding);
		}}

		if (ptnidxs.length!=0){{
			svg.select("svg.pindex")
				.append("text")
				.attr("y", 9)
    		.attr("dy", ".35em")
				.text("Alphabet Index")
		}}

		//グループ内配置
		for(var i=0 ;i<ptnidxs.length;i++){{
			arrange = svg.select("svg.pindex").selectAll("#a"+i)
			arrange
				.selectAll("text.headerK")
				.attr("x",function(d,j){{ return tPadding; }})
				.attr("y",function(d,j){{ return (charH+tPadding); }})

			arrange
				.selectAll("text.headerV")
				.attr("y",function(d,j){{ return (charH+tPadding); }})
				.attr("x",function(d,j){{ return indexX_K[i]+tPadding*3; }})

			arrange
				.selectAll("text.no")
				.attr("x",function(d,j){{ return tPadding; }})
				.attr("y",function(d,j){{ return (j+2)*(charH+tPadding); }})

			arrange
				.selectAll("text.idx")
				.attr("y",function(d,j){{ return (j+2)*(charH+tPadding); }})
				.attr("x",function(d,j){{ return indexX_K[i]+tPadding*3; }})

			arrange
				.selectAll("rect.headerK")
				.attr("width",function(d,j){{ return indexX_K[i]+tPadding*2; }})
				.attr("height",function(d,j){{ return charH+tPadding; }})
				.attr("y",function(d,j){{ return tPadding; }})

			arrange
				.selectAll("rect.headerV")
				.attr("width",function(d,j){{ return indexX_V[i]+tPadding*2; }})
				.attr("height",function(d,j){{ return charH+tPadding; }})
				.attr("x",function(d,j){{ return indexX_K[i]+tPadding*2 }})
				.attr("y",function(d,j){{ return tPadding; }})

			arrange
				.selectAll("rect.no")
				.attr("width",function(d,j){{ return indexX_K[i]+tPadding*2; }})
				.attr("height",function(d,j){{ return charH+tPadding; }})
				.attr("y",function(d,j){{ return (j+1)*(charH+tPadding)+tPadding; }})

			arrange
				.selectAll("rect.idx")
				.attr("width",function(d,j){{ return indexX_V[i]+tPadding*2; }})
				.attr("height",function(d,j){{ return charH+tPadding; }})
				.attr("x",function(d,j){{ return indexX_K[i]+tPadding*2; }})
				.attr("y",function(d,j){{ return (j+1)*(charH+tPadding)+tPadding; }})
		}}

		//全体配置
		svg.select("svg.pindex")
  		.selectAll("g.pindexL")
			.attr("transform", function(d,i) {{ 
				var rtnstr = "translate(0," + indexY_S[i] + ")"; 
				return rtnstr;
			}});

		// Add zoom behavior to the SVG canvas
  	svgGroup.attr("transform", "translate("+tMaxX+", 5)")

	  svg.call(d3.behavior.zoom().on("zoom", function redraw() {{
			dx =  tMaxX + d3.event.translate[0]
			dy =  5 + d3.event.translate[1]
			svgGroup.attr("transform",
    	  "translate(" + dx +"," + dy+ ")" + " scale(" + d3.event.scale + ")");
	  }}));
  
  	// Run the actual layout
  	dagre.layout()
   		.nodes(nodeData)
    	.edges(edgeData)
    	.run();

		/* ------------------------------- 
			ノード表示位置移動
	 	--------------------------------- */
  	nodes
    	.attr("transform", function (d) {{
      	return "translate(" + d.dagre.x + "," + d.dagre.y + ")";
	    }})
			.selectAll("g.node rect.body")
    	.attr("rx", 5)
    	.attr("ry", 5)
    	.attr("x", function (d) {{ return -(rectSize/2);}})
    	.attr("y", function (d) {{ return -(rectSize/2);}})
    	.attr("width", function (d) {{ return rectSize;}})
    	.attr("height", function (d) {{ return rectSize; }});

  	nodes
    	.selectAll("text.foot")
    	.attr("transform", function (d) {{
      	return "translate(" + 0 + "," + (d.height/2) + ")";
	    }});

  	nodes
    	.selectAll("text.head")
    	.attr("transform", function (d) {{
      	return "translate(" + 0   + "," + -( radius*2+rPading*2) + ")";
			}});

	  nodes.selectAll("g.pie")
  	  .attr("transform", function (d) {{ return "scale("+ d.sizerate +")" ;}} );
		/* ------------------------------- 
			エッジ表示位置移動
		--------------------------------- */
		edges
    	.selectAll("path")
    	.attr("d", function (d) {{

      	var points = d.dagre.points.slice(0);
      	points.unshift(dagre.util.intersectRect(d.source.dagre, points[0]));

				var preTarget = points[points.length - 2];
				var target = dagre.util.intersectRect(d.target.dagre, points[points.length - 1]);

				//  This shortens the line by a couple pixels so the arrowhead won't overshoot the edge of the target
				var deltaX = preTarget.x - target.x;
				var deltaY = preTarget.y - target.y;
				
				var m = 2 / Math.sqrt(Math.pow(deltaX, 2) + Math.pow(deltaY, 2));
				points.push({{
					x: target.x + m * deltaX,
					y: target.y + m * deltaY
				}});

				return d3.svg.line()
					.x(function (e) {{ return e.x; }})
        	.y(function (e) {{ return e.y; }})
        	.interpolate("bundle")
        	.tension(.8)(points);
			}});

  	edges
    	.selectAll("g.label")
    	.attr("transform", function (d) {{
      	var points = d.dagre.points;
      	if (points.length > 1) {{
        	var x = (points[0].x + points[1].x) / 2;
        	var y = (points[0].y + points[1].y) / 2;
        	return "translate(" + (-d.bbox.width / 2 + x) + "," + (-d.bbox.height / 2 + y) + ")";
      	}}
      	else {{
        	return "translate(" + (-d.bbox.width / 2 + points[0].x) + "," + (-d.bbox.height / 2 + points[0].y) + ")";
      	}}
    	}});

		var tooltip = d3.select("body").append("div")
			.attr("id", "tooltip")
			.attr("class", "hidden")
			.append("p")
			.attr("id", "value")
			.text("0");
		}}

		// 色決定関数
		function dictColor(i){{
			var colorSet = [ [70,130,180],[144,238,144],[238,232,170],
 											[139,0,0],[0,139,0],[0,0,139]]
			var sur = i % colorSet.length;
			var div = (i-sur) / colorSet.length;
			var r =colorSet[sur][0]+div*20;
			var g =colorSet[sur][1]+div*20;
			var b =colorSet[sur][2]+div*20;
			if(r>255){{ r=255; }}
			if(g>255){{ g=255; }}
			if(b>255){{ b=255; }}
			return "rgb(" + r + ","+ g + "," + b + ")"
		}}
		var nodes=
		{{
			{nodedata}
		}};

		var edges=[
			{edgedata}
		];

		var legands=[
			{legenddata}
		];

		var ptnidxs=[	
			{indexdata}
		];
		
		renderJSObjsToD3(nodes, edges, ".main-svg");
	</script>
	</body>
	</html>
'''.format(dgreejs=vjs.ViewJs.dgreejsMin() , graph_dips=graph_dips,
						nodedata=pm.nodeList(bar) ,edgedata=pm.edgeList(),
						legenddata=pm.legendList(),indexdata=pm.indexList())

	html.write(outTemplate)

	if not oFile ==  None :
		html.close()


if __name__ == '__main__':

#i,o,v,f,k=None,title=None,height=None,width=None,cc=None,footer=None):
	'''
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model1.pmml","./out1.html")
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model2.pmml","./out2.html")
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model3.pmml","./out3.html")
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model4.pmml","./out4.html")
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model5.pmml","./out5.html")
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model6.pmml","./out6.html")
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model7.pmml","./out7.html")


	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model1.pmml","./out1.html",bar=True)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model2.pmml","./out2.html",bar=True)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model3.pmml","./out3.html",bar=True)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model4.pmml","./out4.html",bar=True)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model5.pmml","./out5.html",bar=True)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model6.pmml","./out6.html",bar=True)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model7.pmml","./out7.html",bar=True)
	'''

	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model1.pmml","./out1.html",bar=True,alpha=0.01)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model2.pmml","./out2.html",bar=True,alpha=0.01)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model3.pmml","./out3.html",bar=True,alpha=0.01)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model4.pmml","./out4.html",bar=True,alpha=0.01)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model5.pmml","./out5.html",bar=True,alpha=0)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model6.pmml","./out6.html",bar=True,alpha=0)
	mdtree("/Users/nain/work/git/view/mdtree/check/indat/model7.pmml","./out7.html",bar=True,alpha=1)

