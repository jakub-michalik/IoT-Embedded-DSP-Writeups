**Embedded Rust in 2026: Embassy Is Just the Default Now (Even on the nRF52)**

I read a really good deep-dive the other day — youngju.dev's "Embedded Rust 2026" (14 May 2026) — and it crystallized something I'd been feeling for a while but hadn't said out loud: Embassy isn't "the cool async option" anymore. It's just *the default*. This is a light recap of what changed, with a bias toward the nRF52, which is where I tend to live (see my earlier write-up, [RustOnnRF52BLEAndLowPower.md](./RustOnnRF52BLEAndLowPower.md)).

---

### The big shift: main loop is no longer the starting point

The headline from the post is blunt: Embassy 0.6 is now the de facto default async runtime on MCUs. According to the deep-dive, new projects rarely reach for the old "main loop + interrupt handlers" pattern anymore. You don't start with a superloop and bolt async on later — you start async.

That's a real cultural change. A couple of years ago, picking Embassy felt like a bet. Now it's the boring, sensible choice, and the general thrust of the article is that "Embedded Rust is production-ready in 2026." Not "almost there," not "promising." Production-ready.

---

### What this looks like on the nRF52

This is the part I cared about most. The deep-dive notes that `embassy-nrf` now has stable support across `nRF52832`, `nRF52840`, `nRF5340`, and the newer `nRF54L`. So the whole nRF52 line I've been writing about is squarely supported, not living on a feature branch somewhere.

BLE is where it gets interesting. Per the post, you've got two paths:

- The **SoftDevice wrapper** route — the familiar Nordic stack, wrapped so Rust can talk to it.
- A **pure-Rust host called `trouBLE`** — no SoftDevice at all — which reportedly runs on the nRF52 among other targets.

The pure-Rust host is the one that makes me sit up. Dropping the SoftDevice means one less precompiled blob, one less memory carve-out, and (in principle) a stack you can actually read. I haven't shipped anything on `trouBLE` myself, so take my enthusiasm as exactly that — enthusiasm — but the direction is the right one.

---

### One HAL to rule the STM32s

Slightly off my nRF beat, but worth noting because it shows how the ecosystem is consolidating: the article points out that `embassy-stm32` is a single HAL spanning *all* STM32 families, with async wakers wired up for UART, SPI, I2C, ADC, DMA, and USB. One crate, the whole zoo. That kind of breadth is part of why "just use Embassy" has become the path of least resistance.

---

### The tooling finally feels normal

Two tooling notes from the post that match my experience:

**probe-rs has replaced the OpenOCD + GDB dance.** A plain `cargo run` now does the whole thing — flash, RTT logging, and backtraces — in a single terminal. No three-window setup, no `target remote :3333` muscle memory.

**defmt keeps logs cheap.** The format strings stay on the host, so each log costs roughly 4-8 bytes on the device. On a part where flash and RAM are the whole budget, that's the difference between "logging is a luxury" and "log freely."

---

### A taste of the programming model

Here's the shape of an Embassy app — a blink task awaiting on a timer. Nothing exotic, and that's the point:

```rust
use embassy_executor::Spawner;
use embassy_nrf::gpio::{Level, Output, OutputDrive};
use embassy_time::{Duration, Timer};

#[embassy_executor::task]
async fn blink(mut led: Output<'static>) {
    loop {
        led.set_high();
        Timer::after(Duration::from_millis(500)).await;
        led.set_low();
        Timer::after(Duration::from_millis(500)).await;
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let p = embassy_nrf::init(Default::default());
    let led = Output::new(p.P0_13, Level::Low, OutputDrive::Standard);
    spawner.spawn(blink(led)).unwrap();
}
```

The `Timer::after(...).await` is the whole idea: while that task is waiting, the executor parks it and the MCU can sleep. No spin, no manual flag-juggling in an interrupt handler. Multiply that across a BLE stack, a sensor, and a UART, and you get cooperative concurrency without an RTOS.

---

### So, should you switch?

If you're starting something new on an nRF52 (or honestly any of the supported MCUs), the deep-dive's implicit answer — and mine — is: just start with Embassy. The friction that used to justify the old superloop pattern has mostly evaporated. The tooling is calm, the HALs are broad, and on the BLE side you've now got a no-SoftDevice option worth watching.

I'll likely revisit my earlier nRF52 BLE write-up through a `trouBLE` lens once I've actually put hands on it. For now: read the original, it's better than this recap.

---

### Source

- Embedded Rust 2026 Deep Dive: https://www.youngju.dev/blog/culture/2026-05-14-embedded-rust-2026-esp-rs-embassy-rp2040-stm32-no-std-hands-on-deep-dive.en
- Embassy: https://embassy.dev/
