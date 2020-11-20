# lcus_relay: A Python package for Shenzhen LC serial USB relays
The Shenzhen LC (LCUS*) family of USB serial relay devices present
themselves on the USB bus as standard serial devices. Programming
these devices is much simpler than the HID based ones. This package
makes it easy to control these devices from Python and is compatible
with 2.7+ and 3.0+.

The package was created using a
[LCUS_X2 module](http://www.chinalctech.com/cpzx/Programmer/Relay_Module/115.html "LCUS_X2 module").

## Installation
The external
[pyserial version 3.0+](https://github.com/pyserial/pyserial "pyserial")
package is all that's required. Use your OS or your favorite Python
package manager to install it.

## Usage
```python
import lcus_relay
r = lcus_relay.Relay(port='/dev/ttyUSB0')
print(r.status())   # prints {1: False, 2: False}
r.on(1)   # returns True
r.status(1)  # returns {1: True}
r.toggle(2, 1000)  # toggles on for 1000 milliseconds and returns True
r.off()  # returns True
r.status()  # returns {1: False, 2: False}
r.on(3)  # returns False (relay doesn't exist)
```
For more details about method calls use Python's `help(lcus_relay.Relay)`.
