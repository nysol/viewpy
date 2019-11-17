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
def __makeData(iFile, legendKey, barValue,keys):

	rtn = dataForGraphDsp()

	kvstr = []

	for flds,top,bot in nm.readcsv(iFile).getline(k=keys , otype='dict',q=True):

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


#args=MCMD::Margs.new(ARGV,"i=,o=,title=,cc=,pr=,k=,f=,v=,--help","f=,v=")
#height=None,width=None,

def mpie(i,o,v,f,k=None,title=None,cc=None,pr=None,footer=""):

	# kからディメンジョン決定
	keys = []
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
		
		keys.append(kk[0])


	iFile = i
	oFile = o

	# グラフ用SVGの縦幅
	if pr == None or pr == "" :
		pieRadius = 160 
	else:
		pieRadius = pr
		
	pieBelt   = pieRadius # 表示半径

	# グラフ用SVGのマージン
	innerMargin = 10

	svgWidth  =  pieRadius * 2 + innerMargin *2
	svgHeight =  pieRadius * 2 + innerMargin *2

	# キャンパスのマージン
	outerMarginL = 30
	outerMarginR = 30
	outerMarginT = 30
	outerMarginB = 30

	xMax = 5
	if cc != None:
		if dim==1:
			xMax =  int(cc)
		else:
			raise Exception("cc= takes only k=A")
			
	if xMax < 1 :
		raise Exception("cc= takes more than 1")

	keyText = ""
	if dim == 2 :
		pieBelt = pieRadius / 2
		keyText= '''
    svg.append("text")
        .attr("dy", ".35em")
        .style("text-anchor", "middle")
        .text(function(d) {{ return d.{key1} + d.{key2}; }});
		'''.format(key1=keys[0],key2=keys[1])

	elif dim==1 :
		pieBelt = pieRadius / 2
		keyText= '''
		svg.append("text")
        .attr("dy", ".35em")
        .style("text-anchor", "middle")
        .text(function(d) {{ return d.{key1}; }});
		'''.format(key1=keys[0])

	#keys[0]=>x,keys[1]=>y 
	gdsp = __makeData(iFile, f, v, keys)

	if dim==1:
		gdsp.adjustXMax(xMax)

	
	legendWidth = gdsp.maxLeg * 10 + 30 + 30

	xCampusSize = gdsp.xcount  * svgWidth + legendWidth + outerMarginL + outerMarginR *2
	yCampusSize = gdsp.ycount  * svgHeight + outerMarginT + outerMarginB
	outAxisHeight = yCampusSize - outerMarginT - outerMarginB

	# ============
	# 文字列作成
	colorStyle =""
	if dim > 1 :
		colorStyle = '''
			color.domain( d3.keys(data[0]).filter(function(key) {{ if(key !== "{key1}" && key !== "{key2}") {{ return key; }}}}));
		'''.format(key1=keys[0],key2=keys[1])

	elif dim == 1:
		colorStyle = '''
		color.domain(d3.keys(data[0]).filter(function(key) {{ if(key !== "{key1}") {{ return key; }} }} ));
		'''.format(key1=keys[0])
	else:
		colorStyle = '''
		color.domain(d3.keys(data[0]).filter(function(key) {{ if(key !== "{key1}") {{ return key; }} }} ));
		'''.format(key1=None)


	# ============
	# TITLE用文字列作成
	titleMargin =20
	tmpX = (xCampusSize - outerMarginR * 2 - legendWidth) / 2
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
		xAxistransY = outerMarginL + outAxisHeight

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
   .attr("transform", "translate(" + {outerMarginL} + "," + {xAxistransY} + ")")
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
   .attr("transform", "translate(" + {outerMarginL} + "," + {outerMarginT} + ")") // x方向,y方向
   .call(out_y_axis);

'''.format(outerMarginL=outerMarginL,outerMarginT=outerMarginT,xAxistransY=xAxistransY,xdomain=xdomain,ydomain=ydomain)
	else:
		outLineStr = ""

	textHeight = 30
	legendMargin = 30
	legendHeight = gdsp.keycount * textHeight + legendMargin
	legendTextX = textHeight + 4
	legendTextY = textHeight / 2

	legendStr = '''
var legend = d3.select("svg").append("svg")
      .attr("class", "legend")
      .attr("width", "{legendWidth}")
      .attr("height", "{legendHeight}")
      .attr("x", leg_x)
    .selectAll("g")
      .data(color.domain().slice())
    .enter().append("g")
      .attr("transform", function(d, i) {{ return "translate(0, " + (i*{textHeight}+{legendMargin}) + ")"; }});

  legend.append("rect")
      .attr("width", {textHeight})
      .attr("height", {textHeight})
      .style("fill", color);

  legend.append("text")
      .attr("x", {legendTextX})
      .attr("y", {legendTextY})
      .attr("dy", ".35em")
      .text(function(d) {{ return d.substr(1); }});
'''.format(legendWidth=legendWidth,legendHeight=legendHeight,
						textHeight=textHeight,legendMargin=legendMargin,
						legendTextX=legendTextX,legendTextY=legendTextY)


	tmpX = innerMargin + pieRadius
	svgStr = '''
// 描画領域を作成(svgをデータ行分つくる)
var svg = d3.select("svg").selectAll(".pie")
     .data(data)
    .enter().append("svg")
    .attr("width", svgWidth)
    .attr("height", svgHeight)
     .attr("x", function(d,i) {{ // width+0, width+1,...width+xNum, width+0..
        if (i < {xNum}) {{ return svgWidth*i + outer_margin.left ; }}
        else {{ return svgWidth*(i % {xNum}) + outer_margin.left; }}
    	}}) 
     .attr("y", function(d,i) {{ return  outer_margin.top + svgHeight * parseInt(i/{xNum}); }}) // i/3を整数値で取得
      .attr("class", "pie")
    .append("g")
      .attr("transform", "translate({tmpX},{tmpX})");
'''.format(tmpX=tmpX,xNum=gdsp.xcount)

	comStr = '''
var command = d3.select("body").append("div")
      .attr("x", "430")
      .attr("y", "20")
      .attr("text-anchor", "left")
      .style("font-size", "10px")
      .text("{footer}");
'''.format(footer=footer)




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
var leg_x = out_w - outer_margin.right - {legendWidth};

// 外側のx軸サイズ
var out_axis_width  = out_w - outer_margin.left - outer_margin.right * 2 - {legendWidth};
var out_axis_height = out_h - outer_margin.top - outer_margin.bottom;


var radius = {pieRadius};
var pieBelt  = {pieBelt};

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

var innerRadius = radius - pieBelt;

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

// set color
var color = d3.scale.ordinal()
    .range(colorList);
// set domain to d3.scale.ordinal
{colorStyle}


// set inner radius and outer radius of pie chart
var arc = d3.svg.arc()
    .outerRadius(radius)       //pie outer radius
    .innerRadius(innerRadius); //pie inner radius

// make pie chart
var pie = d3.layout.pie() 
    .sort(null)                                 // invalidate sort
    .value(function(d) {{ return d.value; }}); // set value


// process of data
  data.forEach(function(d) {{
    d.datasets = color.domain().map(function(d1) {{
      //convert value from string to numeric(+)
      return {{name: d1, value: +d[d1]}};
    }});
  }});


// 個々のsvg領域の描画
{svgStr}

svg.selectAll(".arc")
    .data(function(d) {{ return pie(d.datasets); }})
  .enter().append("path")
    .attr("class", "arc")
    .attr("d", arc)
    .style("fill", function(d) {{ return color(d.data.name); }})
    .on("mouseover", function(d) {{
         d3.select("#tooltip")
           .style("left", (d3.event.pageX+10) +"px")
           .style("top", (d3.event.pageY-10) +"px")
           .select("#value")
        .text( d.data.name.substr(1) + " : " + d.data.value );

          d3.select("#tooltip").classed("hidden",false);
      }})
      .on("mouseout", function() {{
          d3.select("#tooltip").classed("hidden", true);
      }});

{keyText}

{legendStr}

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
	d3jsMin=vjs.ViewJs.d3jsMin(), dataStr=gdsp.dataStr() ,
	xCampusSize=xCampusSize,yCampusSize=yCampusSize,
	outerMarginT=outerMarginT,outerMarginR=outerMarginR,
	outerMarginB=outerMarginB,outerMarginL=outerMarginL,
	legendWidth=legendWidth,pieRadius=pieRadius,pieBelt=pieBelt,
	svgWidth = svgWidth, svgHeight = svgHeight,
	titleStr=titleStr,outLineStr=outLineStr,colorStyle=colorStyle,
	svgStr =  svgStr, keyText = keyText, 
	legendStr=legendStr,comStr = comStr)

	html.write(doc)

	if not oFile ==  None :
		html.close()


#"""


if __name__ == '__main__':

#i,o,v,f,k=None,title=None,height=None,width=None,cc=None,footer=None):

	mpie("/Users/nain/work/git/view/mpie/check/data/input1.csv","./out0-1.html","人口","年代",footer="./mbar.py i=/Users/nain/work/git/view/mbar/check/data/input1.csv o=./out0-1.html v=人口 f=年代")
	mpie("/Users/nain/work/git/view/mpie/check/data/input2.csv","./out1-1.html","人口","年代",k="Pref", title="奈良県と北海道の年代ごとの人口" ,footer="./mbar.py")
	mpie("/Users/nain/work/git/view/mpie/check/data/input3.csv","./out2-1.html","回数","テーマパーク",k="性別,年代",footer="./mbar.py")


