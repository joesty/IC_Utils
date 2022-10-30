from moviepy.editor import *
import argparse



class VideoEditor:
    def __init__(self, video_path):
        self.video = VideoFileClip(video_path).subclip(60,)

    def info(self,):
        print("Duration:", self.video.duration)
        print("FPS:", self.video.fps)

    def cut(self, start, end):
        clip = self.video.subclip(start, end)
        clip.write_videofile('teste.mp4', fps=self.video.fps, codec='libx264')

def args_helper():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", "-i")
    parser.add_argument("--output_file", "-o")
    parser.add_argument("--init", '-in')
    parser.add_argument("--end", '-en')
    args = parser.parse_args()
    return args


video = VideoEditor('data/video/Buenos_Aires_Argentina___City_Walking_Tour_4K.mp4')

video.info()
video.cut(0, 60)

