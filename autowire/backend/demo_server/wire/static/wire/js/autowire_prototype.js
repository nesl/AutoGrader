'use strict'

// Scale factor: the width and length of a single pin box
const PIN_PX = 8

// The cursor position is offsetted by -8; we don't know why
const CURSOR_OFFSET = -8

// The giant data dictionary
var platform = {
  "testbed_id": 0,
  "testbed_name": "Sample Platform",
  "testbed_shape": [100, 100], // length 2
  "devices": [
    {
      "device_id": 2,
      "device_name": "Arduino UNO R3",
      "device_shape": [26, 18],
      "device_pos": [50, 5],
      "device_rotation": 1,
      "pin_headers": [
        {
          "header_name": "DIGITAL (PWM~) (Left)",
          "header_shape": [10, 1],
          "header_pos": [5, 1],
          "pins": [
            {
              "pin_no": 1,
              "pin_name": "D8",
              "pin_pos": [9, 0],
              "available": true
            },
            {
              "pin_no": 2,
              "pin_name": "D9~",
              "pin_pos": [8, 0],
              "available": true
            },
            {
              "pin_no": 3,
              "pin_name": "D10~",
              "pin_pos": [7, 0],
              "available": true
            },
            {
              "pin_no": 4,
              "pin_name": "D11~",
              "pin_pos": [6, 0],
              "available": true
            },
            {
              "pin_no": 5,
              "pin_name": "D12",
              "pin_pos": [5, 0],
              "available": true
            },
            {
              "pin_no": 6,
              "pin_name": "D13",
              "pin_pos": [4, 0],
              "available": true
            },
            {
              "pin_no": 7,
              "pin_name": "GND",
              "pin_pos": [3, 0],
              "available": true
            },
            {
              "pin_no": 8,
              "pin_name": "AREF",
              "pin_pos": [2, 0],
              "available": true
            },
            {
              "pin_no": 9,
              "pin_name": "Not Labelled",
              "pin_pos": [1, 0],
              "available": false
            },
            {
              "pin_no": 10,
              "pin_name": "Not Labelled",
              "pin_pos": [0, 0],
              "available": false
            }
          ]
        },
        {
          "header_name": "DIGITAL (PWM~) (Right)",
          "header_shape": [8, 1],
          "header_pos": [16, 1],
          "pins": [
            {
              "pin_no": 1,
              "pin_name": "D0",
              "pin_pos": [7, 0],
              "available": true
            },
            {
              "pin_no": 2,
              "pin_name": "D1",
              "pin_pos": [6, 0],
              "available": true
            },
            {
              "pin_no": 3,
              "pin_name": "D2",
              "pin_pos": [5, 0],
              "available": true
            },
            {
              "pin_no": 4,
              "pin_name": "D3~",
              "pin_pos": [4, 0],
              "available": true
            },
            {
              "pin_no": 5,
              "pin_name": "D4",
              "pin_pos": [3, 0],
              "available": true
            },
            {
              "pin_no": 6,
              "pin_name": "D5~",
              "pin_pos": [2, 0],
              "available": true
            },
            {
              "pin_no": 7,
              "pin_name": "D6~",
              "pin_pos": [1, 0],
              "available": true
            },
            {
              "pin_no": 8,
              "pin_name": "D7",
              "pin_pos": [0, 0],
              "available": true
            }
          ]
        },
        {
          "header_name": "TCSP",
          "header_shape": [2, 3],
          "header_pos": [23, 7],
          "pins": [
            {
              "pin_no": 1,
              "pin_name": "PIN18",
              "pin_pos": [0, 0],
              "available": true
            },
            {
              "pin_no": 2,
              "pin_name": "5V",
              "pin_pos": [1, 0],
              "available": true
            },
            {
              "pin_no": 3,
              "pin_name": "PIN19",
              "pin_pos": [0, 1],
              "available": true
            },
            {
              "pin_no": 4,
              "pin_name": "PIN17~",
              "pin_pos": [1, 1],
              "available": true
            },
            {
              "pin_no": 5,
              "pin_name": "RESET",
              "pin_pos": [0, 2],
              "available": true
            },
            {
              "pin_no": 6,
              "pin_name": "GND",
              "pin_pos": [1, 2],
              "available": true
            },
          ]
        },
        {
          "header_name": "POWER",
          "header_shape": [8, 1],
          "header_pos": [9, 16],
          "pins": [
            {
              "pin_no": 1,
              "pin_name": "Vin",
              "pin_pos": [7, 0],
              "available": true
            },
            {
              "pin_no": 2,
              "pin_name": "GND",
              "pin_pos": [6, 0],
              "available": true
            },
            {
              "pin_no": 3,
              "pin_name": "GND",
              "pin_pos": [5, 0],
              "available": true
            },
            {
              "pin_no": 4,
              "pin_name": "5V",
              "pin_pos": [4, 0],
              "available": true
            },
            {
              "pin_no": 5,
              "pin_name": "3.3V",
              "pin_pos": [3, 0],
              "available": true
            },
            {
              "pin_no": 6,
              "pin_name": "RESET",
              "pin_pos": [2, 0],
              "available": true
            },
            {
              "pin_no": 7,
              "pin_name": "IOREF",
              "pin_pos": [1, 0],
              "available": true
            },
            {
              "pin_no": 8,
              "pin_name": "NC",
              "pin_pos": [0, 0],
              "available": false
            }
          ]
        }, 
        {
          "header_name": "ANALOG IN",
          "header_shape": [6, 1],
          "header_pos": [16, 16],
          "pins": [
            {
              "pin_no": 1,
              "pin_name": "A5",
              "pin_pos": [7, 0],
              "available": false
            },
            {
              "pin_no": 2,
              "pin_name": "A4",
              "pin_pos": [6, 0],
              "available": false
            },
            {
              "pin_no": 3,
              "pin_name": "A3",
              "pin_pos": [5, 0],
              "available": false
            },
            {
              "pin_no": 4,
              "pin_name": "A2",
              "pin_pos": [4, 0],
              "available": false
            },
            {
              "pin_no": 5,
              "pin_name": "A1",
              "pin_pos": [3, 0],
              "available": false
            },
            {
              "pin_no": 6,
              "pin_name": "A0",
              "pin_pos": [2, 0],
              "available": false
            }
          ]
        }       
      ]
    },
    {
      "device_id": 0,
      "device_name": "Raspberry Pi 3 No. 1",
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
              "available": false
            },
          ]
        }
      ]
    },
    {
      "device_id": 1,
      "device_name": "Raspberry Pi 3 No. 2",
      "device_shape": [34, 22],
      "device_pos": [5, 30],
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
  ],
  "connections": [
    // {
    //   'from': {
    //     'device_id': 0,
    //     'header_name': "GPIO",
    //     'pin_no': 2
    //   },
    //   'to': {
    //     'device_id': 1,
    //     'header_name': "GPIO",
    //     'pin_no': 39
    //   }
    // }
  ]
}

function amendPlatformJSON(connections) {
  var targetConnections = []
  
  for (var i in connections) {
    var connection = connections[i];
    var targetEntry = {
      'from': {
        'device_id': connection.src.data('device').device_id,
        'header_name': connection.src.data('header').header_name,
        'pin_no': connection.src.data('pin').pin_no
      },
      'to': {
        'device_id': connection.dst.data('device').device_id,
        'header_name': connection.dst.data('header').header_name,
        'pin_no': connection.dst.data('pin').pin_no
      }
    }
    targetConnections.push(targetEntry)
  }

  platform.connections = targetConnections
}

window.addEventListener('load', function() {

  var pin_views = {}

  // The shape of the testbed
  var tb_shape = platform.testbed_shape

  // Set the size of wrapper div
  var root_div = document.getElementById('autowire')
  root_div.style.width = parseInt(PIN_PX * tb_shape[0]) + 'px'
  root_div.style.height = parseInt(PIN_PX * tb_shape[1]) + 'px'

  // Draw the outmost testbed box
  var root = SVG("autowire")
  console.log(root)
  root.viewbox(0, 0, PIN_PX * tb_shape[0], PIN_PX * tb_shape[1]);
  root.rect(PIN_PX * tb_shape[0], PIN_PX * tb_shape[1]).fill("#fff").stroke({ width: 2, color: "black" })
    .click(function() {
      if (sourcePin && activeWire){
        sourcePin = null
        activeWire.remove()
        activeWire = null
      }
    })

  // Connections established
  var connections = []

  var textLabel = root.nested().move(PIN_PX, 2 * PIN_PX).font({ 'size': 2 * PIN_PX })
  var textLabelText = textLabel.plain("")
  textLabelText.build(false)

  // Variables for drawing the connecting wires: null if there is no active source of connection
  var sourcePin = null
  var activeWire = null
  var sourceX = 0
  var sourceY = 0

  // Cursor tracking and events
  var cursorX = 0
  var cursorY = 0
  root.mousemove(function(e) {
    cursorX = e.clientX + CURSOR_OFFSET
    cursorY = e.clientY + CURSOR_OFFSET

    if (activeWire && sourcePin) {
      activeWire.plot(sourceX, sourceY, cursorX, cursorY)
    }
  })

  // Draw all the devices
  for (var dev_idx in platform.devices) {
    var dev = platform.devices[dev_idx]
    var device = root.nested().move(PIN_PX * dev.device_pos[0], PIN_PX * dev.device_pos[1])
    device.rect(PIN_PX * dev.device_shape[0], PIN_PX * dev.device_shape[1])
      .fill("#fff")
      .stroke({ width: 1, color: "black"})
      .click(function() {
        // Clear cursor selection
        if (sourcePin && activeWire){
          sourcePin = null
          activeWire.remove()
          activeWire = null
        }
      })

    pin_views[dev.device_id] = {}

    for (var hdr_idx in dev.pin_headers) {
      var hdr = dev.pin_headers[hdr_idx]
      var header = device.nested().move(PIN_PX * hdr.header_pos[0], PIN_PX * hdr.header_pos[1])
      
      pin_views[dev.device_id][hdr.header_name] = {}

      for (var pin_idx in hdr.pins) {
        var pin = hdr.pins[pin_idx]
        var pin_rect;

        if (pin.available) {
          pin_rect = header.rect(PIN_PX, PIN_PX)
            .fill("#fff")
            .stroke({ width: 1, color: "black"})
            .move(PIN_PX * pin.pin_pos[0], PIN_PX * pin.pin_pos[1])
            .mouseover(function() { 
              if (pin.available) {
                this.fill("#000")
              }
              
              textLabelText.plain(this.data('device').device_name + ' ' + this.data('header').header_name + ' ' + this.data('pin').pin_name)
            })
            .mouseout(function() {
              this.fill("#fff") 
              textLabelText.plain("None")
            })
            .click(function() {
              if (!sourcePin) {
                for (var i in connections) {
                  var connection = connections[i]
                  if (this == connection.src || this == connection.dst) {
                    connection.wire.remove()
                    connections.splice(i, 1)
                    break
                  }
                }

                sourcePin = this

                sourceX = this.parent().parent().x() + this.parent().x() + this.x() + PIN_PX / 2
                sourceY = this.parent().parent().y() + this.parent().y() + this.y() + PIN_PX / 2

                activeWire = root.line(sourceX, sourceY, cursorX, cursorY).stroke({ width: 1, color: 'blue'})
              } else {
                console.log(connections)

                var willPush = true

                for (var i in connections) {
                  var connection = connections[i]
                  if (this == connection.src || this == connection.dst) {
                    willPush = false
                    activeWire.remove()
                    break
                  }
                }

                if (willPush) {
                  connections.push({
                    'wire': activeWire,
                    'src': sourcePin,
                    'dst': this
                  })  
                }
                
                var activeWireLocal = activeWire

                sourcePin = null
                activeWire = null

                if (willPush) {
                  activeWireLocal.plot(sourceX, sourceY, this.parent().parent().x() + this.parent().x() + this.x() + PIN_PX / 2, this.parent().parent().y() + this.parent().y() + this.y() + PIN_PX / 2)
                  activeWireLocal.marker('end', 20, 20, function(add) {
                    add.path('M4 5 L4 15 L12 10 Z')
                    this.fill('blue')
                  })
                } 
              }
            })
            .data('pin', pin)
            .data('header', hdr)
            .data('device', dev)
        } else {
          pin_rect = header.rect(PIN_PX, PIN_PX)
            .fill("#666")
            .stroke({ width: 1, color: "black"})
            .move(PIN_PX * pin.pin_pos[0], PIN_PX * pin.pin_pos[1])
            .data('pin', pin)
            .data('header', hdr)
            .data('device', dev)
        }
        
        pin_views[dev.device_id][hdr.header_name][pin.pin_no] = pin_rect
      }
    }
  }

  // Recover the connections if any
  if (platform.connections) {
    // Recover the internal connections representation
    for (var i in platform.connections) {
      var connExternal = platform.connections[i]
      var src = pin_views[connExternal.from.device_id][connExternal.from.header_name][connExternal.from.pin_no]
      var dst = pin_views[connExternal.to.device_id][connExternal.to.header_name][connExternal.to.pin_no]
      
      var srcX = src.parent().parent().x() + src.parent().x() + src.x() + PIN_PX / 2
      var dstX = dst.parent().parent().x() + dst.parent().x() + dst.x() + PIN_PX / 2
      var srcY = src.parent().parent().y() + src.parent().y() + src.y() + PIN_PX / 2
      var dstY = dst.parent().parent().y() + dst.parent().y() + dst.y() + PIN_PX / 2
      
      var wire = root.line(srcX, srcY, dstX, dstY).stroke({ width: 1, color: 'blue'})
        .marker('end', 20, 20, function(add) {
                  add.path('M4 5 L4 15 L12 10 Z')
                  this.fill('blue')
                })

      var connInternal = {
        'src': src,
        'dst': dst,
        'wire': wire
      }

      connections.push(connInternal)
    }
  }

  window.addEventListener('keyup', function(e) {
    if (e.keycode === 13 || e.which === 13) {
      amendPlatformJSON(connections)
      console.log(platform)

      var xhttp = new XMLHttpRequest()
      xhttp.open('POST', 'wire/configure_device', true)
      xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8")
      xhttp.send(JSON.stringify(platform))
    }
  })
})






