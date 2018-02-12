const PIN_PX = 8
var platform = {
  "testbed_id": 0,
  "testbed_name": "Sample Platform",
  "testbed_shape": [100, 100], // length 2
  "devices": [
    {
      "device_id": 0,
      "device_name": "Raspberry Pi 3",
      "device_shape": [34, 22],
      "device_pos": [5, 5],
      "device_rotation": 0,
      "pin_headers": [
        {
          "header_name": "GPIO",
          "header_shape": [20, 2],
          "header_pos" :[3, 1],
          "pins": [
            {
              "pin_no": 1,
              "pin_name": "3v3",
              "pin_pos": [0, 1],
              "available": true
            },
            {
              "pin_no": 2,
              "pin_name": "5v",
              "pin_pos": [0, 0],
              "available": true
            },
            {
              "pin_no": 3,
              "pin_name": "BCM2",
              "pin_pos": [1, 1],
              "available": true
            },
            {
              "pin_no": 4,
              "pin_name": "5v",
              "pin_pos": [1, 0],
              "available": true
            },
            {
              "pin_no": 5,
              "pin_name": "BCM3",
              "pin_pos": [2, 1],
              "available": true
            },
            {
              "pin_no": 6,
              "pin_name": "GND",
              "pin_pos": [2, 0],
              "available": true
            },
            {
              "pin_no": 7,
              "pin_name": "BCM4",
              "pin_pos": [3, 1],
              "available": true
            },
            {
              "pin_no": 8,
              "pin_name": "BCM14",
              "pin_pos": [3, 0],
              "available": true
            },
            {
              "pin_no": 9,
              "pin_name": "GND",
              "pin_pos": [4, 1],
              "available": true
            },
            {
              "pin_no": 10,
              "pin_name": "BCM15",
              "pin_pos": [4, 0],
              "available": true
            },
            {
              "pin_no": 11,
              "pin_name": "BCM17",
              "pin_pos": [5, 1],
              "available": true
            },
            {
              "pin_no": 12,
              "pin_name": "BCM18",
              "pin_pos": [5, 0],
              "available": true
            },
            {
              "pin_no": 13,
              "pin_name": "BCM27",
              "pin_pos": [6, 1],
              "available": true
            },
            {
              "pin_no": 14,
              "pin_name": "GND",
              "pin_pos": [6, 0],
              "available": true
            },
            {
              "pin_no": 15,
              "pin_name": "BCM22",
              "pin_pos": [7, 1],
              "available": true
            },
            {
              "pin_no": 16,
              "pin_name": "BCM23",
              "pin_pos": [7, 0],
              "available": true
            },
            {
              "pin_no": 17,
              "pin_name": "3v3",
              "pin_pos": [8, 1],
              "available": true
            },
            {
              "pin_no": 18,
              "pin_name": "BCM24",
              "pin_pos": [8, 0],
              "available": true
            },
            {
              "pin_no": 19,
              "pin_name": "BCM10",
              "pin_pos": [9, 1],
              "available": true
            },
            {
              "pin_no": 20,
              "pin_name": "GND",
              "pin_pos": [9, 0],
              "available": true
            },
            {
              "pin_no": 21,
              "pin_name": "BCM9",
              "pin_pos": [10, 1],
              "available": true
            },
            {
              "pin_no": 22,
              "pin_name": "BCM25",
              "pin_pos": [10, 0],
              "available": true
            },
            {
              "pin_no": 23,
              "pin_name": "BCM11",
              "pin_pos": [11, 1],
              "available": true
            },
            {
              "pin_no": 24,
              "pin_name": "BCM8",
              "pin_pos": [11, 0],
              "available": true
            },
            {
              "pin_no": 25,
              "pin_name": "GND",
              "pin_pos": [12, 1],
              "available": true
            },
            {
              "pin_no": 26,
              "pin_name": "BCM7",
              "pin_pos": [12, 0],
              "available": true
            },
            {
              "pin_no": 27,
              "pin_name": "BCM0",
              "pin_pos": [13, 1],
              "available": true
            },
            {
              "pin_no": 28,
              "pin_name": "BCM1",
              "pin_pos": [13, 0],
              "available": true
            },
            {
              "pin_no": 29,
              "pin_name": "BCM5",
              "pin_pos": [14, 1],
              "available": true
            },
            {
              "pin_no": 30,
              "pin_name": "GND",
              "pin_pos": [14, 0],
              "available": true
            },
            {
              "pin_no": 31,
              "pin_name": "BCM6",
              "pin_pos": [15, 1],
              "available": true
            },
            {
              "pin_no": 32,
              "pin_name": "BCM12",
              "pin_pos": [15, 0],
              "available": true
            },
            {
              "pin_no": 33,
              "pin_name": "BCM13",
              "pin_pos": [16, 1],
              "available": true
            },
            {
              "pin_no": 34,
              "pin_name": "GND",
              "pin_pos": [16, 0],
              "available": true
            },
            {
              "pin_no": 35,
              "pin_name": "BCM19",
              "pin_pos": [17, 1],
              "available": true
            },
            {
              "pin_no": 36,
              "pin_name": "BCM16",
              "pin_pos": [17, 0],
              "available": true
            },
            {
              "pin_no": 37,
              "pin_name": "BCM26",
              "pin_pos": [18, 1],
              "available": true
            },
            {
              "pin_no": 38,
              "pin_name": "BCM20",
              "pin_pos": [18, 0],
              "available": true
            },
            {
              "pin_no": 39,
              "pin_name": "GND",
              "pin_pos": [19, 1],
              "available": true
            },
            {
              "pin_no": 40,
              "pin_name": "BCM21",
              "pin_pos": [19, 0],
              "available": true
            },
          ]
        }
      ]
    }
  ]
}

var tb_shape = platform.testbed_shape;
var root = SVG("autowire")
root.viewbox(0, 0, PIN_PX * tb_shape[0], PIN_PX * tb_shape[1]);
root.rect(PIN_PX * tb_shape[0], PIN_PX * tb_shape[1]).fill("#fff").stroke({ width: 2, color: "black" })

for (var dev_idx in platform.devices) {
  var dev = platform.devices[dev_idx]
  var device = root.nested().move(PIN_PX * dev.device_pos[0], PIN_PX * dev.device_pos[1])
  device.rect(PIN_PX * dev.device_shape[0], PIN_PX * dev.device_shape[1]).fill("#fff").stroke({ width: 1, color: "black"})

  for (var hdr_idx in dev.pin_headers) {
    var hdr = dev.pin_headers[hdr_idx]
    var header = device.nested().move(PIN_PX * hdr.header_pos[0], PIN_PX * hdr.header_pos[1])
      
    for (var pin_idx in hdr.pins) {
      var pin = hdr.pins[pin_idx]
      header.rect(PIN_PX, PIN_PX).fill("#fff").stroke({ width: 1, color: "black"}).move(PIN_PX * pin.pin_pos[0], PIN_PX * pin.pin_pos[1]).mouseover(function() {this.fill("#000")}).mouseout(function() {this.fill("#fff")})
    }
  }
}




