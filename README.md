# 
<p align="center">
  <img src="docs/images/BETSI-logo.jpeg" alt="A2ML" style="padding:10px;" width="700"/>
</p>  

<h3 align="center">

[![Build Status](https://travis-ci.com/nakulrampal/betsi-gui.svg?token=Z8uG4PAMYmS7Xn1zqF5i&branch=master)](https://travis-ci.com/nakulrampal/betsi-gui)
[![Documentation Status](https://readthedocs.org/projects/aamplify/badge/?version=latest)](https://aamplify.readthedocs.io/en/latest/?badge=latest) 
[![Gitter](https://badges.gitter.im/betsi-gui/community.svg)](https://gitter.im/betsi-gui/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)  [![Commit Activity](https://img.shields.io/github/commit-activity/m/nakulrampal/betsi-gui)](https://github.com/nakulrampal/betsi-gui/pulse)  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/nakulrampal/github-gui/LICENSE.txt)

</h3>

<p align="center">
  <img src="docs/images/executables-banner.PNG" alt="banner" style="padding:2px;" width="550"/>
</p>

## Software Requirements:

### OS Requirements
This package is supported for *windows*, *macOS* and *Linux*. The package has been tested on the following systems:
+ Windows: 10 (10.0.19041)
+ macOS: Mojave (10.14.1)
+ Linux: Ubuntu 16.04

### Python Dependencies

`betsi-gui` mainly depends on the Python scientific stack.

```
numpy==1.19.3
scipy==1.5.4
matplotlib==3.2.2
PyQt5==5.9.2
pandas==1.1.5
seaborn==0.11.0
statsmodels==0.12.1
```
## Running BETSI from an executable

Download the executables for *Windows* or *Linux* found in the repositories run them on your machine. This will automatically run the code for you and take you immediately to the [Instructions of use](#instructions-of-use) found below. If instead you wish to download the source code and install BETSI on your machine, please follow the steps below.

## Steps to install BETSI

*Estimated installation time*: ***10 minutes***

Download Anaconda from https://anaconda.org for your operating system. Once you have done so, open the Anaconda Navigator program.

# <img src="docs/images/step-1.png" alt="step-1" style="padding:10px;" width="600"/>

Next, create a new environment by clicking ```Create``` on the bottom left corner. You can give your environment and arbitrary name (we have called ours ```betsi```) and select as a package ```Python 3.7```.

# <img src="docs/images/step-2.png" alt="step-2" style="padding:10px;" width="600"/>

If you have successfully created a new environment, it should appear under the base environment. Next, click the :arrow_forward: button in the newly created environment and select ```Open Terminal```

# <img src="docs/images/step-4.png" alt="step-4" style="padding:10px;" width="600"/>

This will prompt a command terminal in the new environment.

# <img src="docs/images/step-5.png" alt="step-5" style="padding:10px;" width="600"/>

### :star: Option 1: via ```pypi```

Next, type in the command: ```pip install -i https://test.pypi.org/simple/ betsi-gui```

<img src="docs/images/step-6.png" alt="step-6" style="padding:10px;" width="600"/>

### :point_right: Option 2: using the source code

Navigate to the location where you have stored the source code and enter the directory ```betsi-gui```. Once in the directory, run the command ```python setup.py install```, followed by the command ```pip install .```

To read more about using the command line please visit: [windows](https://www.computerhope.com/issues/chusedos.htm), [linux](https://ubuntu.com/tutorials/command-line-for-beginners#1-overview), [macOS](https://blog.teamtreehouse.com/introduction-to-the-mac-os-x-command-line).

#
:heavy_check_mark: This will install BETSI in the newly created environment and download all the relevant python packages from our test server.

## Instructions of use

*Estimated run time*: ***5 minutes***

Next, to run BETSI, type in the command: ```python -m betsi```

# <img src="docs/images/step-7.png" alt="step-7" style="padding:10px;" width="600"/>

Run the command, which will prompt the BETSI GUI. This step may take some time. The BETSI GUI will appear with its default settings as laid out in the Rouquerol criteria. Run an isotherm in the GUI by dragging a correct ```.csv``` file into the empty space on the right. Test isotherms can be found in the repository. Note that isotherms will only run successfully in BETSI if they are in the same format as the exemplary isotherms, further information can be found in section [Test Dataset](#test-dataset) below.

# <img src="docs/images/step-9.png" alt="step-9" style="padding:10px;" width="600"/>

The code will run automatically and two windows appear. For a full explanation of all figures, please refer to the Supplementary Information of the manuscript, Section S5. 

# <img src="docs/images/step-10.png" alt="step-10" style="padding:10px;" width="600"/>

Further, you can interact with the GUI by manually selecting other Rouquerol-permitted BET areas. In the ```Filtered BET areas``` plot, click on one of the other points. All plots will automatically update to the new selected linear region/BET area. The ```active``` plot is always shown in yellow.

# <img src="docs/images/step-11.png" alt="step-11" style="padding:10px;" width="600"/>

To output BETSI data, select an output directory and click ```Export Results``` in the GUI.

# <img src="docs/images/step-12.png" alt="step-12" style="padding:10px;" width="300"/>

The specified directory will contain ```.pdf``` prints of the two active plots (BETSI analysis and regression diagnostics), a ```.json``` file specifying the filter criteria, a ```.txt``` file featuring a small summary, and a folder containing all matrices that the program uses.

# <img src="docs/images/step-14.png" alt="step-14" style="padding:10px;" width="600"/>

Analyse a new isotherm in BETSI by clearing the current plot either via ```Tools-> Clear```, or by pressing the hotkey combination ```CMD/CTRL+C```.

# <img src="docs/images/step-13.png" alt="step-13" style="padding:10px;" width="300"/>

Analyse all isotherms in BETSI by pressing the hotkey combination ```CMD/CTRL+D```. Note that the same parameters defined on the main panel will be used for all calculations. The results can be found in the output directory and the plots are not displayed to avoid overloading the screen.

# <img src="docs/images/step-15.png" alt="step-13" style="padding:10px;" width="400"/>



## Test Dataset

A test dataset of isotherms is supplied on this repository. To run the isotherms in BETSI, download the dataset and drag isotherms into the BETSI GUI as described above. If you would like to try BETSI with your own dataset, you will need to convert it first into the same format as the test isotherms: It must be a 2-column ```.csv``` file with the relative pressure in the first column and the adsorbed quantity in the second. The first row will not be read as this usually contains the header. You must use an adsorption isotherm only, a desorption swing, or discontinuity in the adsorption from pressure equilibration issues will result in an error, with the PChip interpolation method.

## License

BETSI is distributed under the MIT open source license (see [`LICENSE.txt`](LICENSE.txt)).

## Acknowledgements

Main Developers: James Rampersad, Johannes W. M. Osterrieth, and Nakul Rampal

This work is supported by:
* [Cambridge International Scholarship](https://www.cambridgetrust.org/) funded by the Cambridge Commonwealth, European & International Trust;
* [Trinity-Henry Barlow Scholarship](https://www.trin.cam.ac.uk/) (Honorary) funded by Trinity College, Cambridge.

<img src="docs/images/a2ml_logo.png" alt="A2ML" style="padding:10px;" width="150"/>