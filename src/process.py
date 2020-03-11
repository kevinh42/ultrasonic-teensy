#%% # Imports
import serial
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy import ndimage
from scipy import fftpack
import time
#%% # define constants
SAMPLES = 300
CHANNELS = 3
FRAMES = 10
DEADZONE = 40
VOLTAGE_THRESH = 5
TOF_THRESH = 0
STORED_FRAMES = 1500
MEDFILT_KERNEL = 11
STD_THRESH = 25
TRANSDUCER_ORDER = [0,2,1] # left to right

#%% functions
def tap_or_swipe(tofs): #distinguishes between tap and swipe gestures
    nonzeros = tofs[tofs>0]
    print(np.std(nonzeros))
    return np.std(nonzeros)<STD_THRESH
    #returns 1 if swipe, 0 if tap

def classify(tofs): #classify gesture
    chs = tofs.shape[0]
    channel_start_index = np.zeros(chs)
    channel_end_index = np.zeros(chs)
    votes = 0
    for i in range(0,chs):
        plt.plot(tofs[i], label=f"Channel{i}")
        channel_start_index[i] = np.argmax(tofs[i]>0)
        channel_end_index[i] = tofs.shape[1] - np.argmax(np.flip(tofs[i])>0)
        votes += tap_or_swipe(tofs[i])
    plt.legend()
    if votes >=2: #swipe
        print("Swipe")
        direction = 0
        if (channel_start_index[TRANSDUCER_ORDER[2]]>channel_start_index[TRANSDUCER_ORDER[0]]):
            direction +=2
        else:
            direction -=2
        if (channel_end_index[TRANSDUCER_ORDER[2]]>channel_end_index[TRANSDUCER_ORDER[0]]):
            direction +=2
        else:
            direction -=2
        if direction>0:
            print("Right")
        elif direction<0:
            print("Left")
        else:
            print("Centred")
    else: #tap
        print("Tap")

#%% # setup
read_data = np.zeros((FRAMES,CHANNELS,SAMPLES))
read_tof = np.zeros((FRAMES,CHANNELS))
stored_tof = np.zeros((CHANNELS,STORED_FRAMES))

GESTURE_BEGAN = 0
gesture_start_index = 0

#%% # Read data from serial
ser = serial.Serial('COM7', 115200)

while (True):
    #t= time.time()
    ser.write(b'get\n')
    s = ser.read(FRAMES*CHANNELS*SAMPLES)
    #print(time.time()-t)
    read_data = np.array([a for a in s]).reshape((FRAMES,CHANNELS,SAMPLES))
    
    # Process data
    
    read_cleaned = read_data
    for k in range(0,FRAMES):
        for j in range(0,CHANNELS):
            read_cleaned[k,j,0:DEADZONE] = read_cleaned[k,j,DEADZONE+1]   
    #read_envelope = signal.hilbert(read_data,axis=1)
    
    read_cleaned[read_cleaned < VOLTAGE_THRESH] = 0
    # for j in range(0, CHANNELS):
    #     if r < VOLTAGE_THRESH:
    #         r = 0
    read_tof = np.argmax(read_cleaned,axis=2)
    
    stored_tof = np.roll(stored_tof,-FRAMES, axis=1)
    stored_tof[:,-FRAMES:] = read_tof.transpose()
    
    med_tof = ndimage.median_filter(stored_tof,(1,MEDFILT_KERNEL))
    #Gesture started?
    if GESTURE_BEGAN:
    #    if med_tof[]
        #Gesture ended?
        a = med_tof[:,-FRAMES:]
        gesture_start_index -= FRAMES
        if a[a>0].size < FRAMES/3:
            #classify gesture
            classify(med_tof[:,gesture_start_index:])
            break
            #reset flags
            GESTURE_BEGAN = 0
            #break
            
    else:
        a = med_tof[:,-FRAMES:]
        if a[a>0].size > FRAMES/3:
            GESTURE_BEGAN = 1
            gesture_start_index = STORED_FRAMES - FRAMES


    
    fft_tof = fftpack.fft(med_tof, axis=1)
    grad = np.gradient(med_tof, axis=1)
    

    #med_tof

#%%
ser.close()