from pathlib import Path
import sys, csv, math
import numpy as np
import matplotlib.pyplot as plt
out=Path(sys.argv[1])
names=[('Baseline','Baseline (foot_slip -0.1)','#2368a0'),('Footslip_m1','Changed (foot_slip -1.0)','#d35330')]
phases=[('FORWARD','Forward',.15,0),('RIGHT','Right turn',.12,-1),('LEFT','Left turn',.12,1),('BACKWARD','Backward',-.15,0)]
for phase,title,vx,wz in phases:
 fig,(xy,heading_ax)=plt.subplots(1,2,figsize=(11,4.5),gridspec_kw={'width_ratios':[1,1.25]})
 for name,label,col in names:
  with (out/f'{name}_{phase}.csv').open(newline='') as f: rows=list(csv.DictReader(f))
  d={k:np.array([float(r[k]) for r in rows]) for k in ('time','x','y','yaw_rad')}
  x=d['x']-d['x'][0]; y=d['y']-d['y'][0]; yaw=np.unwrap(d['yaw_rad']); yaw-=yaw[0]
  xy.plot(x,y,color=col,lw=2,label=label); xy.scatter(x[0],y[0],marker='o',color=col,s=28,zorder=3)
  xy.scatter(x[-1],y[-1],marker='x',color=col,s=55,zorder=3)
  for i in (100,200,300): xy.annotate('',xy=(x[i+10],y[i+10]),xytext=(x[i],y[i]),arrowprops={'arrowstyle':'->','color':col,'lw':1.2})
  heading_ax.plot(d['time'],np.degrees(yaw),color=col,lw=2,label=label)
 xy.set(xlabel='World X, initial forward [m]',ylabel='World Y, initial left [m]',title='Trajectory: start = circle, end = x')
 xy.set_aspect('equal',adjustable='datalim'); xy.grid(alpha=.3)
 heading_ax.plot([0,8],[0,math.degrees(wz*8)],color='gray',ls='--',lw=1.3,label='Integrated yaw-rate command')
 heading_ax.set(xlabel='Time [s]',ylabel='Yaw change [deg]',title='Heading from initial orientation',xlim=(0,8))
 heading_ax.grid(alpha=.3); heading_ax.legend(fontsize=8)
 fig.suptitle(f'{title}: vx={vx:+.2f} m/s, vy=0, yaw rate={wz:+.2f} rad/s | reset at start',fontsize=12)
 fig.tight_layout(); fig.savefig(out/f'command_{phase.lower()}.png',dpi=200); plt.close(fig)
