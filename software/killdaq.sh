#!/bin/bash
echo "$(date), running killdaq"
sudo pkill -f dump_baseband
sudo pkill -f dump_spectra\.py
