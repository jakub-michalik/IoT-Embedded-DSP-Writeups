**C++ in Embedded Systems: Power, Pitfalls, and When to Use It**

I want to be clear about something upfront: C++ is a genuinely good language for embedded development. I've spent time with both C++ and Rust on embedded targets, and saying "use Rust instead" is not always the right answer—sometimes C++ is the right tool, sometimes it's the only tool because your team already knows it, and sometimes you're working within a codebase that has fifteen years of C++ history and you're not going to rewrite it. Understanding C++ deeply, including where it can hurt you, is valuable regardless of what you write next.

That said, C++ in embedded has failure modes that I've seen trip up experienced developers. This article is about using C++ well in resource-constrained systems—getting the benefits of abstraction without paying unexpected costs in code size, RAM, or determinism.

---

### What C++ Gets Right

C++ gives embedded developers several things that C doesn't, and that genuinely matter:

**Zero-cost abstractions through templates**: When used carefully, C++ templates generate code that's as efficient as hand-written C. A templated UART driver can be specialized for different peripherals at compile time, with no runtime dispatch overhead. The abstraction is real and the cost is zero at runtime—it all happens during compilation.

**RAII for resource management**: Resource Acquisition Is Initialization means you tie a resource's lifetime to an object's lifetime. Open a SPI bus, wrap it in a class, and when that class goes out of scope the bus is released. No forgotten cleanup, no missing `free()`, no partially-initialized peripheral left in a bad state. This pattern is extremely valuable in embedded code where resource leaks are subtle and debugging them is painful.

**`constexpr` for compile-time computation**: Lookup tables, CRC tables, bitmask calculations, register configuration values—all of these can be computed at compile time in C++11 and later. The CPU does less work at runtime, and the values end up in flash rather than being computed each time.

**Strong typing for hardware abstractions**: GPIO pin configurations, peripheral addresses, interrupt priorities—using strong types instead of bare integers catches entire categories of bugs at compile time. Passing a DMA channel number where an interrupt priority is expected becomes a compiler error rather than a runtime fault.

---

### The Mistakes That Actually Cost You

**Exception handling**: Enabling C++ exceptions on an embedded target adds a non-trivial overhead to every function that might throw—the compiler generates unwinding tables, and the runtime library adds several kilobytes of code. On a Cortex-M0 with 32KB flash, that's unacceptable. The standard practice is to compile with `-fno-exceptions` and either avoid exception-throwing code or replace it with error-code-based APIs. The problem is that many developers do this reflexively without thinking through the implications: standard library functions that would throw `std::bad_alloc` or `std::out_of_range` now have undefined behavior instead of a recoverable error. Know what you're suppressing.

```cpp
// Don't use std::vector::at() with -fno-exceptions — it calls terminate() on out-of-bounds
// Use operator[] and range-check yourself, or use a bounded container
template<typename T, size_t N>
class BoundedArray {
    T data_[N];
    size_t size_ = 0;
public:
    bool push(const T& val) {
        if (size_ >= N) return false;
        data_[size_++] = val;
        return true;
    }
    T& operator[](size_t i) { return data_[i]; }
    size_t size() const { return size_; }
};
```

**RTTI (Run-Time Type Information)**: `dynamic_cast` and `typeid` require the compiler to embed type information for every polymorphic class. This bloats the binary significantly. Compile with `-fno-rtti`. If you need polymorphism, use static polymorphism through templates and CRTP (see below), or accept the cost of vtables but avoid RTTI on top of it.

**Dynamic memory allocation**: `new` and `delete` on an embedded target without an RTOS heap are immediate problems—they're non-deterministic, they fragment memory over time, and on bare-metal targets without an OS, the default `new` implementation may panic or return null. The right approach is to avoid dynamic allocation entirely at runtime. Use static storage, stack allocation, or a pool allocator with fixed-size blocks. If you need dynamic allocation, use it only at initialization time, not in the main loop.

```cpp
// Dangerous: heap allocation in a tight loop
void sensor_loop() {
    while (true) {
        auto* buf = new uint8_t[64]; // Don't do this
        read_sensor(buf);
        process(buf);
        delete[] buf;                // Memory fragmentation over time
    }
}

// Better: stack allocation
void sensor_loop() {
    while (true) {
        uint8_t buf[64];
        read_sensor(buf);
        process(buf);
    }
}
```

**Virtual function overhead**: Calling a virtual function adds one level of indirection through the vtable pointer. On modern ARM Cortex-M cores, this is usually one or two extra cycles—often acceptable. The real problem is the vtable itself: every class with virtual functions carries a pointer-sized overhead per instance, and the vtable lives in flash. For a sensor abstraction with five or six virtual methods instantiated on three different sensors, the overhead is negligible. For a design with dozens of small polymorphic objects, it adds up.

---

### Static Polymorphism with CRTP

The Curiously Recurring Template Pattern lets you get the benefits of polymorphism—code that works with any compatible type—without vtable overhead:

```cpp
template<typename Derived>
class SensorBase {
public:
    float read() {
        return static_cast<Derived*>(this)->read_impl();
    }
    bool is_ready() {
        return static_cast<Derived*>(this)->is_ready_impl();
    }
};

class TemperatureSensor : public SensorBase<TemperatureSensor> {
public:
    float read_impl() {
        return read_adc() * SCALE_FACTOR + OFFSET;
    }
    bool is_ready_impl() {
        return adc_conversion_complete();
    }
};

// Works for any sensor type, resolved entirely at compile time
template<typename Sensor>
void log_sensor_reading(Sensor& s) {
    if (s.is_ready()) {
        float val = s.read();
        uart_printf("%.2f\r\n", val);
    }
}
```

No vtable, no indirection, full inlining if the compiler decides to. The tradeoff is that CRTP is more complex to read and you can't store different sensor types in the same array without type erasure. But for embedded code where performance and predictability matter more than runtime flexibility, it's often the right choice.

---

### `constexpr` for Embedded Configuration

One of the genuinely great things C++14 and later brought to embedded is a powerful `constexpr`. Register bitmask tables, CRC tables, and protocol lookup tables that previously required either a Python script to generate or a handwritten const array can now be generated inline:

```cpp
// CRC-8 table generated entirely at compile time
constexpr auto make_crc8_table() {
    std::array<uint8_t, 256> table{};
    for (int i = 0; i < 256; ++i) {
        uint8_t crc = static_cast<uint8_t>(i);
        for (int j = 0; j < 8; ++j) {
            crc = (crc & 0x80) ? (crc << 1) ^ 0x07 : (crc << 1);
        }
        table[i] = crc;
    }
    return table;
}

constexpr auto CRC8_TABLE = make_crc8_table();

uint8_t compute_crc8(const uint8_t* data, size_t len) {
    uint8_t crc = 0xFF;
    for (size_t i = 0; i < len; ++i) {
        crc = CRC8_TABLE[crc ^ data[i]];
    }
    return crc;
}
```

The `CRC8_TABLE` array is computed by the compiler and placed in flash. At runtime it's a simple table lookup—no computation, no RAM usage.

---

### MISRA C++ and Coding Standards

MISRA C++ 2023 (the latest revision) provides a set of guidelines specifically aimed at making C++ safer for safety-critical embedded use. Following MISRA doesn't make C++ as safe as Rust's compile-time guarantees, but it eliminates many of the most dangerous patterns: unchecked pointer arithmetic, implicit conversions that lose precision, using `reinterpret_cast` without justification.

For non-safety-critical embedded work, MISRA is often too restrictive. But cherry-picking the more important rules—ban `goto`, never use uninitialized variables, always initialize members in the constructor initializer list, don't use variable-length arrays—gives you most of the safety benefit at much lower cost.

Static analysis tools like clang-tidy, cppcheck, and PC-lint can enforce many MISRA rules automatically as part of your CI pipeline, which is far more practical than code review alone.

---

### C++ or Rust for a New Embedded Project?

This repo has been predominantly about Rust, so it's fair to address the comparison directly. For a new project with a team that knows both languages equally well, I'd lean toward Rust for bare-metal work—the ownership system genuinely eliminates classes of bugs that C++ merely makes it easier to avoid. But the honest answer is that it depends on:

- **Team knowledge**: A team expert in modern C++ will outperform a team learning Rust on the first several projects
- **Ecosystem**: Some hardware vendors provide C++ SDKs with no Rust equivalent; fighting the SDK costs more than the language benefits
- **Toolchain stability**: Rust's embedded toolchain has matured significantly, but C++ toolchain maturity is still hard to match for niche targets
- **Certification**: For safety-critical systems (automotive, medical), MISRA C++ has a longer track record than anything available for Rust today

C++ is not a language you should be embarrassed to use in 2026. It's powerful, it's mature, and used correctly—with exceptions and RTTI disabled, dynamic allocation banned at runtime, and the type system working for you rather than against you—it produces firmware that's safe, efficient, and maintainable. Just know the pitfalls before they find you.
