import pandas as pd
import numpy as np
from scipy.stats import pearsonr 
import h5py

class ReadFile:
    def __ini__(self,):
        pass
    
    def read_csv(self, file, clipname):
        df = pd.read_csv(file)
        df = df.fillna(0)
        pa_matlab = list(df.loc[df['clip'] == clipname, "PA"])
        pa_matlab = np.asarray(pa_matlab)
        pa_matlab = (pa_matlab-min(pa_matlab))/(max(pa_matlab)-min(pa_matlab))
        return pa_matlab

    def read_h5(self, file, clipname):
    #f = h5py.File('eccv16_dataset_summe_google_pool5.h5', 'r')
        f = h5py.File(file, 'r')
        videos = list(f.keys())
        for video in videos:
            if f[video]['name'][()].decode() == clipname:
                gtscore = f[video]['heatmap'][()]
                nframes = f[video]['n_frames'][()]
                fps = f[video]['frame_rate'][()]
                break
        nframes = int(nframes)
        gtscore = gtscore.tolist()
        gtscore = np.asarray(gtscore)
        gtscore = gtscore/100
        return gtscore, nframes, fps

    def normalization(self, pa_matlab, frame_rate):
        pa_matlab = np.repeat(pa_matlab, int(frame_rate))
        return pa_matlab

    def get_names(self, file):
        f = h5py.File(file, 'r')
        videos = list(f.keys())
        v_names = []
        for video in videos:
            v_names.append(f[video]['name'][()].decode())
        return v_names

class FindWindow:
    def __init__(self, size):
        self.window = size
        
    def find(self, in1, in2, fps, overlap=1):
        """
        Find best correlation window
        using pearson correlation
        """
        if len(in1) > len(in2):
            aux = in2
            in2 = in1
            in1 = aux
        best_window = -np.inf
        best_time = -np.inf
        for i in range(0, len(in1)-int(self.window*fps), int(overlap*fps)):
            #print(i)
            corr, _ = pearsonr(in1[i:i+int(self.window*fps)], in2[i:i+int(self.window*fps)])
            if corr > best_window:
                best_window = corr
                best_time = i/fps
                #print(corr)
            #print(best_time)
        return best_time
        

