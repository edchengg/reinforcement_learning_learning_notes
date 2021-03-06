# How To Setup an AWS Instance with Tensorflow and OpenAI Gym
## Caveat and Why This is Needed:
The reason why this is needed is because OpenAI Gym requires a display, which on a headless `aws` server means the `Tensorflow` need to be compiled with a `-no-opengl-files` flag. 

This also means that you can't use pre-built AMI or docker images.

* **Credit**: Most of this guide is sourced from [Wald Post](https://davidsanwald.github.io/2016/11/13/building-tensorflow-with-gpu-support.html)

## Installing Tensorflow with The `-no-opengl-files` Flag

1. Install Ubuntu 16.04 LST on AWS, choose 100GB for the harddrive. Use p2.xlarge.
2. ssh into the system, do
    ```bash
    sudo apt-get update
    sudo apt-get -y dist-upgrade
    # Java stuff for Google Bazel/Blaze.
    sudo apt-get install openjdk-8-jdk git python-dev python3-dev python-numpy python3-numpy build-essential python-pip python3-pip python3-venv swig python3-wheel libcurl3-dev
    # kernel sources and compilers
    sudo apt-get install -y gcc g++ gfortran  git linux-image-generic linux-headers-generic linux-source linux-image-extra-virtual libopenblas-dev
    ```
3. Now install Bazel
    ```bash
    echo "deb [arch=amd64] http://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
    curl https://storage.googleapis.com/bazel-apt/doc/apt-key.pub.gpg | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install bazel
    sudo apt-get upgrade bazel
    ```

4. Now curl or wget the right NVIDIA driver. For the GRID K520 GPU 367.57 should be the right choice.
    ```bash
    wget -P ~/Downloads/ http://us.download.nvidia.com/XFree86/Linux-x86_64/367.57/NVIDIA-Linux-x86_64-367.57.run
    ```
    NVIDIA will clash with the nouveau driver so deactivate it:

    ```bash
    sudo vim /etc/modprobe.d/blacklist-nouveau.conf
    ```
    Insert the following lines and save:
    ```text
    blacklist nouveau
    blacklist lbm-nouveau
    options nouveau modeset=0
    alias nouveau off
    alias lbm-nouveau off
    ```
    
5. Update the initframs (basically functionality to mount your real rootfs, which has been outsourced from the kernel) and reboot:

    ```bash
    sudo update-initramfs -u
    sudo reboot
    ```

    Make the NVIDIA driver runfile executable and install the driver and reboot one more time, just to be sure.

    **IMPORTANT**: In my experience xvfb will only work if you use the `–no-opengl-files` option!

    ```bash
    chmod +x ~/Downloads/Linux-x86_64/367.57/NVIDIA-Linux-x86_64-367.57.run
    sudo sh ~/Linux-x86_64/367.57/NVIDIA-Linux-x86_64-367.57.run --no-opengl-files
    sudo reboot
    ```
    
6. Now wget CUDA 8.0. toolkid from NVIDIA
    ```bash
    wget https://developer.nvidia.com/compute/cuda/8.0/prod/local_installers/cuda_8.0.44_linux-run
    ```

7. **At the same time**, while downloading register at NVIDIA, **download CUDNN 5 runtinme lib** on your local machine and SCP it to the remote instance. **This is going to take a while (10min depends on your upload speed), so go to step 10 afterward.**
    1. First download on Nvidia's website
    2. do:
        ```bash
        scp cudnn-8.0-linux-x64-v5.1.tgz ubuntu@ec2-35-156-52-27.eu-central-1.compute.amazonaws.com:~/Downloads/
        ```
        
8. Now make the runfile executable and install CUDA but don’t install the driver. 
    - **IMPORTANT**: `–-override` option helps to prevent some annoying errors, which could happen.
    - **IMPORTANT**: Be sure to use the `–no-opengl-libs option`

    ```bash
    chmod +x cuda_8.0.44_linux-run
    sudo sh cuda_8.0.44_linux-run --extract=~/Downloads/
    sudo sh cuda_8.0.44_linux-run --override --no-opengl-libs
    ```
    
9. Now open your `.bashrc`
    ```bash
    vim ~/.bashrc
    ```
    and add the following lines:
    ```text
    export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64"
    export CUDA_HOME=/usr/local/cuda
    ```
    
10. If the SCP operation is complete, extract it to the right locations.

    ```bash
    sudo tar -xzvf cudnn-8.0-linux-x64-v5.1.tgz
    sudo cp cuda/include/cudnn.h /usr/local/cuda/include
    sudo cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
    sudo chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*
    ```
11. Reboot one more time:
    ```bash
    chmod +x ~/Downloads/Linux-x86_64/367.57/NVIDIA-Linux-x86_64-367.57.run
    sudo sh ~/Linux-x86_64/367.57/NVIDIA-Linux-x86_64-367.57.run --no-opengl-files
    sudo reboot
    ```
    
12. Now git clone Tensorflow and start the configuration:
    ```bashrc
    git clone https://github.com/tensorflow/tensorflow
    cd ./tensorflow
    ./configure
    ```
    Whey you are running `./configure`, the prompt is gonna ask you a *lot* of questions. Here we use
    - `/usr/bin/python3.5` for the Python binary 
    - `/usr/local/lib/python3.5/dist-packages` for the path,
    - **No** MKL support
    - -march-native
    - jemalloc
    - **No** Google Cloud-support 
    - **No** Hadoop
    - **No** XLA
    - **No** VERBS
    - **No** OpenCL 
    
    - `Cuda SDK 8.01`
    - `cudnn 6.0`
    - **YES** with GPU support
    - Computing capabilities for the p2.xlarge is `3.7`.
    - MPI support Yes
    
    This compile is going to take a long time (30 min for me at least). run below:
    ```bash
    bazel build -c opt --config=cuda //tensorflow/tools/pip_package:build_pip_package
    ```
    Alternative compile script from [SO link](https://stackoverflow.com/questions/41293077/how-to-compile-tensorflow-with-sse4-2-and-avx-instructions)
    ```bash
    bazel build -c opt --copt=-mavx --copt=-mavx2 --copt=-mfma --copt=-mfpmath=both --copt=-msse4.2 --config=cuda -k //tensorflow/tools/pip_package:build_pip_package
    ```

13. Now compile is done! Let's build the pip wheel:
    ```bash
    bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/tensorflow_pkg
    ```
14. This is the easy part: install tensorflow
    ```bash
    python3.5 -m pip install /tmp/tensorflow_pkg/tensorflow-1.2.0-cp35-cp35m-linux_x86_64.whl 
    ```
    
## Install OpenAI Gym:

- Installing OpenAI Gym is pretty straight forward. 
- Sometimes there are some problems with Box2D. If you want to be sure, follow the instructions below.
- We already installed Swig (we need 3.x before compiling Box2D). Git clone Pybox2d

1. build and install `pybox2d`:
    ```bash
    git clone https://github.com/pybox2d/pybox2d.git
    cd pybox2d
    python3 setup.py build
    python3 setup.py install
    ```
2. Install OpenAI Gym
    These instructions are copy pasted from OpenAI Gym github repo:
    ```bash
    git clone https://github.com/openai/gym.git
    sudo apt-get install -y python-numpy python-dev cmake zlib1g-dev libjpeg-dev xvfb libav-tools xorg-dev python-opengl libboost-all-dev libsdl2-dev swig
    cd gym.git
    pip install -e '.[all]'
    ```
    
## Using A Headless Server and VNC into the Display

The gym will need to run with an `xvfb` display. You can connect to this display remotely with an VNC client to monitor the environment.

### The Quick Way to Run:
Just use `xvfb-run` (note X is lower case). Do:
```bash
xvfb-run -a -s "-screen 0 1400x900x24 +extension RANDR" -- python your_training_script.py
```
Note that the screen size is not flexible. I could not get other screen size to work so you have to use this specific size.

### The Right Way:
1. First start a display:
    ```bash
    Xvfb :1 -screen 0 1400x900x24 +extension RANDR &
    ```
    This script starts a display 1, with screen 0. It's id is `:1.0`.
2. Now set the environment variable `DISPLAY`:
    ```bash
    export DISPLAY=:1.0
    ```
3. In the same shell session
    ```bash
    DISPLAY=1:0 python3 -m meta_learning.py # the DISPLAY variable is optional since we already set earlier.
    ```

### Using VNC to Access the Display Remotely:
0. Preparation: 
    1. install `v11vnc`
        ```bash
        sudo apt-get install v11vnc
        ```
    2. setup access password
        ```bash
        x11vnc -storepasswd $(VNC_PASSWORD) /tmp/vncpass
        ```
1. set up a vnc session using `v11vnc`:
    ```bash
    x11vnc -ncache -rfbport $(VNC_PORT) -rfbauth /tmp/vncpass -display :1 -forever -auth /tmp/xvfb.auth
    ```
2. Now on your local machine: 
    1. setup a ssh tunnel
        ```bash
        ssh -L $(VNC_PORT):localhost:$(VNC_PORT) ubuntu@$(IP_ADDRESS) -i ~/.ec2/escherpad.pem
        ```
    2. connect locally
        ```bash
        x11vnc -safer -localhost -nopw -once -display :1.0
        ```
    Alternatively, you could try to connect directly.
    
