from pathlib import Path
import sys, csv, json, math, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

data_dir=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
font_path=os.environ.get('MICRODUCK_JAPANESE_FONT','/mnt/c/Windows/Fonts/msgothic.ttc')
if not Path(font_path).is_file():
 raise FileNotFoundError('日本語フォントが見つかりません。MICRODUCK_JAPANESE_FONT にフォントのパスを設定してください。')
font=font_manager.FontProperties(fname=font_path)
plt.rcParams.update({'font.family':font.get_name(),'font.size':14,'axes.unicode_minus':False,
                     'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
font_manager.fontManager.addfont(font_path)
policies=[('Baseline','Baseline  (-0.1)','#24699b'),('Footslip_m1','変更後  (-1.0)','#c75934')]
phases=[('FORWARD','前進',.15,0),('RIGHT','右旋回',.12,-1),('LEFT','左旋回',.12,1),('BACKWARD','後退',-.15,0)]
summary={}
for phase,title,vx_cmd,omega in phases:
 fig,(ax,ay)=plt.subplots(1,2,figsize=(9.0,4.4),gridspec_kw={'width_ratios':[1,1.17]})
 fig.suptitle(f'{title}  |  前後 {vx_cmd:+.2f} m/s、横 0、ヨー角速度 {omega:+.2f} rad/s',fontproperties=font,fontsize=16,y=.98)
 summary[phase]={}
 for name,label,color in policies:
  with (data_dir/f'{name}_{phase}.csv').open(newline='') as f: rows=list(csv.DictReader(f))
  d={k:np.array([float(r[k]) for r in rows]) for k in ['time','x','y','yaw_rad']}
  t=d['time']; x=d['x']-d['x'][0]; y=d['y']-d['y'][0]; yaw=np.unwrap(d['yaw_rad']); yaw-=yaw[0]
  style='-' if name=='Baseline' else '--'
  ax.plot(x,y,color=color,lw=2,ls=style,label=label); ax.plot(x[0],y[0],'o',color=color,ms=5); ax.plot(x[-1],y[-1],'x',color=color,ms=8,mew=2)
  for j in (100,200,300): ax.annotate('',xy=(x[j+12],y[j+12]),xytext=(x[j],y[j]),arrowprops={'arrowstyle':'->','color':color,'lw':1.5})
  ay.plot(t,np.degrees(yaw),color=color,lw=2,ls=style,label=label)
  vx=np.gradient(x,t)*np.cos(yaw)+np.gradient(y,t)*np.sin(yaw)
  summary[phase][name]={'x':float(x[-1]),'y':float(y[-1]),'yaw_deg':float(np.degrees(yaw[-1])),
                        'mean_body_vx_approx':float(np.trapezoid(vx,t)/8), 'mean_yaw_rate':float(yaw[-1]/8)}
 ax.set_title('軌跡（○：開始、×：終了）',fontproperties=font,fontsize=14)
 ax.set_xlabel('初期前方 X [m]',fontproperties=font); ax.set_ylabel('初期左方 Y [m]',fontproperties=font)
 ax.set_aspect('equal',adjustable='datalim'); ax.grid(alpha=.25)
 ay.plot([0,8],[0,math.degrees(8*omega)],ls=':',lw=2,color='#606974',label='指令角速度の積分')
 ay.set_title('初期向きからのヨー角変化',fontproperties=font,fontsize=14)
 ay.set(xlim=(0,8),xlabel='時間 [s]',ylabel='ヨー角変化 [度]'); ay.xaxis.label.set_fontproperties(font); ay.yaxis.label.set_fontproperties(font)
 ay.grid(alpha=.25); ay.legend(prop=font_manager.FontProperties(fname=font_path,size=12),loc='best',frameon=True)
 fig.tight_layout(rect=(0,0,1,.92)); fig.savefig(out/f'figure_{phase.lower()}.png',dpi=240); plt.close(fig)
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
