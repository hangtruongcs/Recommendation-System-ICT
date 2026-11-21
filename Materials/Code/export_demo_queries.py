"""Export five anonymized validation cases; no user IDs or ground truth are saved."""
from pathlib import Path
import json,numpy as np,pandas as pd
from final_test_jiaxing import ROOT,load_transactions,operational,train_bpr
D=load_transactions(ROOT/'28182251/Dataset/Charging_Data.csv');train=D[D.start<'2021-07-01'];val=D[(D.start>='2021-07-01')&(D.start<'2021-10-01')].drop_duplicates('UserID');sites=sorted(train.site.unique());users=sorted(train.UserID.unique());si={s:i for i,s in enumerate(sites)};ui={u:i for i,u in enumerate(users)}
counts=np.zeros((len(users),len(sites)),np.int32)
for (u,s),n in train.groupby(['UserID','site']).size().items():counts[ui[u],si[s]]=n
q=val[val.UserID.isin(ui)&val.site.isin(si)];ids=np.array([ui[u] for u in q.UserID]);P,Q,_=train_bpr(counts,8,np.random.default_rng(20261120));scores=P[ids]@Q.T;op=operational(train);end=op[op.end<pd.Timestamp('2021-07-01')];pay=end[end.payment_time<pd.Timestamp('2021-07-01')];c=20*pay.groupby('site').cost_rate.median().reindex(sites).to_numpy();d=20*end.groupby('site').minutes_rate.median().reindex(sites).to_numpy();chosen=[];seen=set()
for i,row in enumerate(scores):
 top=int(np.argmax(row))
 if top not in seen:
  seen.add(top);chosen.append(i)
 if len(chosen)==5:break
if len(chosen)<5:raise RuntimeError('Không tìm đủ năm truy vấn với Top-1 khác nhau')
result=[]
for number,i in enumerate(chosen,1):
 u=ids[i];result.append({'label':f'Tài xế {number:02d}', 'history_count':int(counts[u].sum()),'sites':[{'site':s,'r':float(scores[i,j]),'c':float(c[j]),'d':float(d[j])} for j,s in enumerate(sites)]})
out=Path(__file__).parent/'pilot_results'/'demo_validation_cases.json';out.write_text(json.dumps({'scope':'first five distinct BPR top sites in validation; seed 20261120; post hoc selected for demonstration, not representative','cases':result},ensure_ascii=False,indent=2)+'\n');print('Wrote',out,'cases',len(result))
