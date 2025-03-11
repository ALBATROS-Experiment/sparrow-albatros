- Added one bit logic (including select register for muxing between 4bit and 1bit, as well as one bit reorder logic), have not tested thoroughly yet. 
- Added TVG (test vector generator) downstream of FFT and upstream of requantization. Also not tested. The TVG will be useful for valitating 1bit logic.

### 1bit Logic
High level overview of re-quantization logic.
![requantization-high-level](https://github.com/user-attachments/assets/25808eb5-9a92-4913-b427-3a95dde2d12b)

1bit requantization logic. It's just a bunch of comparators and then a flip flop for when the value is exactly zero (probably overkill but this ensures unbiased data).
![requantization-1bit-logic](https://github.com/user-attachments/assets/80285c92-6174-4514-830a-74d14fc52fac)

1bit reorder logic.  
![requantization-1bit-reorder](https://github.com/user-attachments/assets/f23ffc5f-83a4-4f7b-94d3-dba5f43a79d8)

1bit reorder bram--that stores the output ordered channel indices--block parameter.
![requantization-1bit-reorder-bram-block-parameters](https://github.com/user-attachments/assets/e924d204-2360-48c9-b82a-7ac11c437e04)

1bit reorder double buffer
![requantization-1bit-reorder-double-buffer](https://github.com/user-attachments/assets/8306b5c5-fcf1-424c-a49f-f487c7d8d8ca)

Square transposer
![requantization-1bit-square-transposer](https://github.com/user-attachments/assets/526ebbf1-f81b-4c98-b531-8479cb574ed9)

Barrel switcher
![requantization-1bit-reorder-barrel-switcher](https://github.com/user-attachments/assets/23953589-b67e-4635-8223-75d79a3f7a6b)

### TVG
High level overview of where the new TVG sits in the logic, immediately after the PFB's FFT
![tvg-after-fft](https://github.com/user-attachments/assets/effef1e7-c90b-4b59-9580-b602399315dc)

What the TVG logic actually looks like
![tvg-logic](https://github.com/user-attachments/assets/ae1ed829-1161-4ba5-bfd2-405a29a371ce)

The TVG's BRAM mask parameters
![tvg-bram-block-parameters](https://github.com/user-attachments/assets/d073cbe3-5d6a-4eb0-a39e-ee5af620c68a)


Software changes to handle 1bit mode is not included in the commit in which this release-notes file was created. Likely two commits later (one for documenting the release changes here). 

