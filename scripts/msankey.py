#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.msankey as nvsank
import nysol.util as nu


helpMSG="""
----------------------------
#{$cmd} version #{$version}
----------------------------
概要) DAG(有向閉路グラフ)からsankeyダイアグラムをhtmlとして生成する。
書式) #{$cmd} i= f= v= [-nl] [h=] [w=] [o=] [t=] [T=] [--help]

  ファイル名指定
  i=     : 枝データファイル
  f=     : 枝データ上の2つの節点項目名
  v=     : 枝の重み項目名
  o=     : 出力ファイル(HTMLファイル)
  t=     : タイトル文字列
  h=     : キャンバスの高さ(デフォルト:500)
  w=     : キャンバスの幅(デフォルト:960)
  -nl    : 節点ラベルを表示しない

  その他
  T= : ワークディレクトリ(default:/tmp)
  --help : ヘルプの表示

入力形式)
有向閉路グラフを節点ペア、および枝の重みで表現したCSVファイル。

出力形式)
sankeyダイアグラムを組み込んだ単体のhtmlファイルで、
インターネットへの接続がなくてもブラウザがあれば描画できる。

備考)
本コマンドのチャート描画にはD3(http://d3js.org/)を用いている。
必要なrubyライブラリ: nysol/mcmd, json

例)
$ cat data/edge.csv 
node1,node2,val
a,b,1
a,c,2
a,d,1
a,e,1
b,c,4
b,d,3
b,f,1
c,d,2
c,e,2
d,e,1
e,f,3
n1,n2
$ #{$cmd} i=edge.csv f=node1,node2 v=val o=output.html
Copyright(c) NYSOL 2012- All Rights Reserved.

		"""

if "-help" in sys.argv or "--help" in sys.argv:
	print(helpMSG)
	exit()

args=margs.Margs(sys.argv,"i=,f=,v=,h=,w=,o=,t=,nl=,T=","i=,f=,v=")

footer = os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1:])

iFile		= args.file("i=","r")   # inputファイル名を取得(readable)
oFile		= args.file("o=","w")   # outputファイル名を取得(writable)
title		= args.str("t=")    # タイトル取得
height	= args.int("h=")	#size
width		= args.int("w=")	#size    
ef			= args.str("f=")
ev			= args.str("v=")

if args.keyValue["v="] :
	args.field("v=", iFile)  # 項目値をヘッダからチェック
	
if args.keyValue["f="] : # 凡例項目をヘッダからチェック
	args.field("f=", iFile)

nl=args.bool("nl=")

tmppath = args.str("T=")
if tmppath != None :
	import re
	tmppath = re.sub(r'/$', "", tmppath)


#if args.keyValue["k="] :
#	args.field("k=", iFile)      # key項目値取得

nvsank.msankey(
	iFile,oFile,ev,ef,
	title=title,h=height,w=width,
	nl=nl,T=tmppath
)

nu.mmsg.endLog(footer)


