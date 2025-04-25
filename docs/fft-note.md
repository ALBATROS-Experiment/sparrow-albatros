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

## FFT Shift Schedule

- What is the shift schedule. Link to how to program it in other document. 
- What is the trade off in terms of resources etc.

## Bit Growth

- takes up more resources but at least doesn't raise the noise floor

## Symmetric Group Buffering

- xyz cite Aaron Parson's symetric group paper and optimization



