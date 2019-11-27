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

keylist=[
	["ei","ni","ef","nf","o",
	"nodeSizeFld","pieDataFld","pieTipsFld",
	"nodeTipsFld","picFld","nodeColorFld",
	"edgeWidthFld","edgeColorFld"],
	["undirect","offline"]
]
nparalist=[
	"ei","ni","ef","nf","o"
]

kwd = nu.margv2dict(sys.argv,keylist,nparalist)
footer = os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1:])

nnpie.mnetpie(**kwd)


nu.mmsg.endLog(footer)


