#
# NDPA2TIFF : convert Hamamatsu's annotation file into an Tiff file
# Adapted from NDPA2XML version 0.3, original author G. Thomas Brown

__version__ = 0.4
__author__ = 'Carl Cornwell'
__author__ = 'G. Thomas Brown'
__author__ = 'Tianyi Miao'

import openslide as osl
import xml.etree.ElementTree as ET
import numpy as np
import cv2
import os
import argparse
import warnings
from albumentations import Resize

# NDPI_PATH = 'input/PARPEI-OBMIHX_C-Q70.svs'
# NDPA_PATH = 'input/PARPEI-OBMIHX_C-Q70.svs.ndpa'
# TIFF_PATH = 'result/PARPEI-OBMIHX_C-Q70-NoOffset.tiff'

class hamamatsuNdpa2coor:
    def __init__(self, x_off, y_off, x_mpp, y_mpp, dimX0, dimY0):
       	self.x_off = x_off
       	self.y_off = y_off
       	self.x_mpp = x_mpp
       	self.y_mpp = y_mpp
        self.dimX0 = dimX0
        self.dimY0 = dimY0
    def convert(self, x, y):
        x -= int(self.x_off)    # relative to the center of the image
        y -= int(self.y_off)

        x /= (1000*self.x_mpp)  # in pixels, relative to the center
        y /= (1000*self.y_mpp)

        x = x + self.dimX0 / 2  # in pixels, relative to UL corner
        y = y + self.dimY0 / 2

        return int(x), int(y)

class aperioNdpa2coor:
    def __init__(self, x_off, y_off, x_mpp, y_mpp, dimX0, dimY0):
       	self.x_off = x_off
       	self.y_off = y_off
       	self.x_mpp = x_mpp
       	self.y_mpp = y_mpp
        self.dimX0 = dimX0
        self.dimY0 = dimY0
    def convert(self, x, y):

        # Should not use LineAreaXOffset
        # x -= 1000000*float(self.x_off) # Until we find defination of LineAreaXOffset
        # y -= 1000000*float(self.y_off)

        x /= (1000*self.x_mpp)  # in pixels, relative to the center
        y /= (1000*self.y_mpp)

        return int(x), int(y)
def main(FILE_PATH, NDPA_PATH, TIFF_PATH, TIFF_PATH_10X, format):

    xml_file = ET.parse(NDPA_PATH)

    xml_root = xml_file.getroot()

    _osl = osl.OpenSlide(FILE_PATH)

    if format == 'aperio':
        # print(_osl.properties)
        x_off = _osl.properties['aperio.LineAreaXOffset']
        y_off = _osl.properties['aperio.LineAreaYOffset']
        x_mpp = float(_osl.properties['openslide.mpp-x'])
        y_mpp = float(_osl.properties['openslide.mpp-y'])
        dimX0, dimY0 = _osl.level_dimensions[0]
        # print("x_off =", x_off, "   y_off =", y_off)
        # print("x_mpp =", x_mpp, "   x_mpp =", y_mpp)
        # print("dimX0 =", dimX0, "   dimY0 =", dimY0)

        coor = aperioNdpa2coor(x_off, y_off, x_mpp, y_mpp, dimX0, dimY0)
    elif format == 'hamamatsu':
        x_off = _osl.properties['hamamatsu.XOffsetFromSlideCentre']
        y_off = _osl.properties['hamamatsu.YOffsetFromSlideCentre']
        x_mpp = float(_osl.properties['openslide.mpp-x'])
        y_mpp = float(_osl.properties['openslide.mpp-y'])
        dimX0, dimY0 = _osl.level_dimensions[0]
        coor = hamamatsuNdpa2coor(x_off, y_off, x_mpp, y_mpp, dimX0, dimY0)
    print('[INFO] Creating 40x....')
    mat = np.zeros((dimY0, dimX0), dtype='uint8')
    for ann in list(xml_root):
        points = []
        p = ann.find('annotation')
        if p is None:
            continue

        ntype = p.get('type')
        if ntype == 'freehand':
            st = p.find('specialtype')
            if st is None:
                rtype = 0
            else:
                st = st.text
                if st == 'rectangle':
                    rtype = 1
                else:
                    rtype = 0
        elif ntype == 'circle':
           rtype = 2
        elif ntype == 'pointer':
              rtype = 3
        else:
           rtype = 0

        if (rtype == 2):
            x1 = int(p.find('x').text)
            y1 = int(p.find('y').text)
            x, y = coor.convert(x1, y1)
            points.append((x, y))

            r = int(p.find('radius').text)
            x = x1 + 2*r
            y = y1 + 2*r
            x, y = coor.convert(x, y)
            points.append((x, y))
        elif (rtype == 3): # POINTER
            x = int(p.find('x1').text)
            y = int(p.find('y1').text)
            x, y = coor.convert(x, y)
            points.append((x, y))

            x = int(p.find('x2').text)
            y = int(p.find('y2').text)
            coor.convert(x, y)
            points.append((x, y))
        else: # FREEHAND (curve or rectangle)
            pl = p.find('pointlist')
            if pl is None:
                continue

            for pts in list(pl):
                # convert the coordinates:
                x = int(pts.find('x').text)
                y = int(pts.find('y').text)
                x, y = coor.convert(x, y)
                points.append((x, y))

        cnt = np.array(points).reshape((-1, 1, 2)).astype(np.int32)
        if ann.find('title').text is None:
            cv2.fillPoly(mat, [cnt], 255)
        elif ann.find('title').text == 'ARMS':
            cv2.fillPoly(mat, [cnt], 250)
        elif ann.find('title').text == 'ERMS':
            cv2.fillPoly(mat, [cnt], 200)
        elif ann.find('title').text == 'STROMA':
            cv2.fillPoly(mat, [cnt], 150)
        elif ann.find('title').text == 'NECROSIS':
            cv2.fillPoly(mat, [cnt], 100)
    cv2.imwrite(TIFF_PATH, mat[:,:])
    print('[INFO] Creating 10x....')

    org_height = mat.shape[0]
    org_width = mat.shape[1]


    res_height = org_height//4
    res_width = org_width//4

    aug_inf = Resize(p=1.0, height = res_height, width = res_width)
    augmented_inf = aug_inf(image= mat, mask= mat)
    resized = augmented_inf['mask']
    cv2.imwrite(TIFF_PATH_10X, resized)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""
            Convert NDPA annotation to tiff.
            """)
    parser.add_argument('-i', '--input', action='store', help='input directory of NDPA/NDPI', default=None, required=True)
    parser.add_argument('-o', '--output', action='store', help='output directory of the result tiff file', default=None, required=True)
    args = parser.parse_args()
    ndpafiles = [fileName for fileName in os.listdir(args.input) if fileName.endswith(".ndpa") ]
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    for ndpafilename in ndpafiles:
        basename = os.path.splitext(ndpafilename)
        if not os.path.exists(os.path.join(args.input, basename[0])):
            warnings.warn('%s does not has ndpi' % ndpafilename)
            continue
        print('%s is been processing.' % ndpafilename)
        if basename[0].endswith(".ndpi"):
            filename = basename[0]
            tifffilename = basename[0].replace(".ndpi", ".tiff")
            tifffilename_10x = basename[0].replace(".ndpi", "_10x.tiff")
            format = 'hamamatsu'
        elif basename[0].endswith(".svs"):
            filename = basename[0]
            tifffilename = basename[0].replace(".svs", ".tiff")
            tifffilename_10x = basename[0].replace(".svs", "_10x.tiff")
            format = 'aperio'
        FILE_PATH = os.path.join(args.input, filename)
        NDPA_PATH = os.path.join(args.input, ndpafilename)
        TIFF_PATH = os.path.join(args.output, tifffilename)
        TIFF_PATH_10X = os.path.join(args.output, tifffilename_10x)
        main(FILE_PATH, NDPA_PATH, TIFF_PATH, TIFF_PATH_10X, format)

