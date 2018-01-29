AutoWire Front-end
===
### Technology Overview
The front-end needs to be pluggable to the existing interface. Therefore, the most appropriate way to do it is to put the interface in a `<div>`. An HTML class name will link the div to the programmatic part of the module. With this class name, we use jQuery to draw the interface on the document's load event. The interface is built hierachically, presenting a whitebox in which the devices are drawn. Each device is a rectangle with pin headers drawn inside. The dimension of a pin header is specified in the WDF. 

> TODO: We could also put the device size and location of header in the WDF to fully specify a device.

The interface is drawn with an SVG library, SVG.js, which is one of the few candidates under active maintainence. SVG libraries are useful for drawing the rectangular devices and headers. The arrows representing connections are drawn using SVG. Other effects can be handled in CSS, such as the color change of a header pin to indicate it is activated to be dragged to another pin to make a connection.

The module follows a simple MVC design pattern. The views are the devices, headers and the pins. There controllers are objects to handle mouse events and record connections. The connection is recorded in a JS object and finally got translated into the amendment of the WDF.

> Note: the AutoGrader Web Application should pass the unwired WDF to this module.

