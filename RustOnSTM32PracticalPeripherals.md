**Rust on STM32: Practical Peripherals, HAL Abstractions, and the H7 in the Real World**

ST's STM32 family has been the bread and butter of embedded development for over a decade, and the Rust ecosystem around it has matured considerably. Between the `stm32-hal2` crate, the family of PAC (Peripheral Access Crate) crates generated from SVD files, and the growing Embassy async framework, writing production-grade firmware for STM32 in Rust is no longer an experiment—it's a viable path for new projects. This article gets into the practical details: HAL structure, dealing with the clock tree, DMA, and some specifics of the H7 series that catches people out.

---

### The Crate Landscape

For the STM32 family, you have a few layers to navigate:

**PACs** (e.g., `stm32f4`, `stm32h7`): Machine-generated from the vendor's SVD files. Provide raw register access. You rarely use these directly but they underlie everything else.

**HAL crates** (e.g., `stm32f4xx-hal`, `stm32h7xx-hal`): Built on top of the PAC, provide type-safe abstractions for peripherals. The `stm32h7xx-hal` crate is actively maintained and covers most of the H7's peripherals.

**Embassy** (`embassy-stm32`): An async runtime targeting embedded systems, with drivers for STM32 peripherals built on top of the PAC but with async/await support. If you're building a system that needs to juggle multiple concurrent operations, Embassy's approach is compelling.

For new projects, I'd lean toward either `stm32h7xx-hal` for a more traditional synchronous design or `embassy-stm32` for anything that benefits from async. They're not mutually exclusive—Embassy can work alongside blocking HAL code for specific peripherals.

---

### Clocks: The First Thing You Have to Get Right

The H7 clock tree is one of the most complex in the STM32 family. Multiple PLLs, multiple prescalers, and a split AHB/APB bus structure mean there are many ways to configure an invalid combination. The HAL crate catches most of these at runtime (panicking on invalid configurations) but not all.

A typical configuration for the STM32H743 running at 480 MHz:

```rust
use stm32h7xx_hal::{pac, prelude::*};

let dp = pac::Peripherals::take().unwrap();
let pwr = dp.PWR.constrain();
let pwrcfg = pwr.freeze();

let rcc = dp.RCC.constrain();
let ccdr = rcc
    .sys_ck(480.MHz())
    .pll1_q_ck(48.MHz())   // For USB
    .hclk(240.MHz())
    .pclk1(120.MHz())
    .pclk2(120.MHz())
    .pclk3(120.MHz())
    .pclk4(120.MHz())
    .freeze(pwrcfg, &dp.SYSCFG);
```

The H7 runs its Cortex-M7 core at up to 480 MHz but the AHB (memory bus) maxes at 240 MHz—the prescaler splits them 2:1. Getting this wrong gives you hard faults when accessing flash at speeds it can't support.

Another H7 gotcha: the D-cache and I-cache are enabled by default in some configurations but not in the HAL's startup sequence. Enable them explicitly at startup for full performance:

```rust
let mut core = cortex_m::Peripherals::take().unwrap();
core.SCB.enable_icache();
core.SCB.enable_dcache(&mut core.CPUID);
```

If you're using DMA (which you almost certainly will), the D-cache requires careful management—DMA writes to memory that the CPU might have cached, and the cache won't see the new data without a cache invalidation. More on that below.

---

### DMA: The Sharp Edge

DMA on the STM32H7 is where Rust's ownership model and embedded realities collide most visibly. DMA transfers require that the buffer stays alive and pinned for the duration of the transfer—the hardware is directly writing to that memory address. In C, you'd use a global array and be careful not to touch it during transfer. In Rust, you need a bit more thought.

The `stm32h7xx-hal` crate handles this through transfer types that take ownership of the buffer:

```rust
use stm32h7xx_hal::dma::{config::DmaConfig, Transfer};

// Buffer must be 'static or otherwise guaranteed to outlive the transfer
static mut RX_BUFFER: [u8; 256] = [0u8; 256];

let config = DmaConfig::default()
    .memory_increment(true)
    .priority(stm32h7xx_hal::dma::config::Priority::High);

// Transfer takes ownership, returns it when done
let transfer = Transfer::init_peripheral_to_memory(
    dma_stream,
    serial_rx,
    unsafe { &mut RX_BUFFER },
    None,
    config,
);
transfer.start(|_| {});
```

The D-cache interaction: if `RX_BUFFER` is in cacheable memory (which it usually is by default), you need to invalidate the cache region before reading the data after the DMA completes. The HAL crate doesn't do this automatically because it's architecture-specific:

```rust
// After transfer completes, invalidate cache for the buffer region
let start = RX_BUFFER.as_ptr() as u32;
let size = RX_BUFFER.len() as u32;
cortex_m::asm::dsb(); // Data sync barrier
// Platform-specific cache maintenance...
```

For real projects, placing DMA buffers in SRAM4 or SRAM3 (depending on which peripheral's DMA controller you're using) and configuring those regions as non-cacheable in the MPU saves a lot of headaches.

---

### Timers and PWM

Timer configuration in the H7 HAL follows the embedded-hal trait structure, which makes code reasonably portable. For PWM output:

```rust
use stm32h7xx_hal::{timer::Timer, pwm};

let gpioa = dp.GPIOA.split(ccdr.peripheral.GPIOA);
let ch1 = gpioa.pa8.into_alternate::<1>();

let pwm = dp
    .TIM1
    .pwm(ch1, 20.kHz(), ccdr.peripheral.TIM1, &ccdr.clocks);

let mut ch = pwm.split().0;
ch.enable();
ch.set_duty(ch.get_max_duty() / 2); // 50% duty cycle
```

The HAL figures out the appropriate prescaler and ARR values to achieve 20 kHz, accounting for the peripheral clock frequency. This is one of the places where the HAL abstraction genuinely saves time compared to doing the math manually.

---

### The H5 Series: A Practical Middle Ground

While the H7 is powerful, its complexity (dual-bank flash, multiple power domains, BDMA, MDMA...) can be overkill for many applications. The newer STM32H5 series is worth knowing about: Cortex-M33 core at up to 250 MHz, TrustZone support, hardware crypto accelerators, and a significantly simpler peripheral set than the H7. The Rust support is growing—`stm32h5xx-hal` is still young but usable for basic peripherals.

The H5 is particularly interesting for IoT and security-sensitive applications because TrustZone lets you run sensitive code (key storage, secure boot verification) in a hardware-isolated context, separate from the application code. This is increasingly relevant for compliance with security frameworks like PSA Certified.

---

### Practical Tips

A few things I've learned from STM32 Rust projects that the documentation doesn't make obvious:

**Flash wait states**: At high clock frequencies, you need more wait states for flash access. The HAL handles this automatically when you configure clocks through the RCC, but if you configure clocks manually (via the PAC), forgetting this causes mysterious hard faults at high speeds.

**Pull resistors on I2C**: STM32 internal pull-ups are weak (typically 40kΩ). For reliable I2C above a few kHz, use external pull-ups (4.7kΩ is a common starting point).

**The `cortex-m-rt` stack size**: The default stack size in `cortex-m-rt` is quite small. If you're getting stack overflows in inference code (which uses significant stack space for intermediate arrays), add `STACK_SIZE = 0x8000;` or similar to your memory.x linker script.

**probe-rs for debugging**: The `probe-rs` tool has matured significantly and provides a much better development experience than OpenOCD for most STM32 targets. `cargo flash` and `cargo embed` integrate it directly into the build toolchain.

---

### Summary

The Rust ecosystem for STM32 has reached the point where it's genuinely productive for real projects. The HAL crates handle the complexity of clock configuration, DMA, and peripheral initialization with reasonable type safety. The sharp edges—D-cache interactions, linker script configuration, DMA buffer placement—are manageable once you know where they are. For new STM32 designs, the H5 series deserves a serious look: the TrustZone support and hardware crypto acceleration are increasingly valuable, and the simpler architecture compared to the H7 makes it easier to reason about.
