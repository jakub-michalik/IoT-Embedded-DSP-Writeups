**Power Management Strategies for TinyML Applications in Rust**

A microcontroller running inference continuously at full speed will drain a coin cell battery in hours. Battery-powered TinyML devices—wearables, environmental sensors, predictive maintenance nodes—need to run for months or years on a single charge. This changes how you think about nearly every part of the system design, from how often you sample sensors to whether you run the model at all on a given cycle. Rust's explicit control over hardware state and its lack of runtime overhead make it a good fit for this kind of aggressive power optimization.

---

### Why TinyML Makes Power Management Harder

Standard embedded power management follows a simple pattern: sleep when idle, wake on interrupt, do work, go back to sleep. TinyML complicates this because inference is not "a little work"—it's often the most compute-intensive operation the device does, and it takes time proportional to model complexity.

The tension is between inference frequency and power budget. A gesture recognition device needs to run inference often enough that it doesn't miss gestures. An anomaly detection node on industrial equipment might only need to run inference once per minute. Getting this tradeoff right is as important as optimizing the inference code itself.

A useful mental model: think of your power budget in terms of energy per unit time (millijoules per minute, or microampere-hours per day), and account for every phase of operation: sleep, sensor wakeup and sampling, preprocessing, inference, and any radio communication.

---

### Clock Gating and Frequency Scaling

The first lever is CPU clock frequency. Most modern MCUs support dynamic frequency scaling. Running at 16 MHz instead of 168 MHz uses dramatically less power—roughly proportional to frequency for dynamic power consumption—but inference takes proportionally longer.

For latency-tolerant applications, dropping the clock for inference and running longer is often a net win:

```rust
// In Rust via HAL
fn enter_low_power_inference_mode(rcc: &mut Rcc) {
    rcc.cfgr.hclk(16.mhz()).freeze(&mut flash.acr);
}

fn restore_full_speed(rcc: &mut Rcc) {
    rcc.cfgr.hclk(168.mhz()).freeze(&mut flash.acr);
}
```

The actual API depends on your HAL crate, but the pattern is consistent: configure the PLL before inference if you need full speed, or scale down if latency permits.

Beyond CPU frequency, gate the clocks to peripherals you don't need during inference. On most MCUs, the APB/AHB bus clock enables control whether each peripheral receives a clock signal. If your inference pipeline doesn't use UART or SPI, disable their clocks while the model is running:

```rust
rcc.apb1enr.modify(|_, w| {
    w.usart2en().disabled()
     .spi2en().disabled()
});
// run inference
rcc.apb1enr.modify(|_, w| {
    w.usart2en().enabled()
     .spi2en().enabled()
});
```

---

### Sleep Modes and Wakeup Strategy

Modern MCUs offer several sleep depths: Wait For Interrupt (WFI), Stop mode, Standby mode. Each trades deeper power savings for longer wakeup latency and greater state loss.

For a typical duty-cycled TinyML application, a common pattern is:

1. Wakeup from Stop mode via RTC alarm
2. Enable sensors, sample data, preprocess
3. Run inference
4. Decide whether to take action (transmit, actuate)
5. Power down sensors, return to Stop mode

In Rust, entering Stop mode after cleanup:

```rust
fn sleep_until_next_sample(pwr: &mut Pwr, scb: &mut SCB) {
    pwr.cr.modify(|_, w| w.pdds().stop_mode().lpds().main_regulator());
    pwr.cr.modify(|_, w| w.cwuf().set_bit()); // Clear wakeup flag
    scb.set_sleepdeep();
    cortex_m::asm::wfi(); // Enter Stop mode
    scb.clear_sleepdeep();
}
```

The key subtlety: RAM contents are preserved in Stop mode (unlike Standby), so your model arena, application state, and stack survive the sleep. This means you don't need to reload or reinitialize the inference engine on every wakeup, which saves significant time and power.

---

### Early Exit and Cascaded Models

One of the more effective techniques for reducing inference energy is to only run the full model when necessary. This works well for detection tasks where most of the time "nothing is happening."

A two-stage approach:
1. A very small, cheap "wake word" or "event detector" model runs continuously (or very frequently)
2. Only when stage 1 fires does the larger, more accurate model run

The stage 1 model might be 5KB and run in 2ms. The stage 2 model might be 50KB and run in 25ms. If events occur less than 8% of the time, the cascaded system uses less energy on average than running the full model continuously.

```rust
fn inference_loop(pipeline: &mut TwoStagePipeline, sensor: &mut impl Sensor) {
    loop {
        let reading = sensor.fast_sample();

        // Stage 1: cheap detector
        if pipeline.stage1.run(&reading).score > STAGE1_THRESHOLD {
            // Stage 2: expensive classifier, only on positive stage 1
            let full_input = sensor.full_window_sample();
            let result = pipeline.stage2.run(&full_input);
            handle_classification(result);
        }

        sleep_microseconds(SAMPLE_INTERVAL_US);
    }
}
```

The threshold for stage 1 should be tuned to minimize false negatives (events you miss) while keeping false positive rate low enough that stage 2 rarely fires unnecessarily.

---

### Sensor Power Management

Sensors are often as power-hungry as the MCU itself. An IMU in continuous measurement mode might draw 1.5mA—orders of magnitude more than a sleeping Cortex-M in Stop mode.

Most sensors support low-power modes with configurable ODR (output data rate). When you only need 10Hz measurements, there's no point running the sensor at 400Hz. The tradeoff is sensor wakeup time: some sensors take tens of milliseconds to stabilize after coming out of their lowest power state, which has to be factored into your duty cycle.

Where the sensor supports it, use hardware-triggered FIFO readout rather than polling. The MCU sleeps while the sensor fills its FIFO, then the MCU wakes on a data-ready interrupt, reads the batch, and goes back to sleep. This keeps both the MCU and the bus quiescent for the longest possible fraction of each cycle.

---

### Measuring What You're Actually Spending

All of this is meaningless without measurement. The tools:

**Ammeter in series** (for coarse analysis): a precision shunt and an oscilloscope across it give you current over time with good time resolution.

**Energy monitoring ICs**: chips like the INA219 or INA260 can measure both voltage and current via I2C with enough precision for embedded work. You can log energy consumption from Rust directly to a UART or flash storage during development.

**Nordic PPK2**: if you're targeting nRF devices, this is the most practical tool for real-time power profiling with per-sample energy breakdown.

Once you have measurement in place, profile the actual phases of your inference cycle. In my experience, the distribution is often surprising: sensor stabilization time and data transfer can dominate the cycle, with actual inference accounting for a smaller fraction than expected. Fix the actual bottleneck, not the assumed one.

---

### Summary

Power management for TinyML is fundamentally about minimizing energy per inference while maintaining the application's responsiveness requirements. In Rust, you have the control to implement aggressive power management strategies without the overhead of a runtime getting in the way. The key techniques—clock scaling, peripheral gating, deep sleep between cycles, cascaded models, and proper sensor management—compound: each one multiplies with the others. Combined with real measurement rather than guesswork, these strategies can extend battery life from hours to months or years.
