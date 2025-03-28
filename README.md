# SectionViewer  ![image](https://github.com/Fukumasu/SectionViewer/blob/master/sectionviewer/img/icon_32x32.png)

![gif](https://github.com/Fukumasu/SectionViewer/blob/master/sectionviewer/img/SectionViewer.gif)

## Overview

Viewer for 3-dimensional images (.oir, .oib, .tif) on cross sections (multi-planar reconstruction).

## Requirements

- Windows, macOS, or Linux
- python >= 3.6
- Microsoft Visual C++ compiler (for Windows)

## Installation
Installing the software into a conda virtual environment is recommended. Run the following commands in Anaconda Prompt to enter a minimum environment:
```
conda create -n ENVNAME python pip git numpy-base=1
conda activate ENVNAME
```
In your environment, install the software with the following pip command:
```
pip install git+https://github.com/Fukumasu/SectionViewer
```
To use .oir files as image data, add "scyjava" to the environment with the following conda command (optional):
```
conda install -c conda-forge scyjava
```
If successful, the GUI will be launched by entering 'sectionviewer' command in your environment.

## Description

In addition to GUI, SectionViewer provides a CUI platform to adjust settings of the software.<br>
For detailed instructions to use CUI, please check [examples.ipynb](https://github.com/Fukumasu/SectionViewer/blob/master/examples.ipynb)<br>

## License

This software is distributed under [MIT license](https://github.com/Fukumasu/SectionViewer/blob/master/LICENSE.md).
