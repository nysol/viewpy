#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.viewjs as vjs



class dataForGraphDsp(object):

	def __init__(self):
		self.xcount   = 0 
		self.xlables  = {}
		self.ycount   = 0 
		self.ylables  = {}
		self.keycount = 0
		self.klables  = {}

		self.maxValue = 0 
		self.minValue	= 0 
		self.maxLeg   = 0
		self.maxValueSize = 0
		self.linedata  = []


	def calMaxLeg(self,val):

		if val == None:
			return 

		tmpSize = len(val)
		if tmpSize > self.maxLeg:
			self.maxLeg = tmpSize


	def checkValue(self,val):

		if val == None or val == "":  # 値の項目がnullの場合0にする 
			val =  "0" 

		if not re.match(r'^-?([0-9]\d*|0)(\.\d+)?$',val): # 棒グラフの値の数値チェック
			raise ValueError("%s is not a numeric"%(val))

		if len(val) > self.maxValueSize:
			self.maxValueSize = len(val)

		if float(val) > self.maxValue:
			self.maxValue = float(val)

		if float(val) < self.minValue:
			self.minValue = float(val)

	def addData(self,val):

		self.linedata.append(val)

	def addAxis(self,xy):
		if len(xy) == 0 :
			self.xcount +=1
			self.ycount +=1
			
		else :

			if not xy[0] in self.xlables :
				self.xlables[xy[0]] = 1 
				self.xcount +=1

			if len(xy) > 1:
				if not xy[1] in self.ylables :
					self.ylables[xy[1]] = 1 
					self.ycount +=1

	def adjustXMax(self,xMax):
		if self.xcount > xMax :
			self.ycount = self.xcount / xMax
			self.xcount = xMax
		else:
			self.ycount = 1

	def addKeyLabel(self,key):

		if not key in self.klables :
			self.klables[key] = 1
			self.keycount +=1
			
	def dataStr(self):
		return ",".join(self.linedata) 





# iFile(inputファイル)
# legendKey(キーの項目)
# barValue(値の項目)
# keys
# yBar(keyの値:行の項目)
# xBar(keyの値:列の項目)
def __makeData(imod, legendKey, barValue,kx=None,ky=None):

	rtn = dataForGraphDsp()


	keys = []
	if kx :
		keys.append(kx)
	if ky :
		keys.append(ky)

	kvstr = []
	for flds,top,bot in imod.getline(k=keys , otype='dict',q=True):

		if top == True:
			keyhead = [] 
			keyfld  = [] 
			for key in keys:
				keyhead.append("\"%s\":\"%s\""%(key,flds[key]))
				keyfld.append(flds[key]) 
				
			if len(keyhead) > 0:
				kvstr.append(",".join(keyhead))

			rtn.addAxis(keyfld)


		rtn.calMaxLeg(flds[legendKey])
		rtn.addKeyLabel(flds[legendKey])
		rtn.checkValue(flds[barValue])

		kvstr.append( "\"_%s\":\"%s\""%(flds[legendKey],flds[barValue]) )

		if bot == True : 

			rtn.addData("{" + ",".join(kvstr) + "}")
			kvstr =[]

	return  rtn


def mbar(i,o,v,f,k=None,title=None,height=None,width=None,cc=None,footer=""):
	"""
	CSVデータから棒グラフ(HTML)を作成する
	1次元グリッド、２次元グリッドのグラフ表示が可能
	マウススクロールで拡大、縮小、マウスドラッグで画像の移動が可能
	"""

	# arg check
	# i : str | list | nysol object
	# o : str
	# v : str (fldname)
	# f : str (fldname)
	# k : str | list | None (fldname size<2) => kx,ky
	# title  : str | None
	# height : int | None
	# width  : int | None
	# cc : str | int | None
	# footer : str | None

	# i
	if isinstance( i , ( str ,list ) ):
		imod = nm.mread(i=i)
	elif isinstance( i ,nm.nysollib.core.NysolMOD_CORE):
		imod = i
	else:
		raise TypeError("i= unsupport " + str(type(i)) )

	# o
	if isinstance( o , str ):
		oFile = o
	else:
		raise TypeError("o= unsupport " + str(type(o)) )

	if not isinstance( f , str ):
		raise TypeError("f= unsupport " + str(type(f)) )
		
	if not isinstance( v , str ):
		raise TypeError("v= unsupport " + str(type(v)) )


	#k
	kx = None
	ky = None
	if k == None or k=="":
		dim = 0 
	else:
		if type(k) is str:
			kk = k.split(',')
		elif type(k) is list:
			kk = k			
		else :
			raise TypeError("k= unsupport " + str(type(k)) )

		if len(kk) > 2:
			sys.stderr.write('warning : vaild dim <= 2 ')
			dim = 2 
		else:
			dim = len(kk)

		if dim == 2 :
			keys.append(kk[1])
			ky = kk[0]  
			kx = kk[1]
		elif dim == 1:
			kx = kk[0]

	# hight=
	if isinstance( height , (str , int ) ):
		svgHeight = int(height)  
	else:
		if height != None:
			sys.stderr.write('warning : height= unsupport '+ str(type(height)) + ': using default')
		if dim == 0 :
			svgHeight = 400 
		else :
			svgHeight = 250 

	# width=
	if isinstance( width , (str , int ) ):
		svgWidth = int(width) 
	else:
		if width != None:
			sys.stderr.write('warning : width= unsupport '+ str(type(width)) + ': using default')
		if dim == 0 :
			svgWidth = 600 
		else :
			svgWidth = 250 
	
	# cc=
	xMax = 5
	if cc != None:
		if dim != 1:
			raise Exception("cc= takes only k=A")

		if isinstance( cc , (str , int ) ):
			xMax = int(cc) 
		else:
			raise TypeError("cc= unsupport " + str(type(cc)) )
			
		
		if xMax < 1 :
			raise Exception("cc= takes more than 1")
		
	# titel=
	if title == None :
		title = ""
	if not isinstance( title , str ):
		raise TypeError("title= unsupport " + str(type(title)) )

	# footer
	if footer == None :
		footer = ""
	if not isinstance( footer , str ):
		raise TypeError("footer= unsupport " + str(type(footer)) )


	# キャンパスのマージン
	outerMarginL = 30
	outerMarginR = 30
	outerMarginT = 30
	outerMarginB = 30

	#keys[0]=>x,keys[1]=>y 
	gdsp = __makeData(imod, f, v, kx,ky)

	if dim==1:
		gdsp.adjustXMax(xMax)


	xCampusSize = gdsp.xcount  * svgWidth + outerMarginL + outerMarginR
	yCampusSize = gdsp.ycount  * svgHeight + outerMarginT + outerMarginB
	maxValueCount = len(str(gdsp.maxValue))
	maxLength = maxValueCount + maxValueCount / 3
	if maxLength < gdsp.maxValueSize:
		maxLength = gdsp.maxValueSize

	# 棒グラフ用SVGのマージン
	# 左は最大桁数+カンマの数*10(単位)+10(マージン)
	barMarginL = maxLength * 10 + 10
	barMarginR = 10
	barMarginT = 20
	# 下は最大桁数*10(単位)+30(マージン)
	barMarginB = gdsp.maxLeg * 10 + 30


	# ============
	# 文字列作成
	colorStyle =""
	if dim > 1 :
		colorStyle = '''
			var tmpKeys = d3.keys(data[0]).filter(function(key) {{ if(key !== "{key1}" && key !== "{key2}") {{ return key; }}}});
		'''.format(key1=keys[0],key2=keys[1])

	elif dim == 1:
		colorStyle = '''
		var tmpKeys = d3.keys(data[0]).filter(function(key) {{ if(key !== "{key1}") {{ return key; }} }} );
		'''.format(key1=keys[0])
	else:
		colorStyle = '''
			var tmpKeys = d3.keys(data[0]).filter(function(key) {{ if(key !== "{key1}") {{ return key; }} }} );
		'''.format(key1=None)

	# ============
	# TITLE用文字列作成
	titleMargin =20
	tmpX = (xCampusSize - outerMarginR) / 2 
	if title :
		titleStr = '''
var title = d3.select("svg").append("text")
      .attr("x", ({tmpX}))
      .attr("y", "{titleMargin}")
      .attr("text-anchor", "middle")
      .style("font-size", "13pt")
      .text("{title}");
'''.format(tmpX=tmpX,titleMargin=titleMargin,title=title)
	else:
		titleStr = ""


	# 2次元
	if dim > 1 :
		xdomain = "[\""+ "\",\"".join(list(gdsp.xlables.keys() )) + "\"]"
		ydomain = "[\""+ "\",\"".join(list(gdsp.ylables.keys() )) + "\"]"
		outLineStr = '''
var out_x = d3.scale.ordinal()
   .domain({xdomain})
   .rangeBands([0, out_axis_width]);

var out_x_axis = d3.svg.axis()
   .scale(out_x) //スケールの設定
   .orient("bottom");

var out_xaxis = d3.select("svg")
   .append("g")
   .attr("class", "axis")
   .attr("transform", "translate(" + outer_margin.left + "," + (out_axis_height + outer_margin.top) + ")")
   .call(out_x_axis);          

var out_y = d3.scale.ordinal()
   .domain({ydomain})          
   .rangeBands([0, out_axis_height]);

var out_y_axis = d3.svg.axis()
   .scale(out_y)
   .orient("left");

var out_yaxis = d3.select("svg")
   .append("g")
   .attr("class", "axis")
   .attr("transform", "translate(" + outer_margin.left + "," + outer_margin.top + ")") // x方向,y方向
   .call(out_y_axis);
'''.format(xdomain=xdomain,ydomain=ydomain)
	else:
		outLineStr = ""


	svgStr = '''
// 描画領域を作成(svgをデータ行分つくる)
var svg = d3.select("svg").selectAll(".bar")
     .data(data)
    .enter().append("svg")
    .attr("width", svgWidth)
    .attr("height", svgHeight)
     .attr("x", function(d,i) {{ 
        if (i < {xNum}) {{ return svgWidth*i + outer_margin.left ; }}
        else {{ return svgWidth*(i % {xNum}) + outer_margin.left; }} }}) // width+0, width+1,...width+xNum, width+0..
     .attr("y", function(d,i) {{ return  outer_margin.top + svgHeight * parseInt(i/{xNum}); }} ) // i/3を整数値で取得
     .attr("class", "bar")
     .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
'''.format(xNum=gdsp.xcount)


	# 1次元
	if dim==1 :
		titleY = barMarginT / 2
		graphTitle = '''
svg.append("text")
   .attr("class", "text")
   .style("text-anchor", "middle")
   .style("font-size", "10px")
   .attr("transform", "translate(0, -{titleY})")
   .text( function(d) {{ return d.{key1} }});
'''.format(titleY=titleY,key1=keys[0])

	else:
		graphTitle = ""


	comStr = '''
var command = d3.select("body").append("div")
      .attr("x", "430")
      .attr("y", "20")
      .attr("text-anchor", "left")
      .style("font-size", "14px")
      .text("{footer}");
'''.format(footer=footer)

	xZeroBar = ""
	if gdsp.minValue < 0 :
		xZeroBar = '''
svg.append("g")
   .attr("class", "x0 axis")
   .append("line")
   .attr("x1", 0)
   .attr("y1", y(0))
   .attr("x2",  inWidth )
   .attr("y2", y(0));
'''
	else:
		xZeroBar = ""
		
	html = sys.stdout
	if not oFile ==  None :
		html = open(oFile,"w")

	doc = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
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
  border-radius: 5px;
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

.axis text {{
    font: 11px
    font-family: sans-serif;
}}

.axis path,
.axis line {{
    fill: none;
    stroke: #000;
    shape-rendering: crispEdges;
}}
</style>
</head>
<body>
<script>
{d3jsMin}


var data = [
{dataStr}
];
// キャンパスサイズ
var out_w = {xCampusSize};
var out_h = {yCampusSize};

// キャンパスのマージン
var outer_margin = {{ top: {outerMarginT}, right: {outerMarginR}, bottom: {outerMarginB}, left: {outerMarginL} }};

// 凡例の位置

// 外側のx軸サイズ
var out_axis_width  = out_w - outer_margin.left - outer_margin.right;
var out_axis_height = out_h - outer_margin.top - outer_margin.bottom;

// 棒グラフ表示用SVGのマージン
var margin = {{ top: {barMarginT}, right: {barMarginR}, bottom: {barMarginB}, left: {barMarginL} }};

var svgWidth  = {svgWidth};
var svgHeight = {svgHeight};

var vbox_x = 0;
var vbox_y = 0;
var vbox_default_width = vbox_width = out_w;
var vbox_default_height = vbox_height = out_h;

var outline = d3.select("body").append("svg")
     .attr("width", out_w )
     .attr("height", out_h)
     .attr("viewBox", "" + vbox_x + " " + vbox_y + " " + vbox_width + " " + vbox_height);

var drag = d3.behavior.drag().on("drag", function(d) {{
    vbox_x -= d3.event.dx;      
    vbox_y -= d3.event.dy;      
    return outline.attr("translate", "" + vbox_x + " " + vbox_y);
  }});
  outline.call(drag);
  zoom = d3.behavior.zoom().on("zoom", function(d) {{
        var befere_vbox_width, before_vbox_height, d_x, d_y;
        befere_vbox_width = vbox_width;
        before_vbox_height = vbox_height;
        vbox_width = vbox_default_width * d3.event.scale;
        vbox_height = vbox_default_height * d3.event.scale;
        d_x = (befere_vbox_width - vbox_width) / 2;
        d_y = (before_vbox_height - vbox_height) / 2;
        vbox_x += d_x;
        vbox_y += d_y;
        return outline.attr("viewBox", "" + vbox_x + " " + vbox_y + " " + vbox_width + " " + vbox_height);
  }});
 outline.call(zoom); 

{titleStr}

//outlineのX軸
//outlineのY軸
{outLineStr}

// make colorlist
var color1 = d3.scale.category10();
var color2 = d3.scale.category20b();
var color3 = d3.scale.category20();
var color4 = d3.scale.category20c();
var cl = color1.range();
var colorList = cl.concat(color1.range());
colorList = colorList.concat(color2.range());
colorList = colorList.concat(color3.range());
colorList = colorList.concat(color4.range());

{colorStyle}

var dataNames = tmpKeys.map(function(d) {{ return d.substr(1); }});

// set color
var color = d3.scale.ordinal()
      .range(colorList)
      .domain(dataNames);

// レンジオブジェクト
// 棒グラフの横幅を0からwidthの間に、棒グラフの横幅を10%づつバディングして並べる
var inWidth = svgWidth - (margin.left + margin.right);
var x = d3.scale.ordinal()
    .rangeRoundBands([0, inWidth], .1);

// 棒グラフの縦幅を定義
var inHeight = svgHeight - margin.top - margin.bottom;
var y = d3.scale.linear()
    .range([inHeight, 0]);

// 棒グラフのx軸のオブジェクト
var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

// 棒グラフのy軸のオブジェクト
var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

data.forEach(function(d) {{
  d.datasets = color.domain().map(function(d1) {{
    return {{name: d1, value: +d["_" + d1]}};
  }});
}});

// 棒グラフのx軸のドメインの設定
x.domain(dataNames);

// 棒グラフのy軸のドメインの最小値、最大値の設定(0からdataのvalの最大値)
y.domain([ {minValue}, {maxValue} ]);

// 個々のsvg領域の描画
{svgStr}
{graphTitle}

// 棒グラフのx軸
svg.append("g")
   .attr("class", "x axis")
   .attr("transform", "translate(0," + inHeight + ")")
   .call(xAxis)
   .selectAll("text")
   .style("text-anchor", "end")
   .style("font-size", "10px")
   .attr("dx", "-.8em")
   .attr("dy", ".15em")
   .attr("transform", function(d) {{
     return "rotate(-90) translate(0,-10)"
   }});

// マイナス対応
{xZeroBar}

// 棒グラフのy軸
svg.append("g")
   .attr("class", "y axis")
   .call(yAxis);

svg.selectAll("rect")
    .data(function(d) {{ return d.datasets; }})
  .enter().append("rect")
    .attr("width", x.rangeBand())
    .attr("x", function(d) {{ return x(d.name); }} )
    .attr("y", function(d) {{ return y(Math.max(0, d.value)); }})
    .attr("height", function(d) {{ return Math.abs(y(d.value) - y(0)); }})
    .style("fill", "steelblue")
    .on("mouseover", function(d) {{
       d3.select("#tooltip")
         .style("left", (d3.event.pageX+10) +"px")
         .style("top", (d3.event.pageY-10) +"px")
         .select("#value")
         .text( d.name + " : " + d.value );
       d3.select("#tooltip").classed("hidden",false);
    }} )
    .on("mouseout", function() {{
       d3.select("#tooltip").classed("hidden", true);
    }});

var tooltip = d3.select("body").append("div")
    .attr("id", "tooltip")
    .attr("class", "hidden")
    .append("p")
      .attr("id", "value")
      .text("0");

{comStr}
</script>
</body>
</html>

'''.format(
	d3jsMin=vjs.ViewJs.d3jsMin(), 
	dataStr=gdsp.dataStr() ,xCampusSize=xCampusSize,
	yCampusSize=yCampusSize,outerMarginT=outerMarginT,
	outerMarginR=outerMarginR,outerMarginB=outerMarginB,
	outerMarginL=outerMarginL,barMarginT=barMarginT,
	barMarginR=barMarginR,barMarginB=barMarginB,
	barMarginL=barMarginL,
	svgWidth = svgWidth, svgHeight = svgHeight,
	titleStr=titleStr,
	outLineStr=outLineStr,colorStyle=colorStyle,
	minValue=gdsp.minValue, maxValue = gdsp.maxValue,
	svgStr =  svgStr, graphTitle = graphTitle , 
	xZeroBar=xZeroBar,comStr = comStr)

	html.write(doc)

	if not oFile ==  None :
		html.close()


#"""


if __name__ == '__main__':

#i,o,v,f,k=None,title=None,height=None,width=None,cc=None,footer=None):

	mbar("/Users/nain/work/git/view/mbar/check/data/input1.csv","./out0-1.html","人口","年代",footer="./mbar.py i=/Users/nain/work/git/view/mbar/check/data/input1.csv o=./out0-1.html v=人口 f=年代")
	mbar("/Users/nain/work/git/view/mbar/check/data/input2.csv","./out1-1.html","人口","年代",k="Pref", title="奈良県と北海道の年代ごとの人口" ,footer="./mbar.py")
	mbar("/Users/nain/work/git/view/mbar/check/data/input3.csv","./out2-1.html","回数","テーマパーク",k="性別,年代",footer="./mbar.py")
	mbar("/Users/nain/work/git/view/mbar/check/data/input3-mai.csv","./out2-8.html","回数","テーマパーク",k="性別,年代",title="マイナス")


