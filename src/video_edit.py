from moviepy.editor import *
import argparse
import h5py
import csv
import pandas as pd
from read_utils import *

secs = 300 #size of video

class VideoEditor:
    def __init__(self, video_path):
        self.video = VideoFileClip(video_path)

    def info(self,):
        print("Duration:", self.video.duration)
        print("FPS:", self.video.fps)

    def cut(self, start, end, name):
        clip = self.video.subclip(start, end)
        clip.write_videofile(name, fps=self.video.fps, codec='libx264')

class VideoForDataset:
    def __init__(self, video_path, h5_file, csv):
        #self.video = VideoEditor(video_path)
        self.h5_file = h5_file
        self.csv = csv

    def get_best_window(self, name):
        r = ReadFile()
        pa = r.read_csv(self.csv, name)
        gt, nframes, fps = r.read_h5(self.h5_file, name)
        pa = r.normalization(pa, fps)
        print(len(pa))
        print(len(gt))
        fw = FindWindow(secs)
        bt = fw.find(pa, gt, fps)
        print('Best Time:', bt)
        return bt

def args_helper():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", "-i")
    parser.add_argument("--output_file", "-o")
    parser.add_argument("--init", '-in')
    parser.add_argument("--end", '-en')
    args = parser.parse_args()
    return args
    
class Dataset:
    def __init__(self, h5_file, csv_file, video_path, output_path):
        self.h5_file = h5_file
        self.csv_file = csv_file
        self.video_path = video_path
        self.output_path = output_path

    def create_dataset(self,):
        rf = ReadFile()
        names = rf.get_names(self.h5_file)

        for name in names:
            print(name)
            vfd = VideoForDataset("", self.h5_file, self.csv_file)
            bt = vfd.get_best_window(name)

            video = VideoEditor(self.video_path+name+'.mp4')

            video.info()
            video.cut(bt, bt+secs, 'video_teste.mp4')


def main():
    path = '../data/video/'
    h5_file = 'yt.h5'
    csv_file = 'youtube_test.csv'
    dataset = Dataset(h5_file, csv_file, path, "")
    dataset.create_dataset()

if __name__ == "__main__":
    main()