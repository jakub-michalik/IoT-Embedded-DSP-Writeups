**nRF54 and Ultra-Low Power Embedded Rust: Reaching 30µA and Below**

Nordic's nRF54 family represents a significant step change in what's achievable with low-power wireless IoT. The nRF54L15—the first member of the nRF54L sub-family—achieves sleep currents that make the already-impressive nRF52 series look power-hungry. We're talking about active current in the sub-100µA range for many real-world duty-cycled applications, and sub-2µA in deep sleep. The fundamental question is: what does it take to actually reach those numbers in a Rust-based firmware, and what does the nRF54 bring architecturally to get there?

---

### What Changed in the nRF54 Generation

The nRF52840 was excellent for its time, but it wasn't designed with the assumption that you'd spend 99.9% of time in deep sleep. The nRF54L series made different tradeoffs:

**VDD0.8 domain**: Core logic runs at 0.8V rather than the 1.2V of nRF52. Lower supply voltage directly reduces dynamic power consumption (P = CV²f).

**PPIB (Programmable Peripheral Interconnect Bus)**: A hardware event routing fabric that lets peripherals trigger each other and the DMA without waking the CPU. A sensor can trigger a DMA read, which fills a buffer, which triggers a second DMA write to flash storage, all without the CPU leaving sleep.

**Global Power Management Unit (GPMU)**: More granular power domain gating than the nRF52. You can leave only the RTC and a single GPIO interrupt wakeup powered while the rest of the chip is fully off.

**Cortex-M33 with TrustZone**: PSA Certified security, relevant for Matter device certification.

The result: active current for a single GPIO toggle at 64 MHz is roughly 0.8mA on the nRF54L15 versus 2.5mA on the nRF52840 at equivalent frequency. Sleep current in System Off with RAM retention is 0.7µA versus 1.5µA.

---

### Anatomy of a 30µA Application

Getting to 30µA average current over a duty cycle requires understanding exactly where current is being spent. Let's walk through a concrete example: a Thread-connected environmental sensor sampling temperature and humidity every 30 seconds, transmitting via Thread if the value has changed significantly.

**Sleep phase** (29.8 seconds out of every 30): LFOSC running for RTC wakeup, PPIB and GPIOTE active for interrupt wakeup capability, everything else off. On nRF54L15: ~1.2µA.

**Sensor read phase** (~5ms): CPU active at 64 MHz, I2C (TWIM) transfer to read sensor, processing in Rust. On nRF54L15: ~2.5mA × 0.005s / 30s = 0.42µA weighted average.

**Thread transmission phase** (only when value changed, assume 10% of cycles, ~8ms per transmission including radio): ~8mA × 0.008s × 0.1 / 30s = 0.21µA weighted average.

**Total estimated average**: ~1.2 + 0.42 + 0.21 ≈ **1.83µA**. On a 500mAh AA battery, that's roughly 31 years of runtime. In practice, factors like battery self-discharge and wakeup from external events push this higher, but reaching sustained operation below 30µA is entirely achievable.

For an application that transmits more often (say, every second), the radio energy dominates and you'd be looking at more like 30–80µA depending on Thread topology—still excellent by historical standards.

---

### Embassy on nRF54

`embassy-nrf` support for the nRF54L series is in active development. The nRF54L15 has enough architectural differences from the nRF52 family that peripheral drivers needed significant updates. By late 2025, basic peripheral support (GPIO, TWIM, SPIM, UART, RTC, SAADC) was functional.

Power management in Embassy on nRF54 follows the same pattern as nRF52—the executor automatically sleeps via WFE when no tasks are ready:

```rust
#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let p = embassy_nrf::init(Default::default());

    // Configure retained RAM region (minimum needed for wakeup)
    configure_retained_ram();

    spawner.spawn(sensor_loop(p.TWIM0, p.P0_04, p.P0_05)).unwrap();
    spawner.spawn(thread_handler(p.RADIO)).unwrap();
}

#[embassy_executor::task]
async fn sensor_loop(twim: TWIM0, sda: AnyPin, scl: AnyPin) {
    let config = twim::Config::default();
    let mut sensor_bus = Twim::new(twim, Irqs, sda, scl, config);

    loop {
        let reading = read_sensor(&mut sensor_bus).await;
        if reading.is_significant_change() {
            THREAD_SEND.send(reading).await;
        }
        Timer::after_secs(30).await; // CPU enters WFE sleep here
    }
}
```

The `Timer::after_secs(30)` call suspends the task and programs the RTC to fire after 30 seconds. The CPU enters sleep. Nothing runs until the RTC interrupt fires, the executor wakes, and the task resumes. If no other task needs to run during those 30 seconds, the chip is effectively in System On sleep with only the RTC and optionally the GPIOTE running.

---

### PPIB: Eliminating CPU Wakeups for Routine Operations

The PPIB is worth understanding for applications that need to do periodic work without waking the CPU at all. For example, a sensor that logs data at 10Hz to flash storage:

**nRF52 approach**: RTC interrupt → CPU wakes → reads SAADC → DMA to flash → CPU sleeps. The CPU wakeup overhead is 10µA × ~1ms = 10µAs per sample, or 100µA average at 10Hz. Significant.

**nRF54 PPIB approach**: Configure PPIB to route RTC compare event → trigger SAADC → SAADC end event → trigger DMA write to flash. The CPU never wakes. CPU contribution to current: zero. Total is just SAADC active current (~0.1mA × 50µs = 5nAs per sample).

Setting this up requires configuring the PPIB subscription and publication channels. In Rust, this means writing to the SUBSCRIBE and PUBLISH registers of each peripheral involved:

```rust
// PPIB channel 0: RTC → SAADC
nrf54l15_pac::PPIB00::ptr().write(|w| unsafe {
    w.subscribe0().bits(RTC_COMPARE_CHANNEL_ID)
     .publish0().bits(SAADC_START_CHANNEL_ID)
});
```

The exact API depends on the PAC crate maturity for the nRF54L15 at the time you're working. This kind of low-level register work is where you'll dip below the HAL abstraction, but it's well worth it for applications with strict power budgets.

---

### Measuring Real Power Consumption

Nordic's Power Profiler Kit 2 (PPK2) is the right tool for this work. It samples current at up to 100kHz and can display the average over any time window. A typical workflow:

1. Build firmware with a specific feature/configuration
2. Flash and run while connected to PPK2
3. Measure average current over 5–10 minutes to smooth out radio transmission spikes
4. Identify wakeup sources causing unexpected current by looking at the time-domain profile

Common surprises when profiling:
- Floating GPIO pins drawing leakage current (fix: configure all pins explicitly)
- Debug interface (SWD) keeping the CPU from deep sleeping (fix: disable SWD in production builds)
- Peripheral left enabled between uses (fix: disable after each use, or use PPIB to avoid enabling the CPU at all)
- RAM retention scope too wide (fix: minimize retained RAM to only what's needed across sleep cycles)

---

### Summary

The nRF54L series represents a genuine leap in what's achievable for wireless IoT power consumption. Getting to sustained 30µA or below in a real-world Thread-connected application is realistic with careful design. The key ingredients are: minimal CPU active time through PPIB-based peripheral chaining, aggressive RAM retention scope minimization, explicit power-off of all unused peripherals, and measuring actual consumption rather than estimating from datasheets. Embassy's cooperative multitasking model aligns naturally with this style of development—the implicit WFE on task suspension does the right thing, and the async model makes the duty-cycled structure of the firmware explicit and readable.
