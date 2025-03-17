Images of the sd card, tracked and version controlled with [git-lfs](https://git-lfs.com/). 

To pull the repository without any of the large files tracked here just use git as you usually would. If you want to fetch one of the large files (which you should never do in the sparrow system) install git lfs (e.g. on mac it's `brew install git-lfs`), then figure out which file you want to pull and pull it using the lfs extension, e.g. `git lfs pull --include="path/to/large/image/file.zip"`. 


You can do this in a few short steps:

- Open up you desktop/laptop and clone this repository `git clone https://github.com/ALBATROS-Exp    eriment/sparrow-albatros` 
- Enter the base directory `cd sparrow-albatros`
- Identify the disk-image (.zip file) that you want to pull (e.g. `sparrow-1.4_2023-08-23.zip`).     You can browse the disk-image directory with `ls os-sd-images`
- You're going to need git-lfs to pull large (~1.5G) disk-image files. If you don't have it insta    ll it `sudo apt install git-lfs`
- Replace the fetchexclude line corresponding to the image you want to pull in your `.lfsconfig`     with an include statement, e.g. `fetchinclude = os-sd-images/sparrow-1.4_2023-08-23.zip` 
- Pull that file `git lfs pull "os-sd-images/sparrow-1.4_2023-08-23.zip"`, this will download the     image file 



