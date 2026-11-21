"""Post hoc validation diagnostics; no model selection or test evaluation."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
from final_test_jiaxing import ROOT,load_transactions,operational,train_bpr

df=load_transactions(ROOT/'28182251/Dataset/Charging_Data.csv');train=df[df.start<'2021-07-01'];val=df[(df.start>='2021-07-01')&(df.start<'2021-10-01')].drop_duplicates('UserID')
sites=sorted(train.site.unique());users=sorted(train.UserID.unique());si={s:i for i,s in enumerate(sites)};ui={u:i for i,u in enumerate(users)}
counts=np.zeros((len(users),len(sites)),dtype=np.int32)
for (u,s),n in train.groupby(['UserID','site']).size().items():counts[ui[u],si[s]]=n
q=val[val.UserID.isin(ui)&val.site.isin(si)];uids=np.array([ui[u] for u in q.UserID]);target=np.array([si[s] for s in q.site]);m=len(sites)
P,Q,_=train_bpr(counts,8,np.random.default_rng(20261120));r=P[uids]@Q.T
pop=counts.sum(axis=0);pf=counts[uids].astype(float)+pop/(pop.max()+1)*1e-6
last=train.drop_duplicates('UserID',keep='last').set_index('UserID').site
lastid=np.array([si[x] for x in q.UserID.map(last)]);recent=np.broadcast_to(pop/(pop.max()+1)*1e-6,r.shape).copy();recent[np.arange(len(q)),lastid]+=1
cutoff=pd.Timestamp('2021-07-01'); op=operational(train);dur=op[op.end<cutoff];pay=dur[dur.payment_time<cutoff];c=pay.groupby('site').cost_rate.median().reindex(sites).to_numpy();d=dur.groupby('site').minutes_rate.median().reindex(sites).to_numpy()
def pareto(rr,cc,dd):
 z=np.column_stack([-rr,cc,dd]);dominates=(z[:,None,:]<=z[None,:,:]).all(2)&(z[:,None,:]<z[None,:,:]).any(2);remaining=np.ones(len(rr),bool);out=[]
 while remaining.any():
  front=remaining&~(dominates&remaining[:,None]).any(0);ids=np.flatnonzero(front);out.extend(sorted(ids,key=lambda j:(-rr[j],j)));remaining[front]=False
 return np.array(out)
def metric(scores):
 order=np.argsort(-scores,axis=1,kind='stable');ranks=np.argmax(order==target[:,None],axis=1)+1
 return {'ndcg3':float(np.mean(np.where(ranks<=3,1/np.log2(ranks+1),0))),'hit3':float(np.mean(ranks<=3))}
result={'scope':'post hoc exploratory validation; seed 20261120; same warm users','users':len(q),'personal_frequency':metric(pf),'most_recent_site':metric(recent),'bpr_mf':metric(r),'candidate_subset':{},'duration_shrinkage':{}}
rng=np.random.default_rng(7217)
for size in [5,8,13]:
 vals=[]; overlap=[]
 for rr,t in zip(r,target):
  others=np.delete(np.arange(m),t); subset=np.sort(np.r_[t,rng.choice(others,size=size-1,replace=False)]); order=pareto(rr[subset],c[subset],d[subset]); ranked=subset[order]; normal=subset[np.argsort(-rr[subset],kind='stable')];rank=np.where(ranked==t)[0][0]+1;vals.append(1/np.log2(rank+1) if rank<=3 else 0);overlap.append(len(set(ranked[:3])&set(normal[:3]))/3)
 result['candidate_subset'][str(size)]={'pareto_ndcg3':float(np.mean(vals)),'top3_set_overlap_vs_bpr':float(np.mean(overlap))}
base=[pareto(rr,c,d) for rr in r]
for shrink in [0,0.5,1]:
 # Descriptive estimator sensitivity: pull site medians toward global median; no validation labels used for perturbation.
 ds=(1-shrink)*d+shrink*np.median(dur.minutes_rate);orders=[pareto(rr,c,ds) for rr in r];pos=np.array([int(np.where(order==t)[0][0])+1 for order,t in zip(orders,target)])
 result['duration_shrinkage'][str(shrink)]={'pareto_ndcg3':float(np.mean(np.where(pos<=3,1/np.log2(pos+1),0))),'top3_changed_vs_original':float(np.mean([not np.array_equal(a[:3],b[:3]) for a,b in zip(base,orders)]))}
out=Path(__file__).parent/'pilot_results'/'validation_robustness_posthoc.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
