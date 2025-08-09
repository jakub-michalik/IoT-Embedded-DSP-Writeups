**Rust on nRF52: BLE, Low-Power Modes, and the Embassy Async Runtime**

Nordic Semiconductor's nRF52 series has been the go-to hardware for Bluetooth Low Energy IoT devices for years. The combination of a capable Cortex-M4F core, integrated BLE radio, hardware crypto accelerators, and genuinely excellent low-power modes makes it a strong choice for battery-operated sensor nodes, wearables, and smart home devices. The Rust ecosystem around nRF52 has grown to the point where Embassy—the async embedded Rust framework—provides arguably the most ergonomic BLE development experience available on this hardware.

---

### Why Embassy for nRF52

Embassy started as a project targeting nRF52 specifically, and that heritage shows. The `embassy-nrf` crate provides async drivers for nearly every nRF52 peripheral: SPIM, TWIM, UART, PWM, SAADC, GPIOTE, PPI, RTC, and the RADIO itself. The SoftDevice integration is available for those who need Nordic's certified BLE stack, while `nrf-softdevice` wraps it in a Rust-friendly async API.

Alternatively, the pure-Rust `trouble` crate (formerly `bt-hci` based) is gaining traction as a fully open BLE host stack that doesn't depend on the SoftDevice blob. For new projects without strict certification requirements, it's worth considering.

The key advantage of Embassy's async model for BLE devices: your application can have multiple concurrent tasks—one handling sensor readings, one managing BLE connections, one handling button presses—without the complexity of a traditional RTOS scheduler. The async executor handles task switching cooperatively, with very low overhead:

```rust
#[embassy_executor::task]
async fn sensor_task(mut spi: Spim<'static, SPIM0>, mut cs: Output<'static>) {
    loop {
        cs.set_low();
        let data = read_sensor(&mut spi).await;
        cs.set_high();
        SENSOR_CHANNEL.send(data).await;
        Timer::after_millis(100).await;
    }
}

#[embassy_executor::task]
async fn ble_task(sd: &'static Softdevice) {
    loop {
        let conn = advertise_connectable(sd).await.unwrap();
        let _ = ble_run(&conn).await;
    }
}
```

Both tasks run concurrently on a single thread. When `Timer::after_millis(100).await` suspends the sensor task, the executor runs the BLE task. When the BLE stack is waiting for a connection, the sensor task runs. No explicit context switching, no mutexes around a shared scheduler state.

---

### BLE Advertising and GATT Services

A typical BLE peripheral role implementation with nrf-softdevice involves advertising a device name and exposing GATT characteristics:

```rust
use nrf_softdevice::ble::{gatt_server, peripheral};

#[nrf_softdevice::gatt_server]
struct Server {
    sensor: SensorService,
}

#[nrf_softdevice::gatt_service(uuid = "180F")]  // Battery Service
struct SensorService {
    #[characteristic(uuid = "2A19", read, notify)]
    temperature: i16,
}

async fn run_ble(sd: &'static Softdevice, server: &Server) {
    let adv_data = build_advertisement_data();
    loop {
        let conn = peripheral::advertise_connectable(
            sd,
            peripheral::ConnectableAdvertisement::ScannableUndirected {
                adv_data: &adv_data,
                scan_data: &[],
            },
            &Default::default(),
        ).await.unwrap();

        gatt_server::run(&conn, server, |event| {
            // Handle GATT events
        }).await;
    }
}
```

The `#[nrf_softdevice::gatt_server]` macro generates the boilerplate for service registration and characteristic handling. You define your service structure in Rust and the macro handles the underlying attribute table registration with the SoftDevice.

---

### Power Management: Sleep States and Current Profiles

The nRF52840 has well-documented power modes. In System Off (deepest sleep), current consumption drops to ~0.5µA with RAM retention disabled, or ~1.6µA with full RAM retention. System On sleep with the CPU in WFE and most peripherals clock-gated is typically in the 1–5µA range depending on what's left active.

For a typical BLE sensor node doing advertising every second and sleeping between events:

| Phase | Duration | Current |
|-------|----------|---------|
| CPU active + radio TX (advertising) | ~4ms | ~8mA |
| CPU active + sensor read | ~2ms | ~4mA |
| CPU sleep (System On, RTC running) | ~994ms | ~2µA |

Weighted average: ≈ 0.085mA = 85µA. On a 500mAh coin cell, that's roughly 245 days. Not great but very typical for connected advertising devices.

In Embassy, entering sleep automatically happens when all tasks are suspended. The executor calls WFE before each poll cycle when no tasks are ready, and the SoftDevice manages the radio sleep and wakeup timing. You don't need to manage sleep explicitly—you just await timers and events:

```rust
#[embassy_executor::task]
async fn main_task(mut rtc: Rtc<'static, RTC0>) {
    loop {
        read_and_transmit_sensor_data().await;
        Timer::after_secs(1).await; // CPU sleeps here
    }
}
```

To push current consumption lower, disable peripherals you're not using:

```rust
// Disable unused GPIO ports (nRF52 specific)
let p = embassy_nrf::init(Default::default());
// Configure unused pins as inputs with no pull (lowest leakage)
let _unused1 = Input::new(p.P0_02, Pull::None);
let _unused2 = Input::new(p.P0_03, Pull::None);
```

Floating GPIO pins can draw significant leakage current. Either pull them or configure them as disconnected.

---

### SAADC for Battery Voltage Monitoring

Monitoring battery voltage is essential for BLE devices. The nRF52 has a built-in SAADC (Successive Approximation ADC) with an internal reference, useful for measuring the supply voltage through the VDD input:

```rust
use embassy_nrf::saadc::{self, Saadc};

async fn read_battery_voltage(saadc: &mut Saadc<'_, 1>) -> u16 {
    let mut buf = [0i16; 1];
    saadc.sample(&mut buf).await;

    // Convert ADC reading to millivolts
    // With VDD/4 input and 3.6V reference: (reading / 4096) * 3600 * 4
    let mv = (buf[0] as u32 * 3600 * 4) / 4096;
    mv as u16
}
```

Report this as the BLE Battery Level characteristic (0x2A19) so connected devices can display battery status.

---

### Nordic SDK vs Pure Rust Tradeoffs

The nrf-softdevice approach uses Nordic's binary SoftDevice blob for the BLE stack. This has real advantages: Nordic's BLE stack is mature, certified, and handles timing-critical radio operations in a proven way. The downside is that the SoftDevice occupies a fixed region of flash (typically 128–256KB depending on the variant) and constrains your application's flash and RAM usage.

The pure-Rust alternative (`trouble` + `nrf-hal` or Embassy's built-in radio support) gives you full control and no binary blob, but you're taking on responsibility for a BLE stack that isn't certified for medical or safety-critical applications. For most IoT devices, this is fine.

A practical guideline: if you need BLE certification, use nrf-softdevice. If you're building a product where certification isn't required and you want maximum control and code transparency, the pure-Rust path is compelling.

---

### Summary

The nRF52 family paired with Embassy and the nrf-softdevice (or pure-Rust BLE) ecosystem is one of the most capable platforms for battery-powered BLE devices in Rust today. The async model maps naturally to the event-driven nature of BLE connections and sensor polling cycles. The low-power hardware of the nRF52 series, combined with Embassy's cooperative multitasking that naturally allows deep sleep between events, enables well-designed devices to run for months on a small battery without complex power management code.
