#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import nysol.util.margs as margs
import nysol.view.mgv as nvgv
import nysol.util as nu





helpMSG="""
------------------------
#{$cmd} version #{$version}
------------------------
概要) 入れ子グラフ(nested graph)をtree構造グラフに変換する

書式1) #{$cmd} k= [ni=] [nf=] ei= ef= [no=] [eo=]

  k=  : 入れ子グラフのクラスタ項目名(ni=を指定した場合は同じ項目名でなければならない)
        複数項目指定不可

  ni= : 頂点集合ファイル名
  nf= : 頂点ID項目名

  ei= : 枝集合ファイル名
  ef= : 開始頂点ID項目名,終了頂点ID項目名
  ev= : 枝重み

  no=  : 出力節点ファイル名
  eo=  : 出力枝ファイル名

  -h,--help : ヘルプの表示

基本例)
		"""




#############
# entry point
if "-help" in sys.argv or "--help" in sys.argv:
	print(helpMSG)
	exit()


keylist = [ 
"k,ni,nf,ei,ef,ev,no,eo",
""
]

# ===================================================================
# パラメータ処理
kwd = nu.margv2dict(sys.argv,keylist,"ei,ef")
footer = os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1:])
nvgv.mnest2tree(**kwd)


# 終了メッセージ
nu.mmsg.endLog(footer)


