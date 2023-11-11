import gradio as gr
import os
import subprocess
import shutil

def list_dir(directory):
    return [f for f in os.listdir(directory) if not os.path.isfile(os.path.join(directory, f))]

# UI

def fps_change(fps):
    frames = int(duration * fps)
    return gr.HTML(f"Total frames: {frames}")

def reload_click():
    return gr.Dropdown(choices=list_dir('data/'), value=list_dir('data/')[0], label='Select Dataset')

def prepare_click(video, fps):
    global stop_thread
    stop_thread = False

    dataset = os.path.splitext(os.path.basename(video))[0]
    if not os.path.exists(os.path.join(root_directory, "data", dataset)):
        os.makedirs(os.path.join(root_directory, "data", dataset))

    video_path = os.path.join(root_directory, "data", dataset, os.path.basename(video))
    shutil.copy(video, video_path)

    command1 = f"python scripts/colmap2nerf.py --video_in {video_path} --video_fps {fps} --run_colmap --aabb_scale 16 --overwrite"
    process = subprocess.Popen(command1, shell=True, cwd=root_directory)
    process.wait()

    command2 = f"python {os.path.join(root_directory, 'scripts/colmap2nerf.py')} --colmap_matcher exhaustive --run_colmap --aabb_scale 16 --overwrite"
    process = subprocess.Popen(command2, shell=True, cwd=os.path.join(root_directory, "data", dataset))
    process.wait()

    return gr.Dropdown(choices=list_dir('data/'), value=dataset, label='Select Dataset')

def run_click(dataset):
    global stop_thread
    stop_thread = False

    command = f"instant-ngp {os.path.join(root_directory, 'data', dataset)}"
    subprocess.Popen(command, shell=True, cwd=root_directory)

# APP

duration = 0
stop_thread = False
root_directory = os.getcwd()
with gr.Blocks(title='ibarcena.net') as app:
    with gr.Row():
        with gr.Column():
            video = gr.Video(label='Video')
        with gr.Column():
            fps = gr.Slider(minimum=0.1, maximum=30, value=4, label='FPS')
            prepare = gr.Button('Prepare Dataset')
            with gr.Row():
                dataset = gr.Dropdown(choices=list_dir('data/'), value=list_dir('data/')[0], show_label=False, container=False)
                reload = gr.Button('🔄️')
            run = gr.Button('NeRF it!')

    reload.click(reload_click, outputs=[dataset])
    prepare.click(prepare_click, inputs=[video, fps], outputs=[dataset])
    run.click(run_click, inputs=[dataset])

    app.queue().launch(share=False, debug=True)
