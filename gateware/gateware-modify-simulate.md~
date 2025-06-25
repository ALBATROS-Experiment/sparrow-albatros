
# Modify and Simulate

Once you've got the [toolchain](./installing-the-toolchain.md) up and running on a beefy computer, you'll be ready to modify and simulate the Sparrow Albatros spectrometer design.

## Modify the design

The Sparrow Albatros design is built using Simulink and the CASPER libraries. To modify the design:

1. Launch MATLAB and navigate to your project directory
2. Open the Simulink model file `sparrow_albatros_spec.slx`
3. Make your desired changes to the design
   - Add or modify blocks from the CASPER library
   - Adjust parameters on existing blocks
   - Create new subsystems for complex functionality
   - Connect signals between blocks with appropriate data types

When modifying the design, keep these tips in mind:

- Always maintain synchronization between signal paths
- Check data bit widths at key points in your design
- Consider timing implications when adding complex logic
- Use the CASPER yellow blocks for hardware interfaces
- Add test points at critical junctions to aid in simulation

## Simulate the design

Simulation is a crucial step before synthesis and implementation. It allows you to verify the logical correctness of your design without the time-consuming FPGA build process.

To simulate your design:

1. Configure simulation parameters:
   - Click on the "Simulation" menu in Simulink
   - Select "Model Configuration Parameters"
   - Set appropriate stop time and solver options

2. Add test signals:
   - Use MATLAB Function blocks or From Workspace blocks to generate test vectors
   - Configure step sources or sine wave generators for predictable input patterns
   - Consider using recorded ADC data for realistic testing

3. Add monitoring tools:
   - Place Scope blocks to visualize signals during simulation
   - Use To Workspace blocks to save simulation results for later analysis
   - Add Display blocks to show numerical values at key points

4. Run the simulation:
   - Click the "Run" button in the Simulink toolbar
   - Monitor signals in real-time on Scope blocks
   - Adjust simulation speed as needed

5. Analyze results:
   - Verify that signals behave as expected at each processing stage
   - Check for timing issues, overflows, or unexpected values
   - Use MATLAB scripts to post-process simulation outputs

For example, to simulate the FFT behavior:
- Create test signals with known frequency components
- Run the simulation through the PFB and FFT stages
- Visualize the output to confirm frequency bin mapping
- Verify that the shift schedule prevents overflows

## Synthesize and Implement the design

After successful simulation, proceed to build the FPGA design:

1. Run the CASPER toolflow script with appropriate parameters
2. Monitor the compilation process for warnings and errors
3. Review resource utilization reports

During these stages, the design goes through three transformations:
- Compilation (Simulink model → HDL)
- Synthesis (HDL → logic gates)
- Implementation (logic gates → hardware configuration)

**Open up the synthesized design in Vivado and check timing**

After synthesis, examine the timing reports in Vivado to ensure all timing constraints are met. Pay special attention to:
- Clock domain crossings
- Critical paths
- Setup and hold time violations

For more details on these stages, see [Gateware Compile, Synthesize, and Implement](./gateware-compile-synthesize-implement.md).

