# SectionViewer  ![image](https://github.com/Fukumasu/SectionViewer/blob/master/sectionviewer/img/icon_32x32.png)

![gif](https://github.com/Fukumasu/SectionViewer/blob/master/sectionviewer/img/SectionViewer.gif)

## Overview

Viewer for 3-dimensional images (.oir, .oib, .tif) on cross sections (multi-planar reconstruction).

## Requirements

- Windows, macOS, or Linux
- python >= 3.6
- Microsoft Visual C++ compiler (for Windows)
- To open .oir files, a java executable is required to be available in your environment. If you are using conda, you can install with 'conda install -c conda-forge scyjava'.

## Installation

You can install SectionViewer with the following simple pip command:
```
pip install git+https://github.com/Fukumasu/SectionViewer
```
If successful, a GUI software will be launched with a shell command 'sectionviewer'.

## Description

In addition to GUI, SectionViewer provides a CUI platform to adjust settings of the software.<br>
For detailed instructions to use CUI, please check [examples.ipynb](https://github.com/Fukumasu/SectionViewer/blob/master/examples.ipynb)<br>

## License

This software is distributed under [MIT license](https://github.com/Fukumasu/SectionViewer/blob/master/LICENSE.md).
