'use strict'

function AWViewBase(parent) {
    this.parent = parent
    this.subviews = []

    if (this.parent) {
        this.parent.subviews.push(this)
    }
}

AWViewBase.prototype.draw = function() {}

function AWRootView(parent, id, w, h) {
    AWViewBase.call(this, parent)
    this.w = w
    this.h = h
    this.svg = SVG(id)
    this.svg.viewbox(0, 0, w, h)
    this.ctnr = this.svg
}

AWRootView.prototype = Object.create(AWViewBase.prototype)
AWRootView.prototype.constructor = AWRootView

AWRootView.prototype.draw = function() {
    this.svg.rect(this.w, this.h).fill("#fff").stroke({ width: 2, color: "black" })
}

function AWDeviceView(parent, x, y, w, h) {
    AWViewBase.call(this, parent)
    this.x = x
    this.y = y
    this.w = w
    this.h = h
    this.ctnr = this.parent.ctnr.nested().move(x, y)
}

AWDeviceView.prototype = Object.create(AWViewBase.prototype)
AWDeviceView.prototype.constructor = AWDeviceView

AWDeviceView.prototype.draw = function() {
    this.ctnr.rect(this.w, this.h).fill("#fff").stroke({ width: 1, color: "black" })
}

function AMHeaderView(parent, x, y, npx, npy) {
    AWViewBase.call(this, parent)
    this.x = x
    this.y = y
    this.w = npx * 8
    this.h = npy * 8
    this.npx = npx
    this.npy = npy
    this.ctnr = this.parent.ctnr.nested().move(x, y)

    this.pinViews = []
    for (var i = 0; i < npx; i++) {
        var pinViewRow = []
        for (var j = 0; j < npy; j++) {
            var pinView = new AMPinView(this, i * 8, j * 8)
            pinViewRow.push(pinView)
        }
        this.pinViews.push(pinViewRow)
    }
}

AMHeaderView.prototype = Object.create(AWViewBase.prototype)
AMHeaderView.prototype.constructor = AMHeaderView

AMHeaderView.prototype.draw = function() {
    this.ctnr.rect(this.w, this.h).fill("#fff").stroke({ width: 1, color: "black" }).opacity(0)
    for (var i = 0; i < this.subviews.length; i++) {
        console.log(this.subviews[i])
        this.subviews[i].draw()
    }
}

function AMPinView(parent, x, y) {
    AWViewBase.call(this, parent)
    this.x = x
    this.y = y
    this.w = 8
    this.h = 8
    this.ctnr = this.parent.ctnr.nested().move(x, y)
}

AMPinView.prototype = Object.create(AWViewBase.prototype)
AMPinView.prototype.constructor = AMPinView

AMPinView.prototype.draw = function() {
    this.ctnr.rect(this.w, this.h).fill("#fff").stroke({ width: 1, color: "black" })
}

window.addEventListener('load', function() {
    var root = new AWRootView(null, "autowire", 640, 480)
    root.draw()
    var device = new AWDeviceView(root, 20, 20, 100, 300)
    device.draw()
    var header = new AMHeaderView(device, 20, 20, 2, 20)
    header.draw()
})

