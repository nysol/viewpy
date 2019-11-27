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
概要) 値に応じた色を自動的に割り付ける

書式1) #{$cmd} f= col= [order=alpha|descend|ascend] [transmit=] o=

  f= : カラー項目名(この値に応じてカラーの値が決まる,1項目のみ指定可)。
  col=category|２色HEXコード(ex. FF0000,0000FF)
        categoryを指定した場合は、f=の値をカテゴリとして扱い、
          アルファベット順にRGBの値を以下の順番で設定していく。
          FF,80,C0,40,E0,60,A0,20,F0,70,B0,30,D0,50,90,10
          また上記各値の中でRGBの組合わせをR,G,B,RG,GB,RBの順に設定する。
          よって、16 x 6=96通りの色が設定される。
          カテゴリの数が96を超えた場合、超えた分は000000(黒)として出力される。
          FF0000,00FF00,0000FF,FFFF00,00FFFF,FF00FF,800000,008000,000080,...
        2色のHEXコードを指定した場合、f=の値を数値として扱い、
          指定した2色間のグラデーションを数値の大きさに応じて割り当てる。
          FF0000,0000FFの2色を指定した場合、f=項目の最小値がFF0000で、最大値が0000FFとなる。
          f=項目の値をv,最小値をmin,最大をmaxとすると、
          vに対して割り当てられるR(赤)要素のカラー値は以下の通り計算される。
            floor(r0+(r1-r0)*dist)  ただし、dist:(v-min)/(max-min)
            r0: color=で指定した色範囲開始のR要素
            r1: color=で指定した色範囲終了のR要素
            ex) color=FF0000,0000FFと指定していれば、r0=FF,r1=00
          与えられた値が全て同じ場合は計算不能のため、null値を出力する。
  order=: col=categoryの場合、色の割り付け順序を指定する(デフォルトはalpha)
     alpha: f=で指定した値をalphabet順
     descend: f=で指定した値の件数が多い順
     ascend:  f=で指定した値の件数が少ない順
  transmit= : 透過率を指定する。透過率は00からFFまでの値で、00で完全透明、FFで透明度0となる。
              色コードの後ろに追加される。
  o=  : 出力ファイル名

  -h,--help : ヘルプの表示

カテゴリデータをカラー化する例)
$ cat color.csv
num,class
01,B,10
02,A,15
03,C,11
04,D,29
05,B,32
06,A,
07,C,9
08,D,3
09,B,11
10,E,22
11,,21
12,C,35
$ mautocolor.rb f=class color=category a=color i=color.csv o=output1.csv↩
$ cat output1.csv
num,class1,value,color
01,B,10,00FF00
02,A,15,FF0000
03,C,11,0000FF
04,D,29,FFFF00
05,B,32,00FF00
06,A,,FF0000
07,C,9,0000FF
08,D,3,FFFF00
09,B,11,00FF00
10,E,22,00FFFF
11,,21,
12,C,35,0000FF

数値データをカラー化する例)
$ mautocolor.rb f=value color=FF0000,0000FF a=color i=color.csv o=output2.csv↩
$ cat output2.csv
num,class,value,color
01,B,10,c70037
02,A,15,9f005f
03,C,11,bf003f
04,D,29,2f00cf
05,B,32,1700e7
06,A,,
07,C,9,cf002f
08,D,3,ff0000
09,B,11,bf003f
10,E,22,670097
11,,21,6f008f
12,C,35,0000ff
		"""

#############
# entry point
if "-help" in sys.argv or "--help" in sys.argv:
	print(helpMSG)
	exit()


keylist = [ 
"f,color,order,transmit,a,i,o",
""
]
convkey = {"i":"iFile","o":"oFile","f":"fld","a":"aFld"}

kwd = nu.margv2dict(sys.argv,keylist,"iFile,fld,aFld",convkey)
footer = os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1:])

# ===================================================================
# パラメータ処理
nvgv.mautocolor(**kwd)

# 終了メッセージ
nu.mmsg.endLog(footer)

