Wiring Description File
===

The WDF is passed through the entire stack to carry wiring and other information. This markdown is written to describe what it carries and why.

### Specification of the System
We want to first consider what fully specifies a grading testbed. A grading testbed is composed by a group of devices, among which pin connections are made. Because of the I/O resource limitation of the FPGA board, we can only make possible wiring a sebset of the total pins. We call these pins "available". Therefore, the system is specified by what devices are present and what pins of them are available. The available pins are physically connected to the pins of the FPGA board. In FPGA design, for each pin we have to specify if it is an input or output. This will prevent us from making a duplexed wire connection such as the I2C SDA. 

> I'm not sure if it's `actually` the case, we need some experiments to test whether this limitation is actually a limitation. Perhaps the FPGA doesn't really care physically the connection direction defined in the Verilog code.

### Front-end's Usage
The front-end needs to present a graphical representation of the devices and the available pins in the testbed to the user. It then amends to the file the user's custom connection. Therefore, the input to the front-end will be the following description of an unwired testbed:

 - Devices available in the testbed
 - Pins available on their respective devices

The output of the front-end is the above and

 - Pin connections with direction

> The front-end itself needs to have the notion of the appearence of the devices, including what pin headers there are on the device in order to draw them. It needs the map the devices described in the WDF to its own notion. This can be done by matching the device names.

### Back-end's Action
With the pin connections specified, the back-end generates a Verilog file describing a module which is a collection of wires. It also generates the helper script for the Quartus tool to map the Verilog pin variable to the actual pin. After that, it builds the generated module to a binary and flashes the binary to the FPGA, and the wiring is thereof done.

### Format of WDF

```
{
	"testbed_id": int,
	"testbed_name": string,
	"devices": [
		{
			device_id: int,
			device_name: string,
			pin_headers: [
				{
					header_name: string,
					header_shape: [int], // length 2
					pins: [
						{
							pin_no: int,
							pin_name: string,
							available: boolean
						}
					]
				}
			]
		}
	],

	// After front end processing:
	"connections": [
		{
			from: {
				device_id: int,
				header_name: string,
				pin_no: int
			},
			to: {
				device_id: int,
				header_name: string,
				pin_no: int
			}
		}
	]
}

```

