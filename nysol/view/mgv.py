#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import nysol.util.margs as margs
import nysol.mcmd as nm
import nysol.util as nu
import nysol.util._utillib as _nu
import nysol.view.viewjs as vjs
import nysol.util.mtemp as mtemp
from nysol.util.mmkdir import mkDir
from nysol.util.mrecount import mrecount

class Color(object):

	def __init__(self,nc,ni,col,order):

		self.nc  = nc
		self.ni  = ni
		self.col = col
		self.range = 0
		self.min   = 0
		self.max   = 0
		self.order = order

		if self.nc and self.ni :

			if self.col == "category" :
				
				self.type = "category"
				# preparing a color pallet
				pallet=[]
				val=["FF","80","C0","40","E0","60","A0","20","F0","70","B0","30","D0","50","90","10"]
				for v in val:
					pallet.append("%s0000"%(v))
					pallet.append("00%s00"%(v))
					pallet.append("0000%s"%(v))
					pallet.append("%s%s00"%(v,v))
					pallet.append("00%s%s"%(v,v))
					pallet.append("%s00%s"%(v,v))


				# read color field data and make a mapping table(data to pallet)
				f = None
				f <<= nm.mcut(f="%s:ckey"%(self.nc),i=self.ni)
				f <<= nm.mdelnull(f="ckey")
				f <<= nm.mcount(k="ckey", a="freq")

				if self.order=="descend" :
					f <<= nm.mbest(s="freq%nr,ckey",fr=0,size=96) #,o=#{xxcTable} 
				elif self.order=="ascend" :
					f <<= nm.mbest(s="freq%n,ckey",fr=0,size=96) # o=#{xxcTable}"
				else:
					f <<= nm.mbest(s="ckey",fr=0,size=96) #o=#{xxcTable}"
				
				self.cTable={}
				i = 0 
				for flds in f.getline(otype="dict"):
					cK=flds["ckey"]
					self.cTable[cK]=pallet[i]
					i+=1

			else:
				self.type="numeric"
				ary=col.split(",")
				if len(ary)!=2 or len(ary[0]) !=6 or len(ary[1])!=6:
					raise ValueError("col= takes two 6-digites HEX codes like FF0000,00FF00")

				self.r0=int(ary[0][0:2],16)
				self.g0=int(ary[0][2:4],16)
				self.b0=int(ary[0][4:6],16)
				self.r1=int(ary[1][0:2],16)
				self.g1=int(ary[1][2:4],16)
				self.b1=int(ary[1][4:6],16)

				f = None
				f <<= nm.mcut(f="%s:ckey"%(self.nc),i=self.ni)
				f <<= nm.mdelnull(f="ckey")
				f <<= nm.msummary(f="ckey",c="min,max")
				xxcTable = f.run()
				if len(xxcTable) > 0 :
					if len(xxcTable[0]) >= 2 :
						if xxcTable[0][1] != "":
							self.min = float(xxcTable[0][1])
						if xxcTable[0][2] != "":
							self.max = float(xxcTable[0][2])
				
						if xxcTable[0][1] != "" and xxcTable[0][2] != "" :
							self.range = self.max - self.min
						

	def getRGB(self, val):

		if val==None or val=="" :
			return ""
			 

		if self.type=="category":

			if val in self.cTable:
				rgb=self.cTable[val]
			else:
				rgb="000000"

		else:
			if self.range == 0 : 
				rgb=""
			else:
				distance=(float(val)-self.min)/self.range
				r = int((self.r0+(self.r1-self.r0)*distance))
				g = int((self.g0+(self.g1-self.g0)*distance))
				b = int((self.b0+(self.b1-self.b0)*distance))
				rgb=("%02x%02x%02x",r,g,b)

		return rgb


def mautocolor(iFile,oFile,fld,aFld,color="category",order="alpha",transmit=None):


	color=Color(fld,iFile,color,order)
	head = nu.mheader(i=iFile)
	head.append(aFld)
	with _nu.mcsvout(o=oFile,f=head) as oCSV :

		for flds in nm.readcsv(iFile).getline(otype="dict"):
			colorStr=color.getRGB(flds[fld])
			if colorStr != "" and transmit :
				flds[aFld] = "%s%s"%(colorStr,transmit)
			else:
				flds[aFld]= colorStr
			dt = []
			for hname in head:
				dt.append(flds[hname])
			oCSV.write(dt)
	
def mnest2tree(ei,ef,k,ni=None,nf=None,ev=None,no=None,eo=None):
	# paracheck追加
	efs = ef.split(",")
	ef1=efs[0]
	ef2=efs[1]

	f=nm.mcut(f="%s:#orgKey,%s:#orgEf1,%s:#orgEf2"%(k,ef1,ef2),i=ei) 

	temp =  mtemp.Mtemp()
	of = temp.file()

	with _nu.mcsvout(o=of,f="#orgKey,#orgEf1,#orgEf2,#ef1,#ef2") as oCSV :
		for flds in f:
			orgKey  =flds[0]
			orgEf1  =flds[1]
			orgEf2  =flds[2]
			oCSV.write([orgKey,orgEf1,orgEf2,orgKey,orgEf1])
			oCSV.write([orgKey,orgEf1,orgEf2,orgKey,orgEf2])
			
	f=None
	f <<= nm.mjoin(k="#orgKey,#orgEf1,#orgEf2",K=[k,ef1,ef2],m=ei,i=of) # 全項目join
	if ev :
		f <<= nm.mavg(k="#ef1,#ef2",f=ev)
	else:
		f <<= nm.muniq(k="#ef1,#ef2")
		
	f <<= nm.mcut(r=True,f="#orgKey,#orgEf1,#orgEf2" )
	f <<= nm.mfldname(f="#ef1:%s,#ef2:%s"%(ef1,ef2),o=eo)
	f.run()	
	
	if ni :
		head = nu.mheader(i=ni)
		fldnames = [ s for s in head if s != nf ]
		commas=','*(len(fldnames)-1)
		
		f0=None
		f0 <<= nm.mcut(f="%s:%s"%(ef1,nf),i=eo) 
		f0 <<= nm.muniq(k=nf)
		f0 <<= nm.mcommon(k=nf,m=ni,r=True)
		f0 <<= nm.msetstr(v=commas,a=fldnames)
		
		f =   nm.mcut(f=k,r=True,i=[ni,f0])
		f <<= nm.msetstr(v="",a=k,o=no)
		f.run()

#########################################
# dot用のedgeデータをcluster別に作成する　(evかevvか)
def __dotEdge(iFile,oPath):

	'''
	# key,nam1,nam2%0,keyNum,num1,num2,ev,evv
	# #2_1,#1_1,#1_2,4,1,2,0.2727272727,20
	# #1_1,a,b,1,5,6,0.1818181818,0
	'''

	block=""
	for flds,top,bot in nm.readcsv(iFile).getline(k="keyNum",otype="dict"):

		num1=flds["num1"]
		num2=flds["num2"]
		el=flds["el"]
		ev=flds["ev"]
		ec=flds["ec"]
		ed=flds["ed"]
		leaf1=flds["leaf1"]
		leaf2=flds["leaf2"]

		if leaf1 == None or leaf1 =="" :
			prefix1="cluster"
		else:
			prefix1="n"

		if leaf2 == None or leaf2 =="" :
			prefix2="cluster"
		else:
			prefix2="n"

		e1Str = "%s_%s"%(prefix1,num1)
		e2Str = "%s_%s"%(prefix2,num2)

		attrStr=""
		if el :
			attrStr += 'label="%s" '%(el)
		if ev :
			attrStr += 'style="setlinewidth(%s)" '%(ev)
		if ec :
			attrStr += 'color="#%s" '%(ec)

		if ed :
			if ed=="F":
				attrStr += "dir=forward "
			elif ed=="B" :
				attrStr += "dir=back "
			elif ed=="W" :
				attrStr += "dir=both "
			elif ed=="N" :
				attrStr += "dir=none "

		block += "%s -> %s [%s]\n"%(e1Str,e2Str,attrStr)
		if bot:
			with open("%s/c_%s"%(oPath,flds["keyNum"]),"w") as fpw:
				fpw.write(block)
			block=""
			
#########################################
# dot用のnodeデータをcluster別に作成する(nvvかnvかの違い)
def __dotNode(iFile,nw,type,clusterLabel,oPath):

	'''
	# system "cat #{iFile}"
	# key,nam,keyNum%0,num,nl,nv,nvv,nc,leaf,nvKey,ncKey
	# ##NULL##,j,0,15,j_A,0.09090909091,1,FF0000,1,,
	# ##NULL##,i,0,14,i_A,0.09090909091,1,FF0000,1,,
	# #1_1,a,2,6,a_A,0.3636363636,1.857142857,FF0000,1,0.7272727273,
	# #1_1,b,2,7,b_B,0.3636363636,1.857142857,00FF00,1,0.7272727273,
	# #1_1,d,2,9,d_B,0.3636363636,1.857142857,00FF00,1,0.7272727273,
	# #1_1,e,2,10,e_C,0.4545454545,2.142857143,0000FF,1,0.7272727273,
	# #1_2,c,3,8,c_A,0.2727272727,1.571428571,FF0000,1,0.2727272727,
	# #1_2,f,3,11,f_A,0.1818181818,1.285714286,FF0000,1,0.2727272727,
	# #1_3,g,4,12,g_B,0.1818181818,1.285714286,00FF00,1,,
	# #1_3,h,4,13,h_C,0.1818181818,1.285714286,0000FF,1,,
	# #2_1,#1_2,5,3,#1_2_,0.2727272727,1.571428571,,,,
	# #2_1,#1_1,5,2,#1_1_,0.7272727273,3,,,,
	'''

	block=""
	for flds,top,bot in nm.readcsv(iFile).getline(k="keyNum",otype="dict"):
		nam=flds["nam"]
		nl =flds["nl"]
		nv =flds["nv"]
		nc =flds["nc"]
		leaf=flds["leaf"]

		if leaf == None or leaf == ""   :
			prefix="cluster"
		else:
			prefix="n"

		nStr ="%s_%s"%(prefix,flds["num"])
		attrStr=""

		if prefix != "cluster" :
			# node label
			# labelがleafでなければ、-clusterLabelが指定されていない限りlabelを表示しない
			if leaf or clusterLabel :
				attrStr += 'label="%s" '%(nl)
			else:
				attrStr += 'label="" '

			# node shape
			if nv :
				nRatioNorm = float(nv)
				attrStr += "height=%f width=%f "%(0.5*nRatioNorm,0.75*nRatioNorm)

			# node color
			if nc:
				attrStr += 'color="#%s" '%(nc)

			# node linewidth
			if nw:
				attrStr += 'style="setlinewidth(%s)" '%(nw)

		block += "%s [%s]\n"%(nStr,attrStr)

		if bot:
			keyNum = flds["keyNum"]
			key    = flds["key"]
			nlKey  = flds["nlKey"]
			nvKey  = flds["nvKey"]
			ncKey  = flds["ncKey"]

			with open("%s/c_%s"%(oPath,keyNum),"w") as fpw:
				fpw.write(block)

			# クラスタのラベルや色も出力しておく
			attrStr=""
			attrStr += 'label="%s"\n'%(nlKey)

			# node color
			if ncKey:
				attrStr += 'color="#%s"\n'%(ncKey)

			if nw and ncKey:
				if ncKey: ## ?
					attrStr += 'style="setlinewidth(%s)"\n'%(nw)

			with open("%s/L_%s"%(oPath,keyNum),"w") as fpw:
				fpw.write(attrStr)
				
			block=""

#####################
# edgeフィアルの作成
'''
# 1) key,node名に対応するnodeIDをjoinする
# 2) ev項目を基準化
# 3) evがなければ全データ1をセット
'''
def __mkEdge(key,ef1,ef2,el,ec,ed,ev,ei,mapFile,oFile):

	# mcal cat用のlabel項目の作成
	label=[]
	if el:
		for nml in el :
			label.append("$s{"+nml+"}")	

	evcdStr=[]
	if ev:
		evcdStr.append(ev+":ev")
	if ec:
		evcdStr.append(ec+":ec")
	if ed:
		evcdStr.append(ed+":ed")

	f = None
	if el:
		f <<= nm.mcal(c='cat(\"_\",%s)'%(','.join(label)),a="##label",i=ei)
	else:
		f <<= nm.msetstr(v="",a="##label",i=ei)

	if len(evcdStr) == 0 :
		f <<= nm.mcut(f="%s:key,%s:nam1,%s:nam2,##label:el"%(key,ef1,ef2))
	else: 
		f <<= nm.mcut(f="%s:key,%s:nam1,%s:nam2,##label:el,%s"%(key,ef1,ef2,','.join(evcdStr)))


	if not ev:
		f <<= nm.msetstr(v="",a="ev")

	if not ed:
		f <<= nm.msetstr(v="",a="ed")

	if not ec:
		f <<= nm.msetstr(v="",a="ec")

	f <<= nm.mnullto(f="key",v="##NULL##")
	f <<= nm.mjoin(k="key",K="nam",m=mapFile,f="num:keyNum")
	f <<= nm.mjoin(k="nam1",K="nam",m=mapFile,f="num:num1,leaf:leaf1")
	f <<= nm.mjoin(k="nam2",K="nam",m=mapFile,f="num:num2,leaf:leaf2")
	f <<= nm.mcut(f="key,nam1,nam2,keyNum,num1,num2,el,ev,ed,ec,leaf1,leaf2",o=oFile)
	f.run()


####################
# nodeファイルの作成
'''
# 1) key,node名すべての値に一対一対応するnodeIDを作成=>xxmap
# niがなければeiから作成
# 1) key,node名に対応するnodeIDをjoinする
# 2) nvがなければ全データ1をセット
# 3) ncがなければ全データnullをセット
#
# オリジナルのkey,node名に一意のnodeID(num)をつけて、nodeマスターを作成する
'''
def __mkNode(key,nf,nl,nv,nc,ni,ef1,ef2,ei,noiso,mapFile,oFile):

	xbyE = None
	xbyN =None
	# edgeファイルからnode情報を生成
	# noiso(孤立node排除)の場合は、edgeにあってnodeにないidを省く必要があるので計算する。
	if ni==None or ( ni!=None and noiso ) :
		inp=[
			nm.mcut(f="%s:key,%s:nam,%s:nl"%(key,ef1,ef1),i=ei),
			nm.mcut(f="%s:key,%s:nam,%s:nl"%(key,ef2,ef2),i=ei)
		]
		xbyE <<= nm.mnullto(i=inp,f="key",v="##NULL##")
		xbyE <<= nm.muniq(k="key,nam")
		xbyE <<= nm.mjoin(k="key",K="nam",m=mapFile,f="num:keyNum")
		xbyE <<= nm.mjoin(k="nam",K="nam",m=mapFile,f="num,leaf")
		xbyE <<= nm.msetstr(v=",,,,",a="nv,nc,nlKey,nvKey,ncKey")
		xbyE <<= nm.mcut(f="key,nam,keyNum,num,nl,nv,nc,leaf,nvKey,ncKey,nlKey")

	# nodeファイルから作成
	if ni:
		# mcal cat用のlabel項目の作成
		label=[]
		#label項目
		if nl:
			for nml in nl.split(',') :
				label.append(nml)	
		else:
				label.append("$s{%s}"%(nf))

		nvcStr=[]
		if nv:
			nvcStr.append('%s:nv'%(nv))
		if nc:
			nvcStr.append('%s:nc'%(nc))

		"""
		# map
		# nam,leaf,num
		# ##NULL##,,0
		# #1_1,,2
		# #1_2,,3
		# #1_3,,4
		# #2_1,,5
		# a,1,6
		# b,1,7
		# c,1,8
		"""

		f = None
		f <<= nm.mcal(c='cat("_",%s)'%(','.join(label)),a="##label" ,i=ni )
		if len(nvcStr)==0 :
			f <<= nm.mcut(f='%s:key,%s:nam,##label:nl'%(key,nf))
		else:
			f <<= nm.mcut(f='%s:key,%s:nam,##label:nl,%s'%(key,nf,','.join(nvcStr)))
		f <<= nm.mnullto(f="key",v="##NULL##")
		if not nv :
			f <<= nm.msetstr(v="",a="nv")
		if not nc :
			f <<= nm.msetstr(v="",a="nc")

		f <<= nm.mjoin(k="key",K="nam",m=mapFile,f="num:keyNum")
		f <<= nm.mjoin(k="nam",K="nam",m=mapFile,f="num,leaf")
		f <<= nm.mcut(f="key,nam,keyNum,num,nl,nv,nc,leaf") #o=#{xxa}"

		xbyN <<= nm.mjoin(k="keyNum",K="num",m=f,f="nl:nlk,nv:nvKey,nc:ncKey",n=True,i=f)
		xbyN <<= nm.mcal(c='if(isnull($s{nlk}),$s{key},$s{nlk})',a='nlKey')
		xbyN <<= nm.mcut(f="nlk",r=True)

	if ni!=None and noiso :
		nm.mcommon(k="key,nam",m=xbyE,i=xbyN,o=oFile).run()
	elif ni!=None:
		xbyN.writecsv(o=oFile).run()
	else:
		xbyE.writecsv(o=oFile).run()




####################
# mapファイルの作成
'''
# 1) key,node名の値に一対一対応するnodeIDを作成(niがなければeiから作成)
'''
def __mkMap(key,nf,ni,ef1,ef2,ei,oFile):

	# leaf nodeの構築
	infL = [
		nm.mcommon(k=ef1 , K=key , m=ei, r=True, i=ei).mcut(f="%s:nam"%(ef1)),
		nm.mcommon(k=ef2 , K=key , m=ei, r=True, i=ei).mcut(f="%s:nam"%(ef2))
	]
	if ni :
		infL.append(nm.mcommon(k=nf , K=key , m=ei, r=True, i=ni).mcut(f="%s:nam"%(nf)))

	xleaf =   nm.muniq(i=infL,k="nam")
	xleaf <<= nm.msetstr(v=1,a="leaf")

	if ni :
		inp = [
			nm.mcut(f="%s:nam"%(nf),i=ni),
			nm.mcut(f="%s:nam"%(key),i=ni)
		]

	else:
		inp = [
			nm.mcut(f="%s:nam"%(ef1),i=ei),
			nm.mcut(f="%s:nam"%(ef2),i=ei),
			nm.mcut(f="%s:nam"%(key),i=ei)
		]

	f = None
	f <<= nm.muniq(k="nam",i=inp)
	f <<= nm.mjoin(k="nam",m=xleaf,f="leaf",n=True)
	# nullは最初に来るはずなので、mcalでなくmnumberでもnullを0に採番できるはずだが念のために
	f <<= nm.mcal(c='if(isnull($s{nam}),0,line()+1)',a="num")
	f <<= nm.mnullto(f="nam",v="##NULL##",o=oFile)
	f.run()

# edgeデータからnested graphのtree構造を作る
# clusterのみの構造を作る
def __mkTree(iFile,oFile):

	temp =  mtemp.Mtemp()
	xxbase0  = temp.file()
	xxbase1  = temp.file()
	xxiFile2 = temp.file()
	xxcheck  = temp.file()

	"""
	# #{iFile}
	# key,nam%0,keyNum,num,nv,nc
	# #2_1,#1_1,4,1,6,1
	# #2_1,#1_2,4,2,0.9999999996,1
	"""

	# keyNumとnum項目のuniqリストを作り、お互いの包含関係でrootノードとleafノードを識別する。
	f0 = nm.mcut(f="keyNum,num",i=iFile)  #{xxiFile1}
	fk = f0.mcut(f="keyNum").muniq(k="keyNum") #{xxkey}
	fn = f0.mcut(f="num").muniq(k="num") #{xxnum}

	# root nodesの選択
	fr = nm.mcommon(k="keyNum",K="num",m=fn,i=fk,r=True).mcut(f="keyNum:node0",o=xxbase0) #{xxbase[0]}

	# leaf nodesの選択
	fl = nm.mcommon(k="num",K="keyNum",m=fk,i=fn,r=True).mcut(f="num") #{xxleaf}

	# leaf nodeの構造を知る必要はないので入力ファイルのnodeからleafを除外
	f = nm.mcommon(k="num", m=fl,r=True,i=f0,o=xxiFile2)
	
	nm.runs([f,fr])

	def _xnjoin(inf,outf,mfile,check ,no):
		f  = nm.mnjoin(k="node%d"%(no),K="keyNum",m=mfile,n=True,f="num:node%d"%(no+1),i=inf,o=outf)
		fc = nm.mdelnull(i=f,f="node%d"%(no+1),o=check)
		return fc

	i=0
	depth=None
	inf   = xxbase0
	outf  = xxbase1
	
	'''
	# root nodesファイルから親子関係noodeを次々にjoinしていく
	# xxbase0 : root nodes
	# node0%0
	# 3
	# 4
	# xxbase1
	# node0%0,node1
	# 3,
	# 4,1
	# 4,2
	# xxbase2
	# node0,node1%0,node2
	# 3,,
	# 4,1,
	# 4,2,
	# join項目(node2)の非null項目が0件で終了
	'''

	while True:

		_xnjoin(inf,outf,xxiFile2,xxcheck,i).run()
		size=mrecount(i=xxcheck)

		if size==0:
			nm.msortf(f="*",i=outf,o=oFile).run()
			depth=i+1
			break

		# swap f_name
		xxtmp = outf
		outf  = inf
		inf   = xxtmp
		i += 1
	
	return depth


def __mkFlat(iFile,oFile):
	f = None
	f <<= nm.mcut(f="keyNum:node0", i=iFile)
	f <<= nm.muniq(k="node0",o=oFile)
	f.run()
	return 1


def __keyBreakDepth(newFlds,oldFlds):
	if oldFlds ==None:
		return 0 

	for i in range(len(newFlds)):
		if newFlds[i]!=oldFlds[i]:
			return i

##########################
# creating tree structure
'''
#
# digraph G {edge [dir=none]
#   subgraph n_3 {
# ##3
#   }
#   subgraph n_4 {
# ##4
#     subgraph n_1 {
# ##1
#     }
#     subgraph n_2 {
# ##2
#     }
#   }
# }
'''
def __dotTree(iFile,depth,header,footer,oFile):

	with open(oFile,"w") as fpw :
		fpw.write(header)
		fpw.write("##0\n") # 孤立node(keyがnullのnode)
		oldFlds=None
		stack=[]    # "subgraph {"に対応する終了括弧"}"のスタック
		lastDepth=0 # 前行で出力されたsubgraphの深さ

		for newFlds in nm.readcsv(iFile):

			if newFlds[0] =="0" :
				continue

			kbd=__keyBreakDepth(newFlds,oldFlds) # 前行に比べてどの位置でkeybreakがあったか

			for i in range(0,lastDepth-kbd):
				fpw.write("%s\n"%(stack.pop()))
	
			for i in range(kbd,depth):

				if newFlds[i] == "" : # nullはその深さにsubgraphなしということ
					break  

				indent='  '*(i+1) # インデント

				fpw.write("%ssubgraph cluster_%s {\n"%(indent,newFlds[i]))
				fpw.write("##%s\n"%(newFlds[i]))
				stack.append("%s}"%(indent)) # 対応する終了括弧をスタックしておく
				lastDepth=i+1 # 出力した最深位置の更新

			oldFlds=newFlds
		
		# 深さが戻った分終了括弧"}"を出力
		for i in range(lastDepth):
			fpw.write("%s\n"%(stack.pop()))

		fpw.write("%s\n"%(footer))


def __replace(treeFile,nodePath,edgePath,clusterLabel,oFile):

	import os
	with open(oFile,"w") as dot:
			
		for line in open(treeFile, "r"):
			if line[0]=="#":
				num = line.strip().replace('##',"")
				# 孤立nodeのclusterラベル(null)は出力しない
				if clusterLabel and os.path.isfile("%s/L_%s"%(nodePath,num)) and num!="0" :
					for lineL in open("%s/L_%s"%(nodePath,num), "r"):
						dot.write(lineL)

				if os.path.isfile("%s/c_%s"%(nodePath,num)) : # このifにマッチしないケースはないけど念のため
					for linec in open("%s/c_%s"%(nodePath,num), "r"):
						dot.write(linec) 

				if os.path.isfile("%s/c_%s"%(edgePath,num)) :
					for lineec in open("%s/c_%s"%(edgePath,num), "r"):
						dot.write(lineec)
			else:
				dot.write(line)


# mgv に 
#ec=追加 nr=,er=のぞく
#er=None,nr=None, <=拡大率
def mgv(
	ei     ,ef     ,ev=None,ec=None,el=None,ed=None,
	ni=None,nf=None,nv=None,nc=None,nl=None,nw=1,
	tp="flat",k=None,o=None,
	d=False,clusterLabel=False,noiso=False):

	# arg check
	# ei : str (filename)
	# ef : str | list (fldname size=2)
	# ev : str | None (fldname)
	# ec : str | None (fldname)
	# el : str | list | None (fldname no limit )
	# ed : str | None (fldname)
	# ni : str | None (filename)
	# nf : str | None (fldname)
	# nv : str | None (fldname)
	# nc : str | None (fldname)
	# nl : str | list | None  (fldname no limit )
	# tp : str (flat|nest default:flat ) 
	# k  : str | None (fldname)
	# o  : str (filename)
	# d : bool | None
	# clusterLabel : bool | None
	# noiso : bool | None


	# ei
	if not ( isinstance( ei , str )  ) :
		raise TypeError("ei= unsupport " + str(type(ei)) )

	# ef
	if isinstance( ef , str ):
		ef = ef.split(',')
	elif not isinstance( ef , list ):
		raise TypeError("ef= unsupport " + str(type(ef)) )

	if len(ef) < 2:
		raise TypeError("ef size == 2 " )
	elif len(ef) > 2: 
		sys.stderr.write('warning : ef size == 2 ')

	# k
	if not ( isinstance( k , str ) or k == None ) :
		raise TypeError("k= unsupport " + str(type(k)) )

	# ev
	if not ( isinstance( ev , str ) or ev==None ) :
		raise TypeError("ev= unsupport " + str(type(ev)) )

	# ec
	if not ( isinstance( ec , str ) or ec==None ) :
		raise TypeError("ec= unsupport " + str(type(ec)) )

	# el
	if isinstance( el , str ):
		el = el.split(',')
		if len(el) == 1 and el[0] == '' :
			el = None
	elif not ( isinstance( el , list ) or el == None ):
		raise TypeError("el= unsupport " + str(type(el)) )

	# ed
	if not ( isinstance( ed, str ) or ed==None ) :
		raise TypeError("ed= unsupport " + str(type(ed)) )

	# ni
	if not ( isinstance( ni , str ) or ni==None ) :
		raise TypeError("ni= unsupport " + str(type(ni)) )

	# nf
	if not ( isinstance( nf , str ) or nf==None ) :
		raise TypeError("nf= unsupport " + str(type(nf)) )

	# nv
	if not ( isinstance( nv , str ) or nv==None ) :
		raise TypeError("nv= unsupport " + str(type(nv)) )

	# nc
	if not ( isinstance( nc , str ) or nc==None ) :
		raise TypeError("nc= unsupport " + str(type(nc)) )

	# nl
	if isinstance( nl , str ):
		nl = nl.split(',')
		if len(nl) == 1 and nl[0] == '' :
			nl = None
	elif not ( isinstance( nl , list ) or nl == None ):
		raise TypeError("nl= unsupport " + str(type(nl)) )

	# tp
	if tp == None :
		tp = "flat"
	elif not isinstance( tp , str ):
		raise TypeError("tp= unsupport " + str(type(tp)) )

	# o
	if isinstance( o , str ):
		oFile = o
	else:
		raise TypeError("o= unsupport " + str(type(o)) )

	# d
	if d == None :
		d = False
	if not isinstance( d , bool ):
		raise TypeError("d= unsupport " + str(type(d)) )

	# clusterLabel
	if clusterLabel == None :
		clusterLabel = False
	if not isinstance( clusterLabel , bool ):
		raise TypeError("clusterLabel= unsupport " + str(type(clusterLabel)) )

	# noiso
	if noiso == None :
		noiso = False
	if not isinstance( noiso , bool ):
		raise TypeError("noiso= unsupport " + str(type(bar)) )


	temp =  mtemp.Mtemp()
	xxni  = temp.file()
	xxei  = temp.file()
	xxmap  = temp.file()
	xxnode = temp.file()
	xxedge = temp.file()
	xxdotNode = temp.file()
	xxdotEdge = temp.file()
	xxtree    = temp.file()

	mkDir(xxdotNode)
	mkDir(xxdotEdge)
	
	if d :
		directedStr="edge []"
	else:
		directedStr="edge [dir=none]"


	# key追加 (cluster用)
	if not k :
		if ni :
			nm.msetstr(v="",a="#key",i=ni,o=xxni).run()
			ni=xxni

		nm.msetstr(v="",a="#key",i=ei,o=xxei).run()
		ei = xxei
		k  = "#key"

	#efs = ef.split(",")
	ef1 = ef[0] 
	ef2 = ef[1] 

	__mkMap(k,nf,ni,ef1,ef2,ei,xxmap)
	__mkNode(k,nf,nl,nv,nc,ni,ef1,ef2,ei,noiso,xxmap,xxnode)

	__mkEdge(k,ef1,ef2,el,ec,ed,ev,ei,xxmap,xxedge)
	# dot用のnodeとedgeデータをcluster別ファイルとして生成
	__dotNode(xxnode,nw,tp,clusterLabel,xxdotNode)
	__dotEdge(xxedge                   ,xxdotEdge)

	depth =None
	if tp=="flat":
		depth=__mkFlat(xxnode,xxtree) # mgvとおなじ
	elif tp=="nest":
		# tree構造の処理
		# クラスタのみtree構造に格納する
		depth=__mkTree(xxnode,xxtree) # mgvとおなじ
	else:	
		raise TypeError("unsupport type " + tp )
		


	xxdotTree=temp.file()
	header='''digraph G {{
  {directedStr}
'''.format(directedStr=directedStr)

	footer="}\n"


	__dotTree(xxtree,depth,header,footer,xxdotTree) # mgvとおなじ
	__replace(xxdotTree,xxdotNode,xxdotEdge,clusterLabel,o)


if __name__ == '__main__':

#i,o,v,f,k=None,title=None,height=None,width=None,cc=None,footer=None):
	mgv(ei="/Users/nain/work/git/view/mgv/check/data/edge.csv",ef="e1,e2",o="./t.dot")
	mgv(ni="/Users/nain/work/git/nysolx/view/mgv/check/data/node1.csv",nf="node",ei="/Users/nain/work/git/nysolx/view/mgv/check/data/edge1.csv",ef="node1,node2",d=True,o="test70.dot")
	mgv(ni="/Users/nain/work/git/nysolx/view/mgv/check/data/node1.csv",nf="node",ei="/Users/nain/work/git/nysolx/view/mgv/check/data/edge1.csv",ef="node1,node2",ed="dir",o="test71.dot")
	mgv(ni="/Users/nain/work/git/nysolx/view/mgv/check/data/node1.csv",nf="node", ei="/Users/nain/work/git/nysolx/view/mgv/check/data/edge1.csv",ef="node1,node2",d=True,ed="dir",o="test72.dot")
	mgv(tp="nest",k="cluster",ni="/Users/nain/work/git/nysolx/view/mgv/check/data/node1.csv",nf="node",ei="/Users/nain/work/git/nysolx/view/mgv/check/data/edge1.csv",ef="node1,node2",o="test73.dot")
	mgv(tp="nest",k="cluster",ni="/Users/nain/work/git/nysolx/view/mgv/check/data/node1.csv",nf="node",ei="/Users/nain/work/git/nysolx/view/mgv/check/data/edge1.csv",ef="node1,node2",ed="dir",o="test74.dot")
	mgv(tp="nest",k="cluster",ni="/Users/nain/work/git/nysolx/view/mgv/check/data/node1.csv",nf="node",ei="/Users/nain/work/git/nysolx/view/mgv/check/data/edge1.csv",ef="node1,node2",d=True,ed="dir",o="test75.dot")


	"""
	mnest2tree(k="cluster",ni="/Users/nain/work/git/view/mgv/check/data/node3.csv",
	nf="node",ei="/Users/nain/work/git/view/mgv/check/data/edge3.csv",ef="node1,node2",
	ev="support",no="./tNode3b.csv",eo="./tEdge3b.csv")

	mautocolor("/Users/nain/work/git/view/mgv/check/data/color.csv","./color1.csv","class1","color",color="category")
	mautocolor("/Users/nain/work/git/view/mgv/check/data/color.csv","./color2.csv","class1","color",color="category",order="descend")
	mautocolor("/Users/nain/work/git/view/mgv/check/data/color.csv","./color3.csv","class1","color",color="category",order="ascend")
	mautocolor("/Users/nain/work/git/view/mgv/check/data/color.csv","./color4.csv","class2","color",color="category")
	mautocolor("/Users/nain/work/git/view/mgv/check/data/color.csv","./color5.csv","value1","color",color="FF0000,0000FF")
	mautocolor("/Users/nain/work/git/view/mgv/check/data/color.csv","./color6.csv","value2","color",color="FF0000,0000FF")
	mautocolor("/Users/nain/work/git/view/mgv/check/data/color.csv","./color7.csv","class1","color",color="category",transmit=50)
	"""


