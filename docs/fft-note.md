# A Note on CASPER's FFT Implementation

## What is a Fast Fourier Transform (FFT)

The Fast Fourier Transform is an algorithm that implements the Discrete Fourier Transform (DFT). The DFT is a discrete version of the Fourier Transform, which is a linear functional over the complex plane. 

Lets say you want to to find the frequency components of an electric field signal that fluctuates over time. To do this digitally, first you have to sample that electric field at discrete time points. Mathematicaly, that's like multiplying a continuous signal with a Dirac Comb. Take the Fourier Transform of that and apply the convolution theorem, 

$$
F\{x(t) \cdot \text{DiracComb}_{\Delta t} \} = F\{x(t) \} \ast \text{DiracComb}_{1/\Delta t}, 
$$

and the result is the Fourier Transform multiplied by a Dirac Comb with reciprical spacing. If the spacing between samples in the input, $\Delta t$, is very small, then the spacing between output is large. Convolving with a dirac comb will alias frequencies seperated by integer multiples of $1/\Delta t$ together, so to get around that, make sure that your signal $x(t)$ only has frequency information between $-1 \over 2\Delta t$ and $1 \over 2\Delta t$. This region is known as the first Nyquist zone. 

The result is a repeting finite but continuous patch of frequency space. Sample that at $N$ linear-spaced points and you have a Discrete Fourier Transform (DFT). More commonly, the DFT is written as the linear transformation, 

$$
\hat x[k] = \sum_{t=0}^{N-1} e^{-2\pi i kt/N}x[t],
$$

or, in matrix notation, 

$$
\begin{bmatrix}
1 & 1 & 1 & ...& 1\\
1 & e^{-2\pi i \over N} & e^{-4\pi i \over N} & ... & e^{-(N-1)2\pi i \over N} \\
1 & e^{-4\pi i \over N} & e^{-8\pi i \over N} & ... & e^{-(N-1)4\pi i \over N} \\
\vdots & \vdots & \vdots & \ddots & \vdots 
\end{bmatrix}.
$$

This matrix is fully packed and not sparse, so you might assume that it would take $O(N^2)$ multiply operations to execute it on a computer. As it happens, Cooley and Tukey (1963 [citation needed]) figured out a way to do it in $O(N log N)$ multiplications. Their algorithm is known as the Fast Fourier Transform (FFT). Understanding the FFT amounts to understanding a single matrix decomposition called Radix-2 Decomposition. 

## Radix-2 Decomposition

Start with the definition of your DFT, 

$$
\hat x[k] = \sum_{t=0}^{N-1} e^{-2\pi i kt/N}x[t],
$$

and assume, for simplicity, that $N$ is a power of 2. Notice that you can split the sum half way like so, 

$$
\hat x[k] = \sum_{t=0,2,4,...}^{N-2} e^{-2\pi i kt \over N}x[t] + \sum_{t=1,3,5,...}^{N-1} e^{-2\pi i kt \over N}x[t].
$$

Then re-index those two sums and, for the latter sum, pop out a "twiddle" factor, like so, 

$$
\hat x[k] = \sum_{t=0}^{(N/2)-1} e^{-2\pi i kt \over N/2}x[2t] + e^{-2\pi ik/N}\sum_{t=0}^{(N/2)-1} e^{-2\pi i kt \over N/2}x[2t+1].
$$

Notice that we've just turned one DFT into two smaller DFTs. The first thing we did was change 





## Pipelining

- explain how FFTs are usually optimized

## Biplexing

- xyz


## Symmetric Group Buffering

- xyz cite Aaron Parson's symetric group paper and optimization



## FFT Shift Schedule

- What is the shift schedule. Link to how to program it in other document. 
- What is the trade off in terms of resources etc.

The FFT is implemented in log2 N (=12, in our case) "butterfly" stages. At each stage there's a risk of integer overflow. Shifting by one bit (or dividing the signal by two) at some or all stages mitigates that risk at the cost of losing the least significant bit's worth of information. 

To see where the risk of overflow comes from, look at the DFT formula, 

$$
\hat x[k] = \sum_{t=0}^{N-1} x[t] e^{-2pi i kt\over N},
$$

which has the property

$$
\sum_k |\hat x[k]|^2 = N \sum_t |x[t]|^2.
$$

That is to say that the power of the FT is N times the power of the original signal. At each butterfly stage the magnitude of the intermediate signal product grows by the square root of two on expectation, and it grows by a factor of two at most. In the extreme case where the input in sinusoidal and the output is a dirac function, in each butterfly stage, at least one intermediate product will grow by a factor of two in each stage, requiring a full shift schedule to avoid overflow. Human made RFI are typically strong and narrow band in frequency space, that is why we care so much about out-of-band rejection. Regarding the FFT, the narrow-band nature of RFI means we expect some of our frequency bands to grow by a large factor on each butterfly (close to a factor of two) which means, in turn, that our science bands won't have as much room to grow, and may even shrink. 

We have found from experiance in the field that the sky's power spectrum causes FFT overflows if we do not shift aggressively. Until now we have opted to shift aggressively at the expense of raising the noise floor. Every time we shift we lose, on average, half of a least significant bit of range. However, the signals of interest to us are in the quiet channels and are even more sensitive to bit shifting. We may lose up to one bit of resolution with each shift.  



## Bit Growth

Instead of shifting aggressively, we can grow the capacity of each integery by one bit on each butterfly stage, this way we can enjoy the benefits of shifting without worrying about overflow. We compare on-board accumulated spectra with and without bit-growth. 

*Below, spectra from full shift schedule FFT, 18 bits input (12 bits ADC + 6 bits LSB-padding). Input signal is a 61.03515625 kHz square wave. The Fourier Series coefficients of a square wave go like 1/n. Pol1 had a longer cable than Pol0. The longer cable acts like a better antenna, which is why Pol1 is picking up more signal between 50 and 125 MHz.*

![Screenshot from 2025-04-28 14-09-27](https://github.com/user-attachments/assets/508c1d11-d422-4381-b4c8-77f1f34367db)

*Below, same as above but with bit-growth FFT. Starts at 18 btis (12 bits ADC + 6 bits LSB-padding), grows by one bit in first six butterfly stages, then bit shifts on the remaining six stages. The resulting signal is 24 bits deep.*

![Screenshot from 2025-04-28 14-26-50](https://github.com/user-attachments/assets/9156354d-e989-4790-8edc-771f7c1f0028)

*Below, spectra full shift, as above. No signal input from the function generator.*

![Screenshot from 2025-04-28 14-37-49](https://github.com/user-attachments/assets/c4faf5b3-9aee-4393-8e11-390f8ecd4050)

*Below, bit-growth FFT, as above. No signal input from func-gen.*

![Screenshot from 2025-04-28 14-33-05](https://github.com/user-attachments/assets/9a5a274f-2a06-4e04-aae8-8a04ccdfb364)

In summary, the bit growth FFT... 

