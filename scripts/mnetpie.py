#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.mnetpie as nnpie
import nysol.util as nu


helpMSG="""
概要) Nodeデータ&EdgeファイルからグラフD3を使ったHTMLを作成する

書式) #{$cmd} ni= ei= ef= nf= [nodeSizeFld=] [nodeColorFld=] [edgeWidthFld=]  [edgeColorFld=] pieDataFld= pieTipsFld= picFld= o= -undirect

circle pieChart 画像 をNodeとして利用可能

		"""
if "-help" in sys.argv or "--help" in sys.argv:
	print(helpMSG)
	exit()

paralist=[
	"ei=","ni=","ef=","nf=","o=",
	"nodeSizeFld=","pieDataFld=","pieTipsFld=",
	"nodeTipsFld=","picFld=","nodeColorFld=",
	"edgeWidthFld=","edgeColorFld=",
	"--help","-undirect","-offline"
]
nparalist=[
	"ei=","ni=","ef=","nf="
]
args=margs.Margs(sys.argv,",".join(paralist),",".join(nparalist))

footer = os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1:])


# 必須
ni = args.file("ni=","r")   # inputファイル名を取得(readable)
ei = args.file("ei=","r")   # inputファイル名を取得(readable)
ef = args.str("ef=")    # 棒グラフの構成要素項目
nf = args.str("nf=")     # 棒グラフの値のキー
o  = args.file("o=","w")   # outputファイル名を取得(writable)



nnpie.mnetpie(
	ei,ni,ef,nf,o,
	nodeSizeFld=args.str("nodeSizeFld="),
	pieDataFld=args.str("pieDataFld="),
	pieTipsFld=args.str("pieTipsFld="),
	nodeTipsFld=args.str("nodeTipsFld="),
	picFld=args.str("picFld="),
	nodeColorFld=args.str("nodeColorFld="),
	edgeWidthFld=args.str("edgeWidthFld="),
	edgeColorFld=args.str("edgeColorFld="),
	undirect=args.bool("-undirect"),
	offline= args.bool("-offline")
)

nu.mmsg.endLog(footer)


