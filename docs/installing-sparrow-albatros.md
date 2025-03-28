We're running Ubuntu 18.04.6 LTS (Bionic Beaver) on the Sparrow's ARM processor. 

## Quick start

You have all the hardware for a Sparrow-Albatros data acquisition system and you want to get the software up and running for data collection. Easy, just download the latest image from [os-sd-images directory](https://github.com/ALBATROS-Experiment/sparrow-albatros/tree/main/os-sd-images), unzip it, and write it onto a fresh SD card. 

:warning: To save time writing the image we shrink the main filesystem partition. If the image hasn't automatically resized, make sure to resize the partition so that it takes up the full disk space. To do this:
- Insert the SD card into a linux machine or computer, if using an SD card sleeve, make sure it is in writable mode (physical slot switched upwards, towards metal)
- If it auto-mounts, *unmount it*
- Open gparted *as superuser* `sudo gparted`
- Select the volume corresponding to the SD card
- Resize the filesystem partition "rootfs" so that it fills the remaining disk space (right-click, resize, drag and drop, click green tick box *apply all operations*) 

Stick the card into the Sparrow board's microSD card slot and you're good to go! 

