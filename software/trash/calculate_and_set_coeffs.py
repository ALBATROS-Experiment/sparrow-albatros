"""Calculate and set the digital gain coefficients"""


acc_len = fpga.registers.acc_len.read_uint()
accs=np.array([pols['pol00']/(1<<35), pols['pol11']/(1<<35)])
sigmas = np.sqrt(accs/(2*acc_len))
coeffs=0.125/0.353/sigmas*(1<<17)
coeffs[np.where(coeffs > (1<<32)-1)] = (1<<32)-1
coeffs=np.array(coeffs,dtype="uint32")



