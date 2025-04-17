Bit growth in FFT, first compile *without thorough simulation or hardware testing*. This release note corresponds to both of these binaries (same firmware targeted to two different FPGAs):
- `sparrow_albatros_spec_2025-04-17_2017-xc7z030.fpg`
- `sparrow_albatros_spec_2025-04-17_2115-xc7z035.fpg`

**Imperative Summary**
The (12-stage) FFT bit-grows by 6 bits, which should lower the FFT noise-floor to the minimum given that the polyphase structure adds 6 bits of padding. I chose to get rid of a few bits in the on board correlator so that the fatter outputs could fit comfortably into 64-bit-wide accumulator BRAMs.

Key decisions made: 
- The correlator can accumulate up to 68 seconds but we don't usually correlate more than 6 seconds. This comes at the expense of a few LSBs. We can trade 1 LSB for a doubling in the amount of correlation time.
- We could do a full bit growth to see if that improves anything on what was implemented in this release. If I had infinite time I would test this too. 

**Details**

The data is `Fix_12_11` coming out of the ADCs, the polyphase stage pads it with an additional 6 LSBs to turn it into `Fix_18_17`.

![image](https://github.com/user-attachments/assets/1da39b2e-953c-4e63-86ac-e9026024bd1d)

The FFT is configured to grow each input from 18 to 24 bits.

![image](https://github.com/user-attachments/assets/5bfc2183-2084-4824-bf57-4c2cbfaa001d)

The first six butterfly stages grow the data by 1 bit, 

![image](https://github.com/user-attachments/assets/a1829c58-ea77-4ecb-a32c-6f277f2ba875)

and the shift is ignored, 

![image](https://github.com/user-attachments/assets/72af62fa-cca4-443f-b8c3-fb587b6e85d4)

then next six stages optionally implement an FFT shift (or saturate, but do not grow).

![image](https://github.com/user-attachments/assets/b916e961-3c53-4881-bffe-378b4443aa58)

The FFT now outputs `Fix_24_23` in real/imaginary instead of `Fix_18_17`, so downstream logic needs to be modified to deal with this different data type. 

After the FFT, there's a TVG. In the TVG the only logic that has to change is the bus convert that pads the output of the data bus with zeros and then casts the four 24-bit signals (re/im adc0/adc1) into a `UFix_96_0`.  

![image](https://github.com/user-attachments/assets/7f50d397-6f27-47aa-ac71-9b3a067e37fa)

Downstream of the TVG the signal branches. In one branch we quantize the signal, in the other we correlated the signal. In the 1-bit quantizer we have only to change the bit width and binary point of the complex-to-real reinterprit block as well as the type of the dummy zero value used in all eight comparitors. 

![image](https://github.com/user-attachments/assets/29c3cade-bd74-4ae3-8129-d2f49d632b11)

Similarly, in the 4-bit logic we had only to change the signal types in a few blocks before the comparator logic. 

![image](https://github.com/user-attachments/assets/53161e43-81fd-4343-bf39-675922d16ab9)

Now, in the correlator branch, the bookkeeping gets a little trickier. In overview, complex signals come packaged as `UFix_48_0` (secretly 2x `Fix_24_23`). For the autocorr the abs of the complex numbers is taken and cast into `UFix_42_40`, then accumulated into BRAM as `UFix_64_40`. For the xcorr the complex signals are conjugate-multipled and cast into `Fix_42_39`, then accumulated as `Fix_64_39`.

![image](https://github.com/user-attachments/assets/68f349ee-7a93-4d16-8b2c-456e565b44f0)

In auto-correlation, the magnitude of a complex signal is the sum of the squares of real and imaginary components. First we square `Fix_24_23`s which yield `Fix_48_46`, we must bit-grow by on to include an integer part to make allowance for the (-1)-squared edge-case. The sign bit is superfluous but in this implementation it is got rid of at the add stage. Adding two `Fix_48_46` will ordinarily get you a `Fix_49_46`, but we can get rid of the sign bit because we already know they're both positive, so all we need is `Fix_48_46`. Now we take away six LSBs to give the accumuulator a bit of headroom (about 68 seconds of accumulation time max). Taking away six LSBs is a somewhat arbitrary but (a) it's already better than what we had and (b) it would be annoying to grow the BRAM addresses to make them bigger than 64 bits.  

![image](https://github.com/user-attachments/assets/1d7856d0-58af-4ffe-bdd6-c8104b58eabf)

The cross-correlation stage is a conjugate multiply of two different signals. It also composts two parallel multiplies with an add (twice). In the first multiply stage `Fix_24_23`s are multiplied into `Fix_48_46`s which would ordinarily be summed/substracted to yield `Fix_49_46`. However, we round out *seven* LSBs to get `Fix_42_39`s for real/imagniary components of the output. As with the auto-correlation this gives us 68 seconds to accumulate before overflow becomes logically possible. 

![image](https://github.com/user-attachments/assets/6a531ecd-0243-49f4-a2f7-b70c7073b81d)















