from cgi import print_arguments
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options
import re
import os
import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
import ffmpeg
import yt_dlp as yt
import h5py

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
        self.chrome_driver = ChromeDriverManager().install()
        options = Options()
        options.add_argument('--headless=chrome')
        options.add_extension('extension_5_3_0_0.crx')
        #print("aqui")
        self.driver = webdriver.Chrome(service=Service(self.chrome_driver), options=options )
        #print("aqui")
        if output[-1] == "/":
            self.output = output
        else:
            self.output = output+"/"

    #def __del__(self):
    #    self.driver.quit()

    def find_heat_map(self):
        #options = Options()
        #options.add_argument('headless')
        #options.add_argument("'--load_extension=~/.config/google-chrome/Default/Extensions'")
        #options.add_extension('extension_5_3_0_0.crx')
        #s=Service(ChromeDriverManager().install())
        #driver = webdriver.Chrome(service=s, options=options)
        self.driver.maximize_window()
        time.sleep(5)
        self.driver.get(self.url)
        time.sleep(15)
        self.driver.save_screenshot('./teste.png')
        elements = self.driver.find_elements(By.XPATH, '//*[@class="ytp-heat-map-svg"]  ')
        svg = [WebElement.get_attribute('innerHTML') for WebElement in elements]
        file = open("output.txt", 'w')
        try:
            file.write(svg[0])
            file.close()
        except:
            print("can't extact heatmap")
        idx = 0
        self.driver.close()
        return svg[0]

    def get_heat_map(self, text):
        #with open("output.txt") as f:
            #lines = f.readlines()
            #line = lines[0]
        line = text
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
        heatmap = np.round(heatmap, 4)

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
        title =  (info['title'])
        title = re.sub(r"[^a-zA-Z0-9 .]","", title) ##remove especial characters except space and dot
        title = title.replace(" ", "_")
        yt_config = {
            'outtmpl': self.output+"video/"+title+".mp4",
            "format": "b[height<=480]" 
        }
        yt_config_2 = {
            'outtmpl': self.output+"audio/"+title+".wav",
            "format": "ba"
        }
        yt_dl = yt.YoutubeDL(yt_config)
        yt_dl_a = yt.YoutubeDL(yt_config_2)
        yt_dl.download([self.url])
        yt_dl_a.download([self.url])
        success = False
        for i in range(3):
            try:
                print("first try")
                text = self.find_heat_map()
                heatmap = self.get_heat_map(text)
                success = True
            except:
                print("can't find heatmap")
                if i == 2:
                    exit(0  )
            
            if success:
                print("success")
                break

        n_frames, duration, frame_rate = self.extract_video_data(title+".mp4")
        heatmap = self.normalize(heatmap, (int(n_frames)/heatmap.shape[0]))
        return title, n_frames, duration, frame_rate, heatmap
        

def args_helper():
    parser = argparse.ArgumentParser()
    parser.add_argument("-url")
    parser.add_argument("-o")
    parser.add_argument("-mf")
    parser.add_argument("-input_file")
    parser.add_argument("-dataset")
    args = parser.parse_args()
    return args

def create_json_object(title, n_frames, duration, frame_rate, heatmap):
    data = {
        "title": title,
        "n_frame": n_frames,
        "duration": duration,
        "frame_rate": frame_rate,
        "heatmap": heatmap
    }
    #json_object = json.dumps(data, cls=NumpyEncoder)
    return data

def create_json(title, n_frames, duration, frame_rate, heatmap, output_path):
    os.makedirs(output_path+"/jsons/", exist_ok=True)
    json_object = create_json_object(title, n_frames, duration, frame_rate, heatmap)
    json_object = json.dumps(json_object, cls=NumpyEncoder)
    with open("{}/jsons/{}.json".format(output_path, title), "w") as out:
        out.write(json_object)

def create_jsons(output_path, jsons_objects):
    os.makedirs(output_path+"/jsons/", exist_ok=True)
    jsons_object = json.dumps(jsons_objects, cls=NumpyEncoder)
    with open("{}/jsons/{}.json".format(output_path, "youtube"), "w") as out:
        out.write(jsons_object)
    
def read_input_file(input_file_path):
    videos = []
    with open(input_file_path) as file:
        for line in file:
            print(line)
            videos.append(line)
    return videos

def create_hdf5(objects, filename):
    f = h5py.File(filename, 'w')
    for i in range(len(objects)):
        #print(objects[i])
        g = f.create_group('video_{}'.format(i+1))
        g.create_dataset('name', data=objects[i]['name'])
        g.create_dataset('n_frames', data=objects[i]['n_frames'])
        g.create_dataset('duration', data=objects[i]['duration'])
        g.create_dataset('frame_rate', data=objects[i]['frame_rate'])
        g.create_dataset('heatmap', data=objects[i]['heatmap'], dtype='i')
    f.close()
        
    
def main():
    args = args_helper()
    if args.input_file:
        videos = read_input_file(args.input_file)
        hdf5_objects = []
        for video in videos:
            ht = Heat_Map_Extractor(args.o, video)
            title, n_frames, duration, frame_rate, heatmap = ht.video_download()
            hdf5_objects.append({'name': title.split('.mp4')[0],
                                'n_frames': n_frames, 
                                'duration': duration, 
                                'frame_rate': frame_rate, 
                                'heatmap': heatmap})
            #json_objects.append(create_json_object(title.split('.mp4')[0], n_frames, duration, frame_rate, heatmap))
        #create_jsons(args.o, json_objects)
        create_hdf5(hdf5_objects, args.dataset)
    else:
        ht = Heat_Map_Extractor(args.o, args.url)
        title, n_frames, duration, frame_rate, heatmap = ht.video_download()
        #create_json(title.split('.mp4')[0], n_frames, duration, frame_rate, heatmap, args.o)
        print(n_frames)
        print(duration)
        print(frame_rate)
        print(heatmap)
        print(title)
        create_hdf5([{'name': title.split('.mp4')[0],
                    'n_frames': n_frames, 
                    'duration': duration, 
                    'frame_rate': frame_rate, 
                    'heatmap': heatmap}], args.dataset)

if __name__ == "__main__":
    main()