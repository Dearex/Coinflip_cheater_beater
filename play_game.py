import math

import os
import pandas as pd
import tabulate
import pyautogui
from _python_modules.log.log import log # my log module! see https://github.com/Dearex/log
from PIL import Image, ImageEnhance, ImageGrab, ImageOps
from pytesseract import Output, pytesseract

win = 15
loss = 30

# positions = {
#     "Normal": (540, 930),
#     "Cheater": (760, 930),
#     "More Data": (540, 830),
#     "Heads_Tails_Start": (600, 500),
#     "Heads_Tails_End": (740, 560)
# }

positions = {
    "Normal": (450, 820),
    "Cheater": (830, 820),
    "More Data": (450, 660),
    "Heads_Tails_Start": (590, 120),
    "Heads_Tails_End": (780, 200)
}
# Calculate the probability of x heads in n coin flips with a given probability of each coin
def prob(x, n, p):
    q = 1 - p
    return math.factorial(n) / (math.factorial(x) * math.factorial(n - x)) * p ** x * q ** (n - x)

def print_probs(heads, flips):
    normal_prob = prob(heads, flips, 0.5)
    cheater_prob = prob(heads, flips, 0.75)
    cheater_confidence = (loss + flips) / win
    normal_conficence = (win) / (loss + flips*2)
    ratio = cheater_prob / normal_prob
    log.info(f'Normal: {normal_prob:.2f}')
    log.info(f'Cheater: {cheater_prob:.2f}')
    log.info(f'Normal Confidence: {normal_conficence:.2f}')
    log.info(f'Cheater Confidence: {cheater_confidence:.2f}')
    log.info(f'Ratio: {ratio:.2f}')
    if flips >= 14:
        log.warning("To many flips! Taking more probable result!")
        if normal_prob > cheater_prob:
            return "Normal"
        else:
            return "Cheater"
    if ratio > cheater_confidence:
        log.info("Cheater detected!", "-")
        return "Cheater"
    elif ratio < normal_conficence:
        log.info("Normal detected!", "+")
        return "Normal"
    else:
        log.info("More Data needed!", "=")
        return "More Data"

def output_text(image):

    path_to_tesseract = r"F:\Programme\Python\pytesseract\tesseract.exe"
    pytesseract.tesseract_cmd = path_to_tesseract

    custom_config = r'-c preserve_interword_spaces=1 --oem 1 --psm 6 -l eng'
    d = pytesseract.image_to_data(image, config=custom_config, output_type=Output.DICT)
    df = pd.DataFrame(d)

    # clean up blanks
    df1 = df[(df.conf!='-1')&(df.text!=' ')&(df.text!='')]
    # sort blocks vertically
    sorted_blocks = df1.groupby('block_num').first().sort_values('top').index.tolist()
    for block in sorted_blocks:
        curr = df1[df1['block_num']==block]
        sel = curr[curr.text.str.len()>3]
        char_w = (sel.width/sel.text.str.len()).mean()
        prev_par, prev_line, prev_left = 0, 0, 0
        text = ''
        for ix, ln in curr.iterrows():
            # add new line when necessary
            if prev_par != ln['par_num']:
                text += '\n'
                prev_par = ln['par_num']
                prev_line = ln['line_num']
                prev_left = 0
            elif prev_line != ln['line_num']:
                text += '\n'
                prev_line = ln['line_num']
                prev_left = 0

            added = 0  # num of spaces that should be added
            if ln['left']/char_w > prev_left + 1:
                added = int((ln['left'])/char_w) - prev_left
                text += ' ' * added 
            text += ln['text'] + ' '
            prev_left += len(ln['text']) + added + 1
        text += '\n'
        return text

def do_it(detect:bool = True, heads:int = 0, tails:int = 0):
    if detect:
        image = ImageGrab.grab(bbox=(positions["Heads_Tails_Start"][0], positions["Heads_Tails_Start"][1], positions["Heads_Tails_End"][0], positions["Heads_Tails_End"][1]))
        state = output_text(image)
        if state:
            try:
                state = state.replace(" ", "").split('\n')
                # remove empty strings from list
                state = list(filter(None, state))
                heads = int(state[0][state[0].find(":") + 1:])
                tails = int(state[1][state[1].find(":") + 1:])

                os.system('cls' if os.name == 'nt' else 'clear')
                print(f'{heads} heads, {tails} tails')
                result = print_probs(heads, heads + tails)
                return result
            except:
                print("Couldn't read the state")
                return "Wrong Data"
        else:
            print("No data found!")
            return "More Data"
    else:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f'{heads} heads, {tails} tails')
        result = print_probs(heads, heads + tails)
        return result
import time

auto_mode = True
manual = False

pause = 1


while not manual:
    mouse_pos = pyautogui.position()
    
    result = do_it()
    if result == "More Data" and auto_mode:
        pyautogui.click(*positions["More Data"])
    elif result == "Cheater" and auto_mode:
        pyautogui.click(*positions["Cheater"])
        time.sleep(4)
        log.info("New Blob...")
        pyautogui.click(*positions["More Data"])
    elif result == "Normal" and auto_mode:
        pyautogui.click(*positions["Normal"])
        time.sleep(4)
        log.info("New Blob...")
        pyautogui.click(*positions["More Data"])
    
    pyautogui.moveTo(mouse_pos[0], mouse_pos[1])

    if result == "Wrong Data":
        time.sleep(min(5, max(pause*10, 2)))
    elif auto_mode:
        time.sleep(pause)
    else:
        time.sleep(pause*2.5)
    # input("Press Enter to continue...")

# if manual:
#     do_it(False, 7,3)
