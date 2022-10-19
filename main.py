'''
Encode 8mb discord VP9
'''
import subprocess
import sys
import re


class AudioVideoRatio:
    audio: float = 0.1
    video: float = 0.9


class Ffmpeg:
    ffmpegLocation = 'ffmpeg'
    audioVideoBitrateRatios = AudioVideoRatio()

    def run_ffmpeg(self, arguments: list[str]):
        cmd_line = [self.ffmpegLocation] + arguments
        return subprocess.run(cmd_line)

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

    def ffmpeg_2pass(self, input_path: str, output_path: str, total_bitrate_kbps: int):
        audio_bitrate = total_bitrate_kbps * self.audioVideoBitrateRatios.audio
        video_bitrate = total_bitrate_kbps * self.audioVideoBitrateRatios.video
        # ffmpeg -i "$1" -pix_fmt yuv420p -c:v libvpx-vp9 -pass 1 -b:v $bitrate -threads 1 -speed 4 -tile-columns 0 -frame-parallel 0 -auto-alt-ref 1 -lag-in-frames 25 -g 9999 -aq-mode 0 -an -f null -
        # ffmpeg -i "$1" -pix_fmt yuv420p -c:v libvpx-vp9 -pass 2 -b:v $bitrate -threads 1 -speed 0 -tile-columns 0 -frame-parallel 0 -auto-alt-ref 1 -lag-in-frames 25 -g 9999 -aq-mode 0 -ac 2 -c:a libopus -frame_duration 120 -b:a $audiobitrate -f webm "$1"-2pass.webm

        input_cmd = ['-i', input_path]
        pix_fmt = ['-pix_fmt', 'yuv420p']
        codec = ['-c:v', 'libvpx-vp9']
        bitrate = ['-b:v', str(video_bitrate)]
        preset = ['-speed', '0']
        parallelism = [
            '-threads', '1', '-tile-columns', '0', '-frame-parallel', '0', '-auto-alt-ref', '1']
        lag_in_frames = ['-lag-in-frames', '25']
        keyframes = ['-g', '9999']
        aq_mode = ['-aq_mode', '0']
        audio = ['-ac', '2', '-c:a', 'libopus', '-frame_duration', '120', '-b:a', str(audio_bitrate)]

        # Passes
        for i in range(1, 2):
            local_preset = [preset[0], '4'] if i == 1 else preset
            local_audio = ['-an'] if i == 1 else audio
            local_format = ['-f', 'null'] if i == 1 else ['-f', 'webm']
            local_output = ['-'] if i == 1 else [output_path]

            self.run_ffmpeg(
                input_cmd + pix_fmt + codec + ['-pass',
                                               str(i)] + bitrate + local_preset + parallelism + lag_in_frames + keyframes + aq_mode + local_audio + local_format + local_output)

    def ffmpeg_2pass_size_limit(self, input_path: str, output_path: str, size_in_mb: float):
        video_length_seconds = self.get_length(input_path)
        bitrate_kbps = (size_in_mb * 8 * 1024) / video_length_seconds
        self.ffmpeg_2pass(input_path, output_path, bitrate_kbps)


def main():
    arguments = sys.argv
    ffmpeg = Ffmpeg()
    ffmpeg.ffmpeg_2pass("", "", 1000)


main()
