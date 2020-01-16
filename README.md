# NDPA2TIFF
Convert Hamamatsu's or aperio annotation file into an Tiff file

Adapted from NDPA2XML version 0.3, original author G. Thomas Brown

<hr>

## Usage <a class ="anchor" id="user-guide"></a>

1.    [Environment](#1.)  

2.    [Setup](#2.) 

### 1. Environment <a class ="anchor" id="1."></a>

Go to main directory

##### 1.1 Creating environment from .yml file <a class ="anchor" id="1.1"></a>

<code>conda env create -f environment_ndpa2tiff.yml </code>

Creating the environment might take a few minutes. Once finished, issue the following command to activate the environment:

* Windows: <code>activate ndpa2tiff</code>
* macOS and Linux: <code>source activate ndpa2tiff</code>

If the environment was activated successfully, you should see (ndpa2tiff) at the beggining of the command prompt.

OpenSlide and OpenCV are C libraries; as a result, they have to be installed separately from the conda environment, which contains all of the python dependencies.

### 2. Setup <a class ="anchor" id="2."></a>

Create and put NDPA and corresponding NDPI under an input folder.

### 3. Run <a class ="anchor" id="3."></a>
Once in ndpa2tiff environment, run the python script 'ndpa2tiff.py [-i INPUT] [-o OUTPUT]'.
