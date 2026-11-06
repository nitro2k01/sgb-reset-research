import sys, json, collections, pickle
sys.path.insert(0,'.')
from ramanalyze import *
FW={'SGB1_10':'sgb10','SGB1_11':'sgb11','SGB1_12':'sgb12','SGB2':'sgb2'}
res={}
for fw,sn in FW.items():
    cls,info,ex=classify(fw)
    st={int(k,16):v for k,v in json.load(open(f'ram/static_{sn}.json')).items()}
    final={}
    for a in range(N):
        c=cls[a]
        if c=='free' and a in st: c='static'
        final[a]=c
    res[fw]=(final,st,{a:(sorted(info[a]['wpc'])[:4],sorted(info[a]['rpc'])[:4]) for a in range(N) if cls[a]!='free'})
pickle.dump(res,open('ram/final.pkl','wb'))
print('saved')
