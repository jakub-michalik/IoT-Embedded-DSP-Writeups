**CAN Bus with STM32 in Rust: Industrial Communication for Embedded Systems**

CAN (Controller Area Network) is everywhere in industrial automation, automotive electronics, robotics, and building control systems—and for good reason. It was designed for exactly the environments where things go wrong: high electrical noise, multi-master bus arbitration, multi-kilometer cable runs, and the need for deterministic communication without a central controller. STM32 microcontrollers have excellent hardware CAN support, with most of the mid-range and high-end variants including one or two CAN controllers. Rust support for CAN on STM32, via the `bxcan` crate and the `stm32-bxcan` backend, is mature enough for real projects.

---

### CAN Basics Worth Knowing

CAN uses differential signaling on a twisted pair. Every node on the bus can transmit; arbitration happens automatically—the node that tries to send a recessive bit (logic 1) while another sends a dominant bit (logic 0) loses arbitration and backs off. This means higher-priority messages (lower ID values) always win bus access without any explicit coordination.

A CAN frame has:
- **ID**: 11-bit (standard) or 29-bit (extended)
- **Data**: 0 to 8 bytes
- **DLC**: Data Length Code (how many bytes are in this frame)
- **CRC**: Hardware-computed, transparent to the application
- **ACK**: Every receiver acknowledges; the transmitter knows if no one heard

CAN FD (Flexible Data-rate) extends this to 64 bytes per frame and allows the data phase to run at higher bit rates than the arbitration phase. STM32G0B1, H7, G4, and several other variants include FDCAN (the standard hardware CAN FD implementation). For new designs, FDCAN is worth using even if you don't need the higher data rate—the improved error handling and the future bandwidth headroom are valuable.

---

### Hardware Setup on STM32

Most STM32 CAN peripherals need an external transceiver chip to interface with the physical bus. The most common is the TJA1050 or its derivatives. The connection is straightforward:

- STM32 CAN_TX → TJA1050 TXD
- STM32 CAN_RX → TJA1050 RXD
- TJA1050 CANH/CANL → bus (with 120Ω termination at each end of the bus)

On STM32H743, the FDCAN1 peripheral is on PA11/PA12 or PB8/PB9 (alternate function 9). The HAL and bxcan crate handle pin configuration, but you still need to configure the GPIO alternate function before initializing the CAN peripheral.

---

### Using bxcan in Rust

The `bxcan` crate provides a safe Rust API for the bxCAN peripheral found on most STM32F and STM32L devices. It's well-designed: frame types are strongly typed, filter bank configuration is handled at initialization, and the API catches common mistakes (like trying to transmit before enabling the peripheral) at compile time.

A minimal setup for STM32F4 with the `stm32f4xx-hal` crate:

```rust
use bxcan::{filter::Mask32, Frame, Id, StandardId};
use stm32f4xx_hal::{can::Can, pac, prelude::*};

fn setup_can(dp: pac::Peripherals, clocks: &Clocks) -> bxcan::Can<Can<pac::CAN1>> {
    let gpioa = dp.GPIOA.split();
    let rx = gpioa.pa11.into_alternate::<9>();
    let tx = gpioa.pa12.into_alternate::<9>();

    let can = dp.CAN1.can((tx, rx));

    let mut can = bxcan::Can::builder(can)
        .set_bit_timing(0x001c0003) // 500 kbit/s at 42 MHz APB1
        .leave_disabled();

    // Configure filters: accept all frames with standard ID
    can.modify_filters()
        .enable_bank(0, Mask32::accept_all());

    can.enable_non_blocking().unwrap()
}
```

The bit timing value `0x001c0003` encodes prescaler, time segment 1, and time segment 2. For production use, calculate this precisely with the CAN bit timing calculator tools rather than guessing. The baud rate depends on your APB1 clock frequency, which comes from your RCC configuration.

---

### Transmitting and Receiving Frames

With the CAN interface initialized, sending a frame is straightforward:

```rust
fn send_sensor_data(can: &mut bxcan::Can<impl bxcan::Instance>, value: f32) {
    let id = StandardId::new(0x101).unwrap(); // Sensor data ID
    let bytes = value.to_be_bytes();
    let frame = Frame::new_data(Id::Standard(id), bytes);

    block!(can.transmit(&frame)).unwrap();
}
```

Receiving:

```rust
fn receive_loop(can: &mut bxcan::Can<impl bxcan::Instance>) {
    loop {
        match block!(can.receive()) {
            Ok(frame) => {
                handle_frame(&frame);
            }
            Err(bxcan::OverrunError) => {
                // RX FIFO overrun — some frames were lost
                defmt::warn!("CAN RX overrun");
            }
        }
    }
}

fn handle_frame(frame: &bxcan::Frame) {
    match frame.id() {
        Id::Standard(id) if id.as_raw() == 0x100 => {
            // Command from master
            if let Some(data) = frame.data() {
                process_command(data);
            }
        }
        _ => {} // Ignore other IDs
    }
}
```

For applications that need interrupt-driven reception rather than blocking polling, the bxcan crate works with the HAL's interrupt handler infrastructure—you handle the USB_LP_CAN_RX0 interrupt (on F4), read from the FIFO in the handler, and pass frames to application code via a queue.

---

### FDCAN on STM32G4 and H7

The newer FDCAN peripheral (on STM32G0B1, G4, H7, and others) has a somewhat different API. The `fdcan` crate provides Rust bindings:

```rust
use fdcan::{config::*, *};
use stm32h7xx_hal::can::Can;

let fdcan_config = FdCanConfig::default()
    .set_nominal_bit_timing(NominalBitTiming {
        prescaler: NonZeroU16::new(1).unwrap(),
        seg1: NonZeroU8::new(13).unwrap(),
        seg2: NonZeroU8::new(2).unwrap(),
        sync_jump_width: NonZeroU8::new(1).unwrap(),
    })
    .set_data_bit_timing(DataBitTiming {  // CAN FD data phase
        prescaler: NonZeroU8::new(1).unwrap(),
        seg1: NonZeroU8::new(3).unwrap(),
        seg2: NonZeroU8::new(1).unwrap(),
        sync_jump_width: NonZeroU8::new(1).unwrap(),
    });
```

FDCAN also has a message RAM that needs to be configured—you specify how many TX and RX FIFO entries to allocate. On the H7, the FDCAN message RAM is in a dedicated SRAM region; getting the linker script to place it correctly is one of the common stumbling blocks.

---

### CANopen and Application Protocols

Raw CAN frames are rarely used directly in industrial systems—application protocols like CANopen and J1939 define how to use CAN IDs and data fields for specific purposes. CANopen, widely used in industrial automation and robotics, defines device profiles, network management, and a standardized way to expose device parameters (the Object Dictionary).

There's no mature pure-Rust CANopen stack yet, but the foundation exists. Writing a minimal CANopen node (NMT state machine, heartbeat, a few PDOs for I/O) in Rust on top of bxcan is a reasonable project. The protocol is well-specified in the CiA (CAN in Automation) standards.

---

### Why STM32 for CAN

A few reasons STM32 dominates CAN in embedded projects:

**Hardware integration**: Most STM32 variants have CAN controllers with good filter banks (up to 28 on some devices). No external CAN controller chip needed, just the transceiver.

**Development ecosystem**: The ST toolchain, HAL examples, and community documentation for CAN on STM32 are extensive. Finding examples and debugging help is straightforward.

**FDCAN on the newer series**: The STM32G4 series (Cortex-M4 at 170 MHz) is particularly popular for motor control and industrial automation, and includes dual FDCAN. For designs that need both high-speed control loops and robust CAN communication, the G4 is a strong choice.

**Voltage range**: Many industrial applications run at 5V. STM32 devices with 5V-tolerant I/O can interface directly with many industrial sensors and actuators without level shifters.

---

### Summary

CAN bus remains the standard for industrial embedded communication, and STM32's hardware support for both classic CAN (via bxCAN) and CAN FD (via FDCAN) is excellent. The Rust ecosystem—`bxcan` for classic CAN, `fdcan` for newer devices—provides clean, type-safe APIs that prevent common CAN configuration mistakes. For new industrial designs, the STM32G4 or H7 series with FDCAN is the natural platform, and the Rust HAL support is mature enough for production use.
