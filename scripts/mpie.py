#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.view.mpie as nvpie
import nysol.util as nu


helpMSG="""
概要) CSVデータから円グラフ(HTML)を作成する
      1次元グリッド、２次元グリッドのグラフ表示が可能
      マウススクロールで拡大、縮小、マウスドラッグで画像の移動が可能

書式1) #{$cmd} [i=] [o=] [title=] [pr=] [k=] [cc=] f= share= [--help]
                i=        : 入力データファイル名(CSV形式)
                o=        : 出力ファイル名(HTMLファイル)
                title=    : グラフのタイトル文字列を指定する
                pr=       : 円グラフの半径を指定する(default:160)
                k=        : x軸,y軸に展開する属性項目名
　　　　　　　　　   　　 　k=なしの場合は円グラフを1つ作成する
　　　　　　　　　　    　　項目を1つ指定した場合は1次元の円グラフ行列を、
　　　　　　　　　　　    　項目を2つ指定した場合は2次元の円グラフ行列を作成する
                            (y軸項目,x軸項目の順に指定)
                cc=       : 1行に表示する円グラフの最大数を指定する(default:5)
                            1次元グラフのみで指定可能(k=1つ指定の場合)
                f=        : 構成要素項目名を指定する(必須)
                            データにnullが含まれる場合は無視する
                v=    : 構成比項目(円グラフの円弧の長さを決定する項目)を指定する(必須)
                            データにnullが含まれる場合は0として扱う
                            先頭の0は無視する
                           数字以外の場合はエラーとなる
                --help    : ヘルプの表示

注意1)コマンドには、f=パラメータやk=パラメータで指定した項目を自動的に並べ替える機能はない
グラフに表示したい順に、あらかじめ並べ替えておく必要がある。

例1) 円グラフを1つ描画する
dat1.csvファイルのAgeを構成要素項目に、Populationを構成比項目として円グラフを1つ描画する

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

例2) 1次元の円グラフ行列を描画する
dat2.csvファイルのAgeを構成要素項目に、Populationを構成比項目として円グラフを描画する
k=パラメータにPref項目を指定しているので、
Pref項目の値をx軸(横方向)に展開した1次元の円グラフ行列が描画される
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

例3) x軸上に表示する円グラフの最大数を1とする

$ #{$cmd} i=dat2.csv k=Pref v=Population f=Age o=result3.html cc=1

例4) 2次元の円グラフ行列を描画する
dat3.csvファイルのテーマパーク名を構成要素項目に、
Numberを構成比項目として円グラフを描画する
k=パラメータにGenderとAge項目を指定して、Gender項目の値をx軸(横方向)に、
Age項目の値をy軸(縦方向)に展開した2次元の円グラフ行列を描画する

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

		"""

if "-help" in sys.argv or "--help" in sys.argv:
	print(helpMSG)
	exit()

args=margs.Margs(sys.argv,"i=,o=,title=,cc=,pr=,k=,f=,v=,--help","i=,f=,v=")

footer = os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1:])

iFile = args.file("i=","r")   # inputファイル名を取得(readable)
oFile = args.file("o=","w")   # outputファイル名を取得(writable)
title         = args.str("title=")    # タイトル取得
pieRadius     = args.int("pr=")       # pieの半径

xMax  = args.int("cc=")     # x軸に並べる棒グラフの数取得
legendKey    = args.str("f=")    # 棒グラフの構成要素項目
pieValue     = args.str("v=")     # 棒グラフの値のキー
keyValue     = args.str("k=")     # key項目値取得

if args.keyValue["v="] :
	args.field("v=", iFile)  # 項目値をヘッダからチェック
	
if args.keyValue["f="] : # 凡例項目をヘッダからチェック
	args.field("f=", iFile)

#if args.keyValue["k="] :
#	args.field("k=", iFile)      # key項目値取得

nvpie.mpie(
	iFile,oFile,pieValue,legendKey,
	k=keyValue,title=title,pr=pieRadius,
	cc=xMax,footer=footer
)

nu.mmsg.endLog(footer)


