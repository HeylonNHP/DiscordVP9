'''
Encode 8mb discord VP9
'''
import subprocess
import sys
import re
from os import listdir
from os.path import isfile, join


class AudioVideoRatio:
    audio: float = 0.1
    video: float = 0.9


class Ffmpeg:
    ffmpegLocation = 'ffmpeg'
    audioVideoBitrateRatios = AudioVideoRatio()

    def run_and_print_output(self, array_command: list[str]):
        # result = run(arrayCommand, shell=False, universal_newlines=True, stderr=STDOUT, check=False).stdout
        p = subprocess.Popen(array_command, shell=False, universal_newlines=True, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             close_fds=True)
        result = p.stdout.read()
        print(result)

    def run_ffmpeg(self, arguments: list[str]):
        cmd_line = [self.ffmpegLocation] + arguments
        self.run_and_print_output(cmd_line)

    def get_length(self, input_path):
        """
        Get the duration of a video in seconds as a float
        """
        length_seconds = 0.0
        result = subprocess.run([self.ffmpegLocation, '-i', input_path], stderr=subprocess.PIPE)
        lines = result.stderr.splitlines()

        for line in lines:
            try:
                decoded_line = line.decode('UTF-8')
            except:
                continue
            if 'Duration:' in decoded_line:
                x = re.search(r"Duration: ([0-9]+:[0-9]+:[0-9]+\.*[0-9]*)", decoded_line)
                time_string = x.group(1)
                time_string_list = time_string.split(':')
                length_seconds += float(time_string_list[0]) * 3600
                length_seconds += float(time_string_list[1]) * 60
                length_seconds += float(time_string_list[2])
                print('Fetched video length (secs):', length_seconds)
                return length_seconds

    def has_audio(self, input_path):
        """
        Check if input has audio
        """
        result = subprocess.run([self.ffmpegLocation, '-i', input_path], stderr=subprocess.PIPE)
        lines = result.stderr.splitlines()

        for line in lines:
            try:
                decoded_line = line.decode('UTF-8')
            except:
                continue
            if "Stream".lower() in decoded_line.lower() and "Audio".lower() in decoded_line.lower():
                return True
        return False

    def ffmpeg_2pass(self, input_path: str, output_path: str, total_bitrate_kbps: int):
        audio_bitrate = total_bitrate_kbps * self.audioVideoBitrateRatios.audio
        video_bitrate = total_bitrate_kbps * self.audioVideoBitrateRatios.video

        # Limit audio to 128kbps max
        if audio_bitrate > 128:
            audio_bitrate = 128
            video_bitrate = total_bitrate_kbps - audio_bitrate

        input_has_audio = self.has_audio(input_path)
        if not input_has_audio:
            audio_bitrate = 0
            video_bitrate = total_bitrate_kbps

        input_cmd = ['-y', '-i', input_path]
        pix_fmt = ['-pix_fmt', 'yuv420p']
        codec = ['-c:v', 'libvpx-vp9']
        bitrate = ['-b:v', str(video_bitrate) + 'k']
        quality = ['-quality', 'best']
        preset = ['-speed', '0']
        parallelism = [
            '-threads', '4', '-tile-rows', '0', '-tile-columns', '1', '-frame-parallel', '0', '-auto-alt-ref', '1',
            '-row-mt', '1']
        lag_in_frames = ['-lag-in-frames', '25', '-arnr-maxframes', '25']
        tpl = ['-enable-tpl', '1']
        keyframes = ['-g', '9999']
        aq_mode = ['-aq-mode', '0']
        audio = ['-ac', '2', '-c:a', 'libopus', '-frame_duration', '120', '-b:a', str(audio_bitrate) + 'k']

        # Passes
        for i in range(1, 3):
            local_preset = [preset[0], '4'] if i == 1 else preset
            local_audio = ['-an'] if i == 1 or not input_has_audio else audio
            local_format = ['-f', 'null'] if i == 1 else ['-f', 'webm']
            local_output = ['-'] if i == 1 else [output_path]

            self.run_ffmpeg(
                input_cmd + pix_fmt + codec + ['-pass',
                                               str(i)] + bitrate + quality + local_preset + parallelism + lag_in_frames + tpl + keyframes + aq_mode + local_audio + local_format + local_output)

    def ffmpeg_2pass_size_limit(self, input_path: str, output_path: str, size_in_mb: float, bitrate_limit: int):
        video_length_seconds = self.get_length(input_path)
        bitrate_kbps = (size_in_mb * 8 * 1024) / video_length_seconds
        bitrate_kbps = 2000 if bitrate_kbps > bitrate_limit else bitrate_kbps
        self.ffmpeg_2pass(input_path, output_path, bitrate_kbps)


def main():
    arguments = sys.argv

    mypath = arguments[1]
    whitelisted_extensions = ['mp4']
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    ffmpeg = Ffmpeg()

    if len(arguments) > 2:
        whitelisted_extensions = arguments[2].split(',')

    for file in onlyfiles:
        filepath = join(mypath, file)
        if file[-3:].lower() in whitelisted_extensions:
            ffmpeg.ffmpeg_2pass_size_limit(filepath, filepath + '-2pass.webm', 8, 2000)


main()
