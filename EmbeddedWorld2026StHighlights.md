**What ST Showed at Embedded World 2026: AI Creeping Onto the MCU**

---

Embedded World always produces a pile of "look what we built" demos, and this year STMicroelectronics leaned into one idea hard enough that it's worth a quick write-up. I wasn't there in person, but ST's recap of the show makes the theme pretty clear: **physical AI** is the headline, and the interesting part is that it's increasingly running on plain microcontrollers rather than the beefier application processors you'd normally reach for.

Here's my quick read of what stood out.

### "Physical AI," but on an MCU

The phrase ST keeps using is *physical AI* — edge AI that lives inside the device interacting with the real world, instead of phoning home to a cloud GPU. That's not a new aspiration. What's new, according to the ST blog, is how far down the silicon stack it's sliding. The pitch isn't "AI at the edge" in the hand-wavy sense; it's AI on the kind of chip that historically just blinked LEDs and read sensors.

If you've spent any time fighting to squeeze a model onto a Cortex-M part, you know why that's a big deal. The usual answer has been "buy a bigger processor." ST's argument this year is that you increasingly don't have to.

### STM32N6 and the Neural-ART accelerator

The flagship example is the STM32N6. ST says its on-chip Neural-ART accelerator delivers around **600 GOPS** — and the framing that caught my eye is that workloads which used to *require* a microprocessor can now run on a microcontroller, at a fraction of the power.

I'd take any single GOPS number with the usual grain of salt — peak throughput and real-world throughput are rarely the same animal, and ST is obviously selling something here. But even discounting for marketing, the directional claim is interesting: a dedicated NPU sitting next to a Cortex-M core changes what's reasonable to attempt on a device with an MCU power budget. Vision, audio, anomaly detection — the stuff that used to mean "okay, now we need Linux and a heatsink" starts looking feasible on a part that boots in milliseconds and sips power.

That's the whole value proposition in one line: keep the simplicity, cost, and power profile of an MCU, but get a chunk of the AI capability you'd previously have to step up to a microprocessor for.

### The graphics demo that uses almost no RAM

The other demo I liked was less about AI and more about a flex on resource efficiency. ST showed an STM32H7R/S running an advanced, high-resolution GUI — the example was a coffee machine interface — and the number they put on it is that it ran using only about **285 KB of internal RAM**.

If you've ever built an embedded UI, that number is the punchline. Modern-looking, high-res GUIs usually want a framebuffer (or two) and external RAM to back it, which adds cost, board complexity, and power. Pulling off something that looks good while staying inside a few hundred KB of *internal* RAM is the kind of thing that quietly saves a BOM line. According to the ST blog, that's exactly the point they were making with it.

### The through-line

Put the two demos together and you get ST's overall message for the show: **AI plus graphics plus low power, all on a microcontroller.** One chip family pushing on inference performance, another pushing on doing more with less memory — both aimed at the same place, which is letting product teams stay on MCUs for longer before they're forced to "graduate" to an MPU and everything that comes with it.

Is it as clean as a trade-show recap makes it sound? Probably not — these are curated demos, and the gap between a Neural-ART showcase and your specific model on your specific data is where the real engineering happens. But the trend is genuine and it's been building for a couple of years now: the floor for "what an MCU can do" keeps rising, and the line between microcontroller and microprocessor keeps getting blurrier.

For anyone shipping battery-powered or cost-sensitive hardware, that's a good problem to have. Worth keeping an eye on the STM32N6 in particular if you've got an edge-AI idea that didn't quite fit a year ago — it might fit now.

### Source

- ST blog, Embedded World 2026: https://blog.st.com/embedded-world-2026/
- STM32N6: https://blog.st.com/stm32n6/
