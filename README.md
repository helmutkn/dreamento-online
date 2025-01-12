# dreamento

This repository contains an implementation of the **dreamento online**, altered from this (https://github.com/dreamento/dreamento) repository.

Before you use this repository I suggest you visit the original one and follow the instructions there.

## changes from the original repository
The TCP socket made problems in that the program was not able to read data from it. Therefore I implemented a raw socket to read the data put there by the HDServer.

## requirements
- python 3.6

all the following steps describe the procedure for the windows operating system. On other os the commands may differ slightly.

## run from scripts
clone the repository

create a virtual env:
  python -m venv /path/to/wherever/you/want/it/to/live/

activate the venv:
  run the activate.bat file from your cmd located at /path/to/venv/Scripts/activate.bat
  
make sure pip is upgraded:
  python -m pip install --upgrade pip

install the requirements from requirements.txt located in the repository:
  python -m pip install -r requirements.txt

run mainwindow.py from your cmd that has the venv activated

## create an executable from scripts
activate the venv:
    run the activate.bat file from your cmd located at /path/to/venv/Scripts/activate.bat

run the command:
  pyinstall mainwindow.py

a directory called dist will be created with a subdirectory called mainwindow. 

copy the 'resources' and 'lspopt' directory from the source code directory into the dist/mainwidnow directory. 

double click the mainwindow.exe to run
  
wait. it may take a minute or 2 for the application to start.
If it starts and closes immediatly run the mainwindow.exe from a cmd and see the output. 

## usage
make sure **HDServer** and **HDRecorder** from hypnodyne are running. 
Without the HDServer the connection wont work, without the HDRecorder the record timer will freeze at 1 second and with it the whole program will!
