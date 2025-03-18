

## Leo Bodnar Setup

*In newdaq readme* 
- Copy `10-local.rules` to `/etc/udev/rules.d/` -- sets the LB permissions
- Then reboot or reinit rules with two commands `sudo udevadm control --reload`, `sudo udevadm trigger`. Then try running a script `check_lb.py` *as superuser*.
