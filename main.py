'''
Encode 8mb discord VP9
'''
import subprocess


def run_ffmpeg(arguments: list):
    cmd_line = ['ffmpeg'] + arguments
    subprocess.run(cmd_line)
