**Debugging and Profiling TinyML Applications in Rust**

Getting a TinyML model to actually run on a microcontroller is satisfying—until you realize it's producing wrong results, crashing after a hundred inference cycles, or taking three times longer than your latency budget allows. I've been there more than once. Debugging embedded Rust is already a discipline of its own; add a machine learning inference engine on top, usually brought in through an FFI boundary from a C library, and the surface area for bugs expands considerably.

This writeup is about the practical techniques I've settled on for finding and fixing problems in TinyML applications built with Rust. Some of it is general embedded debugging wisdom, but a lot of it is specific to the TinyML context—tensor shape mismatches, arena sizing, numerical preprocessing errors, and latency profiling on hardware that doesn't come with a profiler.

---

### Start Simple: Semihosting for Correctness Checks

Before you worry about performance, you need to know the system is actually doing what you think it's doing. For that, semihosting is the quickest tool to reach for. With `cortex-m-semihosting`, you get `hprintln!` which works just like `println!`, except it routes output through the debug adapter to your host terminal:

```rust
use cortex_m_semihosting::hprintln;

hprintln!("Input buffer: {:?}", &input_data[..8]).unwrap();
hprintln!("Inference result index: {}", result_index).unwrap();
```

The important caveat: semihosting is *slow*. Each call involves a debug trap, context switch, and host-side processing. If you're trying to measure inference latency with semihosting calls inside the hot path, the numbers you get will be useless—sometimes off by orders of magnitude. Use semihosting to verify that your data flows correctly and that the model initialization succeeds, then strip those calls out entirely before you start measuring anything.

---

### Validating Inputs: The Most Common Source of Silent Failures

In my experience, a surprisingly large fraction of "the model outputs garbage" problems trace back to input preprocessing. The model was trained with float values normalized to the range [-1.0, 1.0], and the embedded code is feeding it raw 12-bit ADC readings in the range [0, 4095]. The model doesn't crash—it just produces confidently wrong results, which is in some ways worse.

The most reliable fix is to validate inputs before they reach the inference engine. If you have a UART available, temporarily dump a window of the input buffer and compare it against what your training pipeline would produce for the same raw data:

```rust
use core::fmt::Write;

fn dump_input_slice(tx: &mut impl Write, data: &[f32]) {
    for v in data {
        write!(tx, "{:.5},", v).ok();
    }
    write!(tx, "\r\n").ok();
}
```

Capture that output on the host side, run the same inference in Python with the original framework, and compare results. If the embedded output diverges, the bug is in preprocessing. If they match, look elsewhere—output tensor interpretation, model corruption, arena overflow.

---

### Memory: Arena Sizing and the Quiet Crash

TensorFlow Lite Micro requires you to hand it a static byte array—the "tensor arena"—at initialization time. Get the size wrong and you'll see one of two things: an initialization error (if you're handling errors correctly) or a silent crash later during inference (if you're not).

```rust
const ARENA_SIZE: usize = 48 * 1024;
static mut TENSOR_ARENA: [u8; ARENA_SIZE] = [0u8; ARENA_SIZE];
```

The right size depends entirely on your model and its intermediate activation buffers. TFLM can report how much of the arena was actually used after a successful initialization—this is the `arena_used_bytes()` call in the C++ API. If you're wrapping TFLM via FFI, expose that function. Use the reported value plus a small safety margin (10–15%) as your actual arena size.

For projects using a dynamic allocator (via `embedded-alloc` or similar), add instrumentation to your out-of-memory handler:

```rust
#[alloc_error_handler]
fn oom_handler(layout: core::alloc::Layout) -> ! {
    // Log the failing allocation size before halting
    hprintln!("OOM: requested {} bytes", layout.size()).unwrap();
    loop {}
}
```

When this fires, you know both that you're out of memory and roughly how much was being requested at the time. That's often enough to identify the culprit.

---

### Measuring Latency: GPIO Toggles and the DWT Counter

Once you're confident the model is producing correct results, the next question is usually: how long does it take? There are two practical approaches on ARM Cortex-M.

The simplest and most reliable is a GPIO toggle around the inference call, measured with an oscilloscope or logic analyzer:

```rust
profile_pin.set_high().unwrap();
unsafe { tflm_invoke(interpreter) };
profile_pin.set_low().unwrap();
```

The toggle overhead is in the tens of nanoseconds range—negligible compared to any real inference workload. This approach also gives you the actual wall-clock time on the hardware, which accounts for cache effects, bus contention, and other real-world factors that simulation misses.

If you don't have a logic analyzer handy, the DWT (Data Watchpoint and Trace) cycle counter works well:

```rust
use cortex_m::peripheral::DWT;

// Enable trace and the cycle counter before using it
cortex_m::peripheral::DCB::enable_trace();
DWT::unlock();
DWT::enable_cycle_counter();

let start = DWT::cycle_count();
unsafe { tflm_invoke(interpreter) };
let elapsed = DWT::cycle_count().wrapping_sub(start);

hprintln!("Inference: {} cycles ({} µs at 168 MHz)",
    elapsed,
    elapsed / 168).unwrap();
```

The `wrapping_sub` is important—the 32-bit counter wraps around after about 25 seconds at 168 MHz, and subtraction without wrapping semantics will give you a huge wrong number if that happens.

---

### Finding Bottlenecks Inside the Model

If inference is too slow, knowing the total time is only the starting point. You need to know *which layer* is taking most of that time. TFLM includes a profiling interface that, when enabled at compile time, calls a profiler object before and after each operator invocation. Getting this wired up from Rust requires some FFI work—you need to provide a C-compatible profiler implementation—but the payoff is a breakdown that looks something like:

```
CONV_2D:            8.2 ms
DEPTHWISE_CONV_2D:  3.1 ms
FULLY_CONNECTED:    0.4 ms
SOFTMAX:            0.1 ms
```

In practice, convolutional layers dominate on most small models. Once you have this data, your optimization options become clearer: quantizing the model from float32 to int8 typically gives a 3–4x speedup on those convolutions, and on Cortex-M4/M7 you can additionally route the quantized kernels through CMSIS-NN, which uses SIMD DSP instructions under the hood. TFLM does this automatically when compiled with the right flags—it's worth checking whether your build is actually taking advantage of it.

---

### Reproduce on the Host First

One pattern I've found consistently valuable: before spending an afternoon on hardware debugging, try to reproduce the issue in a standard hosted Rust test. You won't have the exact same memory layout or clock speed, but most logic bugs and numerical issues show up just as clearly on the host:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Instant;

    #[test]
    fn validate_preprocessing() {
        let raw_adc = [2048u16; 64]; // midpoint reading
        let normalized = preprocess(&raw_adc);
        // Should be all zeros after normalization from a midpoint
        assert!(normalized.iter().all(|&v| (v - 0.0f32).abs() < 1e-5));
    }

    #[test]
    fn bench_inference_iterations() {
        let input = vec![0.0f32; INPUT_SIZE];
        let start = Instant::now();
        for _ in 0..1000 {
            let _ = run_inference(&input);
        }
        println!("1000 iterations: {:?}", start.elapsed());
    }
}
```

Host-side tests run under the standard Rust test harness, so you get nice error messages, easy iteration, and access to tools like `cargo bench`, `perf`, or a flamegraph. The relative hotspot profile you get here usually transfers fairly well to the embedded target—it won't match in absolute terms, but if a particular function accounts for 60% of host-side time, it's probably also the bottleneck on hardware.

---

### Pulling It Together

Debugging TinyML in Rust is manageable if you work through it in layers. Start by confirming correctness—use semihosting to trace the data flow, dump inputs over UART and compare against your training pipeline, and make sure your arena is sized correctly. Once you're confident the model is producing the right answers, move on to performance: GPIO toggles or the DWT counter for overall latency, TFLM's operator profiler for layer-level breakdown.

Rust helps more than you might expect here. The type system catches a lot of interface mismatches at compile time, and the ownership model makes it harder to accidentally corrupt the tensor arena through a dangling pointer. The bugs that remain tend to be numerical or algorithmic—and those respond well to the empirical, measurement-first approach I've described.
