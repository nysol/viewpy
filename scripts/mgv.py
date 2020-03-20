#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.mgv as nvgv

import nysol.util as nu






helpMSG="""
概要) CSVによるグラフ構造データをDOTフォーマットで出力する

書式1) #{$cmd} [type=flat|nest] [k=] [ni=] [nf=] [nv=] [nc=] [col=] [nl=] [nw=]
                  [-clusterLabel] [-noiso] ei= ef= [ev=] [er=] [el=] [-d] [o=]

  type= : グラフのタイプ(省略時はflat)
          flat: key項目をクラスタとした木構造グラフ
          nest: 木構造であることを前提にした入れ子構造グラフ(データが木構造でない場合の描画は不定)
  k=  : 入れ子グラフのクラスタ項目名(ni=を指定した場合は同じ項目名でなければならない)
        複数項目指定不可
        k=を省略すればtype=に関わらずクラスタを伴わない普通のグラフ描画となる。

  ni= : 節点集合ファイル名
  nf= : 節点ID項目名
  nv= : 節点の大きさ項目名(この値に応じて節点の楕円の大きさが変化する,1項目のみ指定可)。
  nc= : 節点カラー項目名(この値に応じて枠線カラーが変化する,1項目のみ指定可)。
        カラーは、RGBを16進数2桁づつ6桁で表現する。ex) FF00FF:紫
        さらに最後に2桁追加すればそれは透過率となる。
  nl= : ノードラベルの項目(複数指定したら"_"で区切って結合される)
        省略すればnf=でしてした項目をラベルとする。
  nw= : 節点の枠線の幅を指定する(デフォルトは1)
  -clusterLabel : k=を指定して入れ子グラフを作成する場合、クラスタのラベルも表示する
  -noiso : 孤立節点(隣接節点のない節点で、本コマンドではni=に出てきてei=に出てこない節点のこと)は出力しない

  ei= : 枝集合ファイル名
  ef= : 開始節点ID項目名,終了節点ID項目名
  ev= : 枝の幅項目名
  ec= : 枝の色を表す項目(色の値はnc=と同じ)
  ed= : 枝の矢印を表す項目(-dの指定、未指定に関わらず優先される)
        値としては、F,B,W,N,nullの5つの値のいずれかでなければならない。
        ef=e1,e2とした場合、それぞれで描画される矢印は以下の通り。
        F: e1->e2, B: e1<-e2, W: e1<->e2, N:e1-e2(矢印なし),null:デフォルト
        デフォルトは、-dが指定されていればF、-dの指定がなければNとなる。
  el= : エッジラベルの項目(複数指定したら"_"で区切って結合される)
        省略すれば、エッジラベルは表示されない。

  -d  : 有向グラフと見なす。"edge [dir=none]"を記述する。
  o=  : 出力ファイル名

  -h,--help : ヘルプの表示

基本例)
$ cat edge.csv
e1,e2,v
a,b,11
a,c,20
b,d,11
d,e,8
c,e,9

$ #{$cmd} ei=edge.csv ef=e1,e2 ev=v el=v er=20 o=result.dot
$ cat result.dot
digraph G {
  edge [dir=none]
  n_2 [label="a" style="setlinewidth(1)" ]
  n_3 [label="b" style="setlinewidth(1)" ]
  n_4 [label="c" style="setlinewidth(1)" ]
  n_5 [label="d" style="setlinewidth(1)" ]
  n_6 [label="e" style="setlinewidth(1)" ]
  n_2 -> n_3 [label="11" style="setlinewidth(5.75)" ]
  n_2 -> n_4 [label="20" style="setlinewidth(20)" ]
  n_3 -> n_5 [label="11" style="setlinewidth(5.75)" ]
  n_4 -> n_6 [label="9" style="setlinewidth(2.583333333)" ]
  n_5 -> n_6 [label="8" style="setlinewidth(1)" ]
}

ネストグラフの例)
$ cat edge4.csv
cluster,node1,node2,support
#1_1,a,b,0.1
#1_2,d,e,0.1
#2_1,#1_1,c,0.2
#3_1,#1_2,#2_1,0.3
#3_1,#2_1,f,0.4

$ #{$cmd} mgv.rb type=flat k=cluster ei=edge4.csv ef=node1,node2 o=result.dot
# fdpはgraphVizのコマンド, nested graphはdotコマンドでは描画できない
$ fdp -Tpdf result.dot >result.pdf
$ open result.pdf
$ cat result.dot
digraph G {
  edge [dir=none]
  subgraph cluster_1 {
n_5 [label="a" style="setlinewidth(1)" ]
n_6 [label="b" style="setlinewidth(1)" ]
n_5 -> n_6 []
  }
  subgraph cluster_2 {
n_8 [label="d" style="setlinewidth(1)" ]
n_9 [label="e" style="setlinewidth(1)" ]
n_8 -> n_9 []
  }
  subgraph cluster_3 {
cluster_1 []
n_7 [label="c" style="setlinewidth(1)" ]
cluster_1 -> n_7 []
  }
  subgraph cluster_4 {
cluster_2 []
cluster_3 []
n_10 [label="f" style="setlinewidth(1)" ]
cluster_2 -> cluster_3 []
cluster_3 -> n_10 []
  }
}
		"""

if "-help" in sys.argv or "--help" in sys.argv:
	print(helpMSG)
	exit()


keylist = [ 
"type,k,ni,nf,nv,nc,ei,ef,ev,ec,o,nl,el,ed,nw",
"d,clusterLabel,noiso,normalize,normalizeEdge,normalizeNode"
]

convkey = {"type":"tp"}


kwd = nu.margv2dict(sys.argv,keylist,"ei,ef",convkey)
footer = os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1:])



nvgv.mgv(**kwd)

nu.mmsg.endLog(footer)


