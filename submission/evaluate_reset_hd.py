import os, sys, csv, math, json
from pathlib import Path
sys.path.insert(0, os.getcwd())
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont
import onnxruntime as ort
orig_session=ort.InferenceSession
def one_thread(path, *args, **kwargs):
    opts=ort.SessionOptions(); opts.intra_op_num_threads=1; opts.inter_op_num_threads=1
    return orig_session(path, sess_options=opts, *args, **kwargs)
ort.InferenceSession=one_thread
from scripts.infer_policy import PolicyInference, MICRODUCK_XML

out=Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
label=sys.argv[2]
model_dir=Path(__file__).resolve().parent / 'models'
paths={'Baseline':str(model_dir/'output_baseline_m01.onnx'),
       'Footslip_m1':str(model_dir/'output_footslip_m10.onnx')}
phases=[('FORWARD',(.15,0.,0.)),('RIGHT',(.12,0.,-1.)),('LEFT',(.12,0.,1.)),('BACKWARD',(-.15,0.,0.))]
model=mujoco.MjModel.from_xml_path(MICRODUCK_XML); model.opt.timestep=.005
model.vis.global_.offwidth=960; model.vis.global_.offheight=544
renderer=mujoco.Renderer(model,height=544,width=960)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
camera=mujoco.MjvCamera(); mujoco.mjv_defaultCamera(camera); camera.type=mujoco.mjtCamera.mjCAMERA_FREE
camera.distance=1.25; camera.azimuth=135; camera.elevation=-25
results={}
try:
 for phase,cmd in phases:
    # A new data object and policy instance also reset action history and time.
    data=mujoco.MjData(model)
    policy=PolicyInference(model,data,walking_onnx_path=paths[label],new_cmd_obs=True,use_projected_gravity=True)
    jid=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_JOINT,'trunk_base_freejoint'); q=int(model.jnt_qposadr[jid])
    data.qpos[q:q+7]=[0,0,.125,1,0,0,0]
    for i,idx in enumerate(policy.joint_qpos_indices): data.qpos[idx]=policy.default_pose[i]
    data.ctrl[:]=policy.default_pose; mujoco.mj_forward(model,data); policy.set_vel_cmd(*cmd)
    writer=imageio.get_writer(str(out/f'{label}_{phase}.mp4'),fps=10,codec='libx264',quality=8,macro_block_size=8)
    rows=[]; fall=None
    try:
     for step in range(401):
      t=step*.02
      w,x,y,z=data.qpos[q+3:q+7]; yaw=math.atan2(2*(w*z+x*y),1-2*(y*y+z*z)); upright=1-2*(x*x+y*y)
      if fall is None and (upright < .5 or data.qpos[q+2] < .07): fall=t
      rows.append([t,phase,*cmd,*data.qpos[q:q+3],yaw,upright,float(policy.get_base_ang_vel()[2])])
      if step<400 and step%5==0:
       camera.lookat[:]=[data.qpos[q],data.qpos[q+1],.12]
       renderer.update_scene(data,camera=camera)
       im=Image.fromarray(renderer.render()); d=ImageDraw.Draw(im)
       d.rectangle((0,0,959,85),fill=(0,0,0)); d.text((16,8),f'{label} | {phase} | t={t:.1f} / 8.0 s',fill='white',font=font)
       d.text((16,45),f'vx={cmd[0]:+.2f} m/s  vy={cmd[1]:+.2f} m/s  yaw={cmd[2]:+.2f} rad/s',fill='white',font=font)
       if fall is not None: d.text((690,45),f'FALL: {fall:.2f}s',fill='yellow',font=font)
       weight='-0.1' if label=='Baseline' else '-1.0'
       d.rectangle((0,506,440,543),fill=(0,0,0)); d.text((16,510),f'Training foot_slip weight {weight}',fill='white',font=font)
       writer.append_data(np.asarray(im))
      if step<400:
       policy.apply_action(policy.infer())
       for _ in range(4): mujoco.mj_step(model,data)
    finally: writer.close()
    with (out/f'{label}_{phase}.csv').open('w',newline='') as f:
     wr=csv.writer(f,lineterminator='\n'); wr.writerow(['time','phase','cmd_vx','cmd_vy','cmd_yaw','x','y','z','yaw_rad','upright_cos','body_gyro_z']); wr.writerows(rows)
    results[phase]={'fall_flag_s':fall,'duration_s':rows[-1][0]}
    (out/f'{label}_summary.json').write_text(json.dumps(results,indent=2))
    print(label,phase,'completed, fall:',fall,flush=True)
finally: renderer.close()
