- Added one bit logic (including select register for muxing between 4bit and 1bit, as well as one bit reorder logic), have not tested thoroughly yet. 
- Added TVG (test vector generator) downstream of FFT and upstream of requantization. Also not tested. The TVG will be useful for valitating 1bit logic.

Software changes to handle 1bit mode is not included in the commit in which this release-notes file was created. Likely two commits later (one for documenting the release changes here). 
