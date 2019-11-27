#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.mdtree as nvdtree
import nysol.util as nu


helpMSG="""
------------------------
mdtree.rb version #{$version}
------------------------
概要) PMMLで記述された決定木モデルのHTMLによる視覚化
書式) mdtree.rb i= o= [alpha=] [--help]

  i=     : PMMLファイル名
  o=     : 出力ファイル名(HTMLファイル)
  alpha= : 枝刈り度を指定する (0 以上の実数で、大きくすると枝が多く刈られる)。
         : 指定しなかった場合、mbonsai で交差検証を指定しなければ、
         : 0.01 が指定されたことになり、交差検証を指定していれば、誤分類率最小のモデルが描画される。
         : このパラメータは mbonsai で構築した決定木のみ有効。
  -bar   : ノードを棒グラフ表示にする
  --help : ヘルプの表示

備考)
本コマンドのチャート描画にはD3(http://d3js.org/)を用いている。

利用例)
$ mbonsai c=入院歴 n=来店距離 p=購入パターン d=性別 i=dat1.csv O=outdat
$ mdtree.rb i=outdat/model.pmml o=model.html
$ mdtree.rb alpha=0.1 i=outdat/model.pmml o=model2.html

Copyright(c) NYSOL 2012- All Rights Reserved.
		"""

if "-help" in sys.argv or "--help" in sys.argv:
	print(helpMSG)
	exit()

keylist = [ 
"i,o,alpha",
"bar"
]


kwd = nu.margv2dict(sys.argv,keylist,"i,o")

footer = os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1:])

nvdtree.mdtree(**kwd)

nu.mmsg.endLog(footer)


