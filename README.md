
# Intermediate Filament Tracking (IFTracking)

This software allows you to compute the motion of filamentous structures based on 2D confocal fluorescence microscopy data. It is written in Python, some modules are in C++.

<p float="center" align="center">
  <img src="./docs/example4.gif" width="300" height="300" />
  <img src="./docs/example1.gif" width="480" height="300" /><br/>
  <img src="./docs/example3.gif" width="300" height="300" />
  <img src="./docs/example2.gif" width="480" height="300" />
</p>


## How to run this software


1) Download or clone this repository to any folder on your computer:

```
git clone https://github.com/SCCH-KVS/IFTracking.git
```

2) If you don't have Docker, [install Docker CE](https://www.docker.com/products/docker-engine#/download) for your platform (Windows, Linux or Mac);

3) To run this software execute script `run_docker.sh` (for Linux and Mac) or `run_docker.bat` (for Windows), which you can find in the folder of this repository. The first time you run the script, it automatically pulls the necessary Docker-image from DockerHub to your computer. This image contains Python interpreter and all necessary libraries (no code related to this software).

Alternatively, you can download Docker image `IFTracking-DockerImage.tar` using this [link](https://1drv.ms/u/s!Aoi3MOXlJd9saoSysaObtFTmrH4) and load it manually as follows:
```
docker load --input /path/to/IFTracking-DockerImage.tar
```

However, in this case you should run the program using the script `run_docker_alt.sh` (for Linux and Mac) or `run_docker_alt.bat` (for Windows)

## How to work with this software

### General information

The software consists of the following components:
1. __Image sequence processing__. Performs image enhancement and all processing routines necessary for filament detection and tracking. The results of this step are stored in the folder `output/preprocessing`.
2. __Filament detection (generation)__. Detects filaments (randomized) in the first frame of image sequence. The results are saved to the folder `output/generator`.
3. __Filament tracking__. Tracks and transfers the filaments from the previous step though the whole image sequence. Alternatively, at this step you can specify filaments from other sources. The results are saved to the folder `output/tracking`.
4. __Visualization of the results__. Overlays tracked filaments over the image sequence, also produces the legend and the mask, where each filament is enconded by color (grayscale) corresponding to its number. The results are also saved to the folder `output/tracking`.

When you run the software, you should be able to see the console interface with available operations as shown in the figure below:

<p float="center" align="center">
  <img src="./docs/interface.png" width="700" height="286" />
</p>

The operations (1) to (4) correspond to the respective modules mentioned above. Operation (5) consecutively runs operations from (1) to (4). To run operation, just type its number and hit ENTER. Also, please, take into account that each operation depends on the results of its predecessors. For example, the result of (3) won't be successfull if (1) or (2) were not performed.

Every component has its own configuration file, which is contained in subfolder `config` of the repository root folder. The most important configuration file is `config/common.config`. It contains the path and the name of image sequence to be processed. More information about configuring the software one can find in the respective configuration files.

> **Configure Docker:**
>  1. Before running the software, you should [give access](./docs/docker_1.PNG) to the drive containing the repository folder.
>  2. Also make sure that __Docker__ has [enough resources](docs/docker_2.PNG) to run this software (it depends on the size of image sequence). The software tracks filaments in parallel, therefore the more available for __Docker__ CPUs the faster it works. You can also specify number of CPUs in the configuration file `config/tracker.config`.


### Data formats

1. Input image sequence should be in __TIFF__.
2. The initial coordinates of filaments (on the first frame of the image sequence) are stored in a __ZIP__ archive. The archive contains one __CSV__ file with two columns (__x__ and __y__) per filament.

## How to remove the software

Firstly, remove the folder containing the Git repository. Also remove the respective Docker image using the command:

```
docker rmi -f dkotsur/incem:if-tracking
```
or

```
docker rmi -f if-tracking 
```
if you have uploaded the Docker-image manually.

## Acknowledgements
The research received funding from the European Union's Horizon 2020 research and innovation program under the Marie Sklodowska-Curie grant agreement No. 642866. It was also supported by the Austrian Ministry for Transport, Innovation and Technology, the Federal Ministry of Science, Research and Economy, and the Province of Upper Austria in the frame of the COMET center SCCH.

## License
This software is licensed under the GNU GPL v.3 License - see the [LICENSE](LICENSE) file for details.
