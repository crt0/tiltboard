# tiltboard: web interface for visualizing Tilt app data

Tiltboard is for you if you want to look at their Tilt status and data
on a static web site you control, as opposed to Google
Sheets. Tiltboard doesn't talk to the Tilt itself (there are many
other projects you can load onto a Raspberry Pi to do that) but from
the Tilt mobile app, which you'll need to run on a dedicated mobile
device within Bluetooth range of the Tilt.

Tiltboard consists of two parts: a receiver (`tb-recv`) that receives
and processes data via the web from the Tilt app, and a publisher
(`tb-pub`) that publishes the data as static HTML for human
consumption.
