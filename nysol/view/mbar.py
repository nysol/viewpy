#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import nysol.util.margs as margs
import nysol.mcmd as nm

#sys.path.append('../nysol/view')
import viewjs as vjs

#  (dataStr, countKey, maxValue, maxLeg, maxValueSize, minValue) = makeZeroDemData(iFile, legendKey, barValue)
# iFile(inputファイル)
# legendKey(キーの項目)     (例：年代)
# barValue(値の項目)     (例：人口)

class dataForGraphDsp(object):

	def __init__(self):
		self.xcount   = 0 
		self.xlables  = {}
		self.ycount   = 0 
		self.ylables  = {}
		self.keycount = 0
		self.klables  = {}

		self.maxValue = 0 # 構成量項目の最大値を取得 全体で一つ
		self.minValue	= 0 # 構成量項目の最小値を取得 全体で一つ
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

	def addAxis(self,x,y=None):

		if not x in self.xlables :
			self.xlables[x] = 1 
			self.xcount +=1

		if y!=None and not y in self.ylables :
			self.ylables[y] = 1 
			self.ycount +=1
			

	def addKeyLabel(self,key):

		if not key in self.klables :
			self.klables[key] = 1
			self.keycount +=1
			
	def dataStr(self):
		return ",".join(self.linedata) 

def __makeZeroDemData(iFile, legendKey, barValue):

	#rtn = dataForGraphDsp("var data = [\n{")
	rtn = dataForGraphDsp()

	kvstr = []

	for flds in nm.readcsv(iFile).getline(otype='dict'):

		rtn.calMaxLeg(flds[legendKey])

		rtn.addKeyLabel(flds[legendKey])

		rtn.checkValue(flds[barValue])
		
		kvstr.append("\"_%s\":\"%s\""%(flds[legendKey],flds[barValue]))

	rtn.xcount = 1
	rtn.ycount = 1
	rtn.addData("{" + ",".join(kvstr) + "}")

	return rtn


#  (dataStr, xcount, keycount, maxValue, maxLeg, maxValueSize, minValue) = makeOneDemData(iFile, primKey, legendKey, barValue)
# iFile(inputファイル)
# primKey(主キー)        (例：Pref)
# legendKey(キーの項目)     (例：年代)
# barValue(値の項目)     (例：人口)
def __makeOneDemData(iFile , legendKey, barValue, primKey):

	kvstr = []

	rtn = dataForGraphDsp()

	for flds,top,bot in nm.readcsv(iFile).getline(k=primKey , otype='dict',q=True):

		if top == True:
			kvstr.append("\"%s\":\"%s\""%(primKey,flds[primKey]))		
			rtn.addAxis(flds[primKey])


		rtn.calMaxLeg(flds[legendKey])

		rtn.addKeyLabel(flds[legendKey])

		rtn.checkValue(flds[barValue])

		kvstr.append( "\"_%s\":\"%s\""%(flds[legendKey],flds[barValue]) )

		if bot == True : 
			rtn.addData("{" + ",".join(kvstr) + "}")
			kvstr =[]

	return rtn



#  (dataStr, xcount, ycount, keycount, maxValue, maxLeg, maxValueSize, minValue) = makeTwoDemData(iFile, yBar, xBar, legendKey, barValue)
# iFile(inputファイル)
# yBar(keyの値:行の項目)
# xBar(keyの値:列の項目)
# legendKey(キーの項目)
# barValue(値の項目)
def __makeTwoDemData(iFile, legendKey, barValue, xBar, yBar):

	rtn = dataForGraphDsp()

	kvstr = []

	for flds,top,bot in nm.readcsv(iFile).getline(k=[yBar,xBar] , otype='dict',q=True):

		if top == True:
			kvstr.append("\"%s\":\"%s\",\"%s\":\"%s\""%(xBar,flds[xBar],yBar,flds[yBar]))
			rtn.addAxis(flds[xBar],flds[yBar])

		rtn.calMaxLeg(flds[legendKey])

		rtn.addKeyLabel(flds[legendKey])

		rtn.checkValue(flds[barValue])

		kvstr.append( "\"_%s\":\"%s\""%(flds[legendKey],flds[barValue]) )

		if bot == True : 

			rtn.addData("{" + ",".join(kvstr) + "}")
			kvstr =[]


	return  rtn




"""
args=margs.Margs(sys.argv,"i=,o=,title=,cc=,height=,width=,k=,f=,v=,--help","f=,v=")

入力ファイル
終了ファイル
タイトル
サイズ(z,y)
key(0,1,2)
横個数 (keyが一つの時のみ)
構成要素項目名(横軸)
構成量項目名(縦軸)
"""


def mbar(i,o,v,f,k=None,title=None,height=None,width=None,cc=None,footer=""):
	"""
概要) CSVデータから棒グラフ(HTML)を作成する
      1次元グリッド、２次元グリッドのグラフ表示が可能
      マウススクロールで拡大、縮小、マウスドラッグで画像の移動が可能

書式1) #{$cmd} [i=] [o=] [title=] [height=] [width=] [k=] [cc=] f= v= [--help]
                i=        : 入力データファイル名(CSV形式)
                o=        : 出力ファイル名(HTMLファイル)
                title=    : グラフのタイトル文字列を指定する
                height=   : 棒グラフ用描画枠の縦幅を指定する(default:250/1つの棒グラフは400)
                width=    : 棒グラフ用描画枠の横幅を指定する(default:250/1つの棒グラフは600)
                k=        : x軸,y軸に展開する属性項目名
                            k=なしの場合は棒グラフを1つ作成する
                            項目を1つ指定した場合は1次元の棒グラフ行列を、
                            項目を2つ指定した場合は2次元の棒グラフ行列を作成する
                            (y軸項目,x軸項目の順に指定)
                cc=       : 1行に表示する棒グラフの最大数を指定する(default:5)
                            1次元グラフのみで指定可能(k=1つ指定の場合)
                f=        : 構成要素項目名を指定する(必須)
                            データにnullが含まれる場合は無視する
                v=    : 構成量項目(棒グラフの高さを決定する項目)を指定する(必須)
                            データにnullが含まれる場合は0として扱う
                            先頭の0は無視する
                            数字以外の場合はエラーとなる
                --help    : ヘルプの表示

注意1)コマンドには、f=パラメータやk=パラメータで指定した項目を自動的に並べ替える機能はない
グラフに表示したい順に、あらかじめ並べ替えておく必要がある。
1次元、２次元グラフの場合はデータの先頭の棒グラフの表示順に並べられる

例1) 棒グラフを1つ描画する
dat1.csvファイルのAgeを構成要素項目に、Populationを構成量項目として棒グラフを1つ描画する

dat1.csv
Age,Population
10,310504
20,552339
30,259034.5555
40,0450818
50,1231572
60,1215966
70,641667

$ #{$cmd} i=dat1.csv v=Population f=Age o=result1.html

例2) 1次元の棒グラフ行列を描画する
dat2.csvファイルのAgeを構成要素項目に、Populationを構成量項目として棒グラフを描画する
k=パラメータにPref項目を指定しているので、
Pref項目の値をx軸(横方向)に展開した1次元の棒グラフ行列が描画される
title=パラメータでグラフのタイトルも指定している

dat2.csv
Pref,Age,Population
奈良,10,310504
奈良,20,552339
奈良,30,259034
奈良,40,450818
奈良,50,1231572
奈良,60,1215966
奈良,70,641667
北海道,10,310504
北海道,20,252339
北海道,30,859034
北海道,40,150818
北海道,50,9231572
北海道,60,4215966
北海道,70,341667

$ #{$cmd} i=dat2.csv k=Pref v=Population f=Age o=result2.html

例3) x軸上に表示する棒グラフの最大数を1とする

$ #{$cmd} i=dat2.csv k=Pref v=Population f=Age o=result3.html cc=1

例4) 2次元の棒グラフ行列を描画する
dat3.csvファイルのテーマパーク名を構成要素項目に、
Numberを構成量項目として棒グラフを描画する
k=パラメータにGenderとAge項目を指定して、Gender項目の値をx軸(横方向)に、
Age項目の値をy軸(縦方向)に展開した2次元の棒グラフ行列を描画する

dat3.csv
Gender,Age,テーマパーク名,Number
男性,30,デズニ,100
男性,30,UFJ,59
男性,30,梅屋敷,180
男性,40,デズニ,200
男性,40,UFJ,3
男性,40,梅屋敷,10
男性,50,デズニ,110
男性,50,UFJ,40
女性,30,梅屋敷,100
女性,30,デズニ,80
女性,30,UFJ,200
女性,40,デズニ,90
女性,40,UFJ,80
女性,40,梅屋敷,120
女性,50,デズニ,99
女性,50,UFJ,80
女性,50,梅屋敷,110

$ #{$cmd} i=dat3.csv k=Gender,Age v=Number f=テーマパーク名 o=result3.html title=性別と年代ごとのテーマパーク訪問回

args=margs.Margs(sys.argv,"i=,o=,title=,cc=,height=,width=,k=,f=,v=,--help","f=,v=")

入力ファイル => i
終了ファイル => o
タイトル  => title
サイズ(z,y) => hight,width
key(0,1,2) => k 
横個数 (keyが一つの時のみ) => cc
構成要素項目名(横軸)  => f
構成量項目名(縦軸)  => v
		"""
	#i=,o=,title=,cc=,height=,width=,k=,f=,v=

	# i,o,v,f,k=None,title=None,height=None,width=None,cc=None	
	# kからディメンジョン決定
	keys = [None,None]
	if k == None :
		dim = 0 
	elif type(k) is str:
		keys = k.split(',')
		dim = len(keys)
	elif type(k) is list:
		keys = k
		dim = len(keys)
	else :
		raise TypeError("k= unsupport " + str(type(k)) )
		  		
	if dim > 2:
		sys.stderr.write('warning : vaild dim <= 2 ') 

	iFile = i
	oFile = o
	title

	# グラフ用SVGの縦幅
	if height : 
		svgHeight = int(height)  
	else:
		if dim == 0 :
			svgHeight = 400 
		else :
			svgHeight = 250 

	# グラフ用SVGの縦幅
	if width : 
		svgWidth = int(width)  
	else:
		if dim == 0 :
			svgWidth = 600 
		else :
			svgWidth = 250 

	xMax = 5
	if cc != None:
		if dim==1:
			xMax =  int(cc)
		else:
			raise Exception("cc= takes only k=A")
			
	if xMax < 1 :
		raise Exception("cc= takes more than 1")

	# キャンパスのマージン
	outerMarginL = 30
	outerMarginR = 30
	outerMarginT = 30
	outerMarginB = 30

	if dim == 0 : 
		#makeZeroDemData(iFile, legendKey, barValue)
	  #dataStr, countKey, maxValue, maxLeg, maxValueSize, minValue  = makeZeroDemData(iFile, legendKey, barValue)
		#keyNum = countKey
		#gdsp = __makeZeroDemData(iFile, legendKey, barValue)
		gdsp = __makeZeroDemData(iFile, f, v)
		keyNum    = gdsp.keycount
		maxValue  = gdsp.maxValue
		minValue  = gdsp.minValue
		maxLeg    = gdsp.maxLeg
		maxValueSize = gdsp.maxValueSize
		xNum = gdsp.xcount  
		yNum = gdsp.ycount  


	elif dim == 1 : 
		#makeOneDemData(iFile, key1, legendKey, barValue)	
		#dataStr, xcount, countKey, maxValue, maxLeg, maxValueSize, minValue  = makeOneDemData(iFile, legendKey, barValue, key1)

		gdsp = __makeOneDemData(iFile, f, v, keys[0])

		keyNum    = gdsp.keycount #keyの数
		maxValue  = gdsp.maxValue 
		minValue  = gdsp.minValue
		maxLeg    = gdsp.maxLeg
		maxValueSize = gdsp.maxValueSize
		xNum   = gdsp.xcount      #主キーの数
		if xNum > xMax :
			yNum = xNum / xMax
			xNum = xMax
		else:
			yNum   = 1
		

	else:

		#makeTwoDemData(iFile, key1, key2, legendKey, barValue)
		# dataStr, xcount, ycount, keycount, maxValue, maxLeg, maxValueSize, minValue = makeTwoDemData(iFile, legendKey, barValue, key1, key2)
		
		gdsp = __makeTwoDemData(iFile, f, v, keys[1], keys[0])

		maxValue  = gdsp.maxValue 
		minValue  = gdsp.minValue
		maxLeg    = gdsp.maxLeg
		maxValueSize = gdsp.maxValueSize
		xNum   = gdsp.xcount   # x軸の棒グラフ数
		yNum   = gdsp.ycount   # y軸の棒グラフ数
		keyNum = gdsp.keycount # 凡例用キー数
		

#	0 : dataStr, 1     , 1         , countKey, maxValue, maxLeg, maxValueSize, minValue 	
#	1 :	dataStr, xcount, ttl/xmax , countKey, maxValue, maxLeg, maxValueSize, minValue 
#	2 :	dataStr, xcount, ycount   , keycount, maxValue, maxLeg, maxValueSize, minValue


	xCampusSize = xNum * svgWidth + outerMarginL + outerMarginR
	yCampusSize = yNum * svgHeight + outerMarginT + outerMarginB
	maxValueCount = len(str(maxValue))
	maxLength = maxValueCount + maxValueCount / 3
	if maxLength < maxValueSize:
		maxLength = maxValueSize


	# 棒グラフ用SVGのマージン
	# 左は最大桁数+カンマの数*10(単位)+10(マージン)
	barMarginL = maxLength * 10 + 10
	barMarginR = 10
	barMarginT = 20
	# 下は最大桁数*10(単位)+30(マージン)
	barMarginB = maxLeg * 10 + 30


	# ============
	# 文字列作成
	xZeroBar = ""

	if dim > 1 :
		colorStyle = '''
			var tmpKeys = d3.keys(data[0]).filter(function(key) {{ if(key !== "{key1}" && key !== "{key2}") {{ return key; }}}});
		'''.format(key1=keys[0],key2=keys[1])

	else:
		colorStyle = '''
		var tmpKeys = d3.keys(data[0]).filter(function(key) {{ if(key !== "{key1}") {{ return key; }} }} );
		'''.format(key1=keys[0])

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
'''.format(xNum=xNum)


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

	if minValue < 0 :
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
	minValue=minValue, maxValue = maxValue,
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


