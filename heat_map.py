from cgi import print_arguments
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options
import cv2 as cv
import sys
import re
import os
import numpy as np
import matplotlib.pyplot as plt 
import h5py                                                                                                                                                                                                                                   
import pdb
import argparse
import json
import ffmpeg                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
#import youtube_dl as yt
import yt_dlp as yt


url = "https://www.youtube.com/watch?v=W93XyXHI8Nw"
output_path = './YouTube/video'

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class Heat_Map_Extractor:

    def __init__(self, output, input):
        self.url = input
        self.output = output
        if output[-1] == "/":
            self.output = output
        else:
            self.output = output+"/"

    def find_heat_map(self):
        options = Options()
        options.add_argument('headless')
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options=options)
        driver.maximize_window()
        driver.get(self.url)
        time.sleep(5)
        elements = driver.find_elements(By.XPATH, '//*[@class="ytp-heat-map-svg"]  ')
        svg = [WebElement.get_attribute('innerHTML') for WebElement in elements]
        file = open("output.txt", 'w')
        try:
            file.write(svg[0])
            file.close()
        except:
            print("can't extact heatmap")
            driver.close()
            exit(0)
        driver.close()

    def get_heat_map(self):
        with open("output.txt") as f:
            lines = f.readlines()
            line = lines[0]
            beg_search_str = '<path class="ytp-heat-map-path" d="'
            end_search_str = '" fill="white" fill-opacity="0.6"></path>'
            beg_idx = line.index(beg_search_str) + len(beg_search_str)
            end_idx = line.index(end_search_str)
            raw_seq = line[beg_idx:end_idx]
        seq = re.split(",| |'", raw_seq)[3:]
        heatmap = []
        for i in range(len(seq)):
            idx = i % 7
            if idx == 6:
                heatmap.append(float(seq[i]))

        heatmap = 1-np.asarray(heatmap)
        heatmap = heatmap + abs(min(heatmap))

        return heatmap

    def normalize(self, heatmap, n_frames):
        return np.repeat(heatmap, n_frames)

    def extract_video_data(self, new_title):
        meta = (ffmpeg.probe(self.output+"video/"+new_title)["streams"])
        n_frames = meta[0]['nb_frames']
        duration = meta[0]['duration']
        frame_rate = meta[0]['r_frame_rate'].split('/')[0]
        return n_frames, duration, frame_rate

    def video_download(self):
        yt_dl = yt.YoutubeDL()
        info = yt_dl.extract_info(self.url, download=False)
        title =  (info['title']+".mp4")
        title = title.replace(" ", "_")
        yt_config = {
            'outtmpl': self.output+"video/"+title,
            "format": "mp4" 
        }
        yt_dl = yt.YoutubeDL(yt_config)
        yt_dl.download([self.url])
        self.find_heat_map()
        heatmap = self.get_heat_map()
        n_frames, duration, frame_rate = self.extract_video_data(title)
        heatmap = self.normalize(heatmap, (int(n_frames)/heatmap.shape[0]))
        return title, n_frames, duration, frame_rate, heatmap
        

def args_helper():
    parser = argparse.ArgumentParser()
    parser.add_argument("-url")
    parser.add_argument("-o")
    parser.add_argument("-mf")
    parser.add_argument("-if")
    args = parser.parse_args()
    return args

def create_json(title, n_frames, duration, frame_rate, heatmap, output_path):
    os.makedirs(output_path+"/jsons/", exist_ok=True)
    data = {
        "title": title,
        "n_frame": n_frames,
        "duration": duration,
        "frame_rate": frame_rate,
        "heatmap": heatmap
    }

    json_object = json.dumps(data, cls=NumpyEncoder)
    with open("{}/jsons/{}.json".format(output_path, title), "w") as out:
        out.write(json_object)

def read_input_file(input_file_path):
    videos = []
    with open(input_file_path) as file:
        for line in file:
            print(line)
            videos.append(line)

def main():
    args = args_helper()
    ht = Heat_Map_Extractor(args.o, args.url)
    title, n_frames, duration, frame_rate, heatmap = ht.video_download()
    create_json(title.split('.mp4')[0], n_frames, duration, frame_rate, heatmap, args.o)
    print(n_frames)
    print(duration)
    print(frame_rate)
    print(heatmap)
    print(title)

if __name__ == "__main__":
    main()