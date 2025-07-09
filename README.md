# SectionViewer  ![image](https://github.com/Fukumasu/SectionViewer/blob/master/sectionviewer/img/icon_32x32.png)

![gif](https://github.com/Fukumasu/SectionViewer/blob/master/sectionviewer/img/SectionViewer.gif)

## Overview

Viewer for 3-dimensional images (.oir, .oib, .tif) on cross sections (multi-planar reconstruction).

## Requirements

- Windows, macOS, or Linux
- python >= 3.6
- Microsoft Visual C++ compiler (for Windows)

## Installation
It is recommended to install the software in a conda virtual environment. 
1. Run the following command in Anaconda Prompt to create a minimum environment:
```
conda create -n ENVNAME python pip git numpy=1
```
2. Activate the new environment:
```
conda activate ENVNAME
```
3. Install the software with the following pip command:
```
pip install git+https://github.com/Fukumasu/SectionViewer
```
4. To use .oir files as image data, add "scyjava" to the environment with the following conda command (optional):
```
conda install -c conda-forge scyjava
```
If successful, the GUI will be launched by entering 'sectionviewer' command.

## Description

In addition to GUI, SectionViewer provides a CUI platform to adjust settings of the software.<br>
For detailed instructions to use CUI, please check [examples.ipynb](https://github.com/Fukumasu/SectionViewer/blob/master/examples.ipynb)<br>

## License

This software is distributed under [MIT license](https://github.com/Fukumasu/SectionViewer/blob/master/LICENSE.md).
