# -*- coding: utf-8 -*-
"""
Estimate Relaxation from Band Powers

This example shows how to buffer, epoch, and transform EEG data from a single
electrode into values for each of the classic frequencies (e.g. alpha, beta, theta)
Furthermore, it shows how ratios of the band powers can be used to estimate
mental state for neurofeedback.

The neurofeedback protocols described here are inspired by
*Neurofeedback: A Comprehensive Review on System Design, Methodology and Clinical Applications* by Marzbani et. al

Adapted from https://github.com/NeuroTechX/bci-workshop
"""
import pyautogui
from time import sleep
from os import system as sys
from datetime import datetime
import numpy as np  # Module that simplifies computations on matrices
from pylsl import StreamInlet, resolve_byprop  # Module to receive EEG data
import playsound
import sys
sys.path.append(r"c:\Users\anush\OneDrive\Documents\GitHub\museEEG")
import utils  # Our own utility functions

class Band:
    Delta = 0
    Theta = 1
    Alpha = 2
    Beta = 3

""" EXPERIMENTAL PARAMETERS """
# Modify these to change aspects of the signal processing

# Length of the EEG data buffer (in seconds)
# This buffer will hold last n seconds of data and be used for calculations
BUFFER_LENGTH = 3

# Length of the epochs used to compute the FFT (in seconds)
EPOCH_LENGTH = 1

# Amount of overlap between two consecutive epochs (in seconds)
OVERLAP_LENGTH = 0.5

# Amount to 'shift' the start of each next consecutive epoch
SHIFT_LENGTH = EPOCH_LENGTH - OVERLAP_LENGTH

# Index of the channel(s) (electrodes) to be used
# 0 = left ear, 1 = left forehead, 2 = right forehead, 3 = right ear
INDEX_CHANNELS = [1, 2]

if __name__ == "__main__":

    """ 1. CONNECT TO EEG STREAM """

    # Search for active LSL streams
    print('Looking for an EEG stream...')
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if len(streams) == 0:
        raise RuntimeError('Can\'t find EEG stream.')

    # Set active EEG stream to inlet and apply time correction
    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=12)

    # Get the stream info
    info = inlet.info()

    # Get the sampling frequency
    # This is an important value that represents how many EEG data points are
    # collected in a second. This influences our frequency band calculation.
    # for the Muse 2016, this should always be 256
    fs = int(info.nominal_srate())

    """ 2. INITIALIZE BUFFERS """

    # Initialize raw EEG data buffer
    eeg_buffer = np.zeros((int(fs * BUFFER_LENGTH), 1))
    filter_state = None  # for use with the notch filter

    # Compute the number of epochs in "buffer_length"
    n_win_test = int(np.floor((BUFFER_LENGTH - EPOCH_LENGTH) /
                              SHIFT_LENGTH + 1))

    # Initialize the band power buffer (for plotting)
    # bands will be ordered: [delta, theta, alpha, beta]
    band_buffer = np.zeros((n_win_test, 4)) #9 epochs/5 sec buffer

    #list of buffers for iteration
    buffers = [[eeg_buffer, eeg_buffer, eeg_buffer], [band_buffer, band_buffer, band_buffer]]

    """ 3. GET DATA """

    # The try/except structure allows to quit the while loop by aborting the
    # script with <Ctrl-C>
    print('Press Ctrl-C in the console to break the while loop.')



    try:
        i=0
        Up = False
        # The following loop acquires data, computes band powers, and calculates neurofeedback metrics based on those band powers
        while True:
            i += 1 
            
            for index in range(len(INDEX_CHANNELS)):

                """ 3.1 ACQUIRE DATA """
                # Obtain EEG data from the LSL stream
                eeg_data, timestamp = inlet.pull_chunk(
                    timeout=1, max_samples=int(SHIFT_LENGTH * fs))

                # Only keep the channel we're interested in
                ch_data = np.array(eeg_data)[:, INDEX_CHANNELS[index]]

                # Update EEG buffer with the new data
                buffers[0][index], filter_state = utils.update_buffer(
                    buffers[0][index], ch_data, notch=True,
                    filter_state=filter_state)

                """ 3.2 COMPUTE BAND POWERS """
                # Get newest samples from the buffer
                data_epoch = utils.get_last_data(buffers[0][int(index)],
                                        EPOCH_LENGTH * fs)

                # Compute band powers
                band_powers = utils.compute_PSD(data_epoch, fs)
                buffers[1][index], _ = utils.update_buffer(buffers[1][index], np.asarray([band_powers]))

            print('Delta Left: {}, Delta Right: {}, DL+DR: {}, Alpha Right: {}'.format(str(buffers[1][0][-1][Band.Delta]), str(buffers[1][1][-1][Band.Delta]), 
                                                                                str(buffers[1][1][-1][Band.Delta]+buffers[1][0][-1][Band.Delta]), 
                                                                                str(np.mean(buffers[1][1][:, Band.Alpha]))))


            """ 3.3 COMPARE METRICS """

            if buffers[1][1][-1][Band.Delta]+buffers[1][0][-1][Band.Delta] >= 3.9:
                if Up == True:
                    Up = False
                    playsound.playsound('Vine Boom.mp3', True)
                elif Up == False:
                    Up = True
                    playsound.playsound('Bruh.mp3', True)
                print('switching scroll direction: Up is set to {}'.format(str(Up)))
                buffers[1][1][-1][Band.Delta] = 0
                buffers[1][0][-1][Band.Delta] = 0
               

            elif  buffers[1][1][-2][Band.Delta] > 2.1:
                print("""

                right

                """)
                pyautogui.hotkey('ctrl', 'tab')
                buffers[1][1][-1][Band.Delta] = 0
                buffers[1][0][-1][Band.Delta] = 0

            #  + buffers[1][0][-2][Band.Delta] > 4.4:

            elif buffers[1][0][-2][Band.Delta] > 2:
                print("""

                left

                """)
                pyautogui.hotkey('ctrl', 'shift', 'tab')
                buffers[1][0][-1][Band.Delta] = 0
            
            #Concentration 
            if i > 3:
                if Up == False:
                    if buffers[1][1][-1, Band.Alpha] < 0.6:   
                        print('he do be concentratin')
                        pyautogui.scroll(-200)
                else:
                    if buffers[1][1][-1, Band.Alpha] < 0.6:   
                        print('he do be concentratin')
                        pyautogui.scroll(200)

    except KeyboardInterrupt:
        print('Closing!')
