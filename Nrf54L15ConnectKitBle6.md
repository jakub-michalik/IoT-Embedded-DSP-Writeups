**Nordic's nRF54L15 Connect Kit: Bluetooth LE 6.0 and a RISC-V Sidekick**

---

I wasn't planning to write anything today, but the nRF54L15 Connect Kit popped up in my feed and a couple of details made me pause. A small Nordic dev board is not exactly headline material on its own, but "Bluetooth LE 6.0" and "RISC-V coprocessor" sitting next to each other on a low-power wireless SoC is the kind of combination that catches my eye. So here are some quick thoughts, based entirely on what LinuxGizmos wrote and Nordic's own product page.

### What's actually in it

The interesting part is the silicon. According to LinuxGizmos, the nRF54L15 pairs a 128 MHz Arm Cortex-M33 with a 128 MHz RISC-V coprocessor. I like that framing of a "sidekick" core, because for a lot of wireless designs the main application core ends up babysitting timing-sensitive housekeeping it would rather offload. Having a second core at the same clock to soak up that work, rather than a tiny always-on management blob, feels like the more useful version of this idea. I haven't dug into exactly what the RISC-V core is meant to handle, so I'll leave it at "neat" for now.

On memory, LinuxGizmos reports 1.5 MB of NVM and 256 KB of RAM. That's a comfortable budget for the kind of workloads this thing is aimed at — plenty for a Matter or Thread node, and not bad for BLE applications that want a bit of room to breathe.

### The protocol checklist

This is where Nordic is clearly going for the "one chip, many radios" pitch. Per the article, the kit covers:

- Bluetooth LE 6.0
- Thread
- Matter
- Zigbee
- NFC
- IEEE 802.15.4-2020

That's the full smart-home and mesh bingo card. If you're building something that needs to speak Matter over Thread today but might want Zigbee or plain BLE tomorrow, having all of it on one part is genuinely convenient. NFC is a nice extra for things like tap-to-provision or pairing handoff.

### What does BLE 6.0 buy you?

Honestly, this is the bit I'm least sure about, so take it with a grain of salt. From what I understand, the headline feature people associate with Bluetooth LE 6.0 is Channel Sounding — a standardized way to estimate distance between two devices, using both phase-based and round-trip-time measurements. The pitch is accurate ranging: think finding a tag, secure proximity unlocking, or knowing roughly how far apart two nodes are without bolting on UWB.

I want to be careful here: the LinuxGizmos piece lists BLE 6.0 as a supported protocol, and I'm filling in the "why you'd care" from general knowledge rather than anything the article claims. If precise ranging is on your roadmap, it's worth confirming against Nordic's actual specs how much of the Channel Sounding story this part supports.

### The power story

The detail that probably matters most for real products is the power design. LinuxGizmos reports the board uses a TPS63901 buck-boost converter with a quiescent current of around 75 nA. That is a very small idle draw, and for a battery-powered sensor that spends most of its life asleep, the converter's quiescent current often dominates the energy budget more than the radio does. Picking a buck-boost with that kind of standby figure suggests Nordic is thinking about coin-cell and energy-harvesting style use cases, not just bench demos.

Power input is flexible too: the article notes USB-C, a battery option, and a 1.8–5.5 V supply range. The wide input range is the friendly part — it means you can run it off a wide spread of battery chemistries without extra regulation gymnastics.

### Out-of-the-box developer experience

For getting started, LinuxGizmos says the kit ships with a preinstalled Quick Start Demo, so you can plug it in and see something happen before writing a line of code. Nordic also provides samples covering GPIO, NFC, BLE profiles, and Thread. That's a sensible starter set — enough to poke at each radio and the basic I/O without assembling an example from scratch. I always appreciate when a board lets you confirm it's alive before you've committed to a toolchain.

### Quick take

Nothing here is revolutionary on its own, but the package is tidy: a dual-core (Cortex-M33 plus RISC-V) low-power SoC, the full mesh-and-BLE protocol spread including Bluetooth LE 6.0, a seriously low idle-current power path, and a board that's apparently ready to demo out of the box. If I were starting a new low-power wireless project, this is the kind of kit I'd want on the bench to evaluate. I haven't touched the hardware — this is just me reacting to the news — but it's gone on my "worth a closer look" list.

### Source

- LinuxGizmos: https://linuxgizmos.com/nordic-nrf54l15-connect-kit-adds-bluetooth-le-6-0-thread-zigbee-and-nfc-support/
- nRF54L15: https://www.nordicsemi.com/Products/nRF54L15
