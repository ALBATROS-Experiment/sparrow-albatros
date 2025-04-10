#!/bin/bash
echo "$(date), running killdaq"
sudo pkill -f dump_baseband
sudo kill -2 $(pgrep -f "dump_spectra\.py")
