**Thread and Matter: The New IoT Connectivity Stack and Where Rust Fits**

For a long time, IoT connectivity was a fragmented mess. Zigbee, Z-Wave, Bluetooth Mesh, proprietary 2.4GHz protocols, and dozens of cloud-vendor lock-in solutions all competed, and none of them talked to each other. The combination of Thread and Matter is the most serious attempt yet to fix that—and it's gaining enough industry traction that it's worth understanding deeply, whether you're building devices, gateways, or the infrastructure that connects them.

---

### Thread: The Mesh Networking Layer

Thread is an IPv6-based mesh networking protocol designed for low-power IoT devices. It runs at the 802.15.4 physical and MAC layer (the same radio layer as Zigbee) but replaces the Zigbee application stack with an IP-native approach. Every Thread device gets an IPv6 address. Devices can talk to each other and to the internet using standard IP protocols—no application-layer translation required.

The key architectural properties:

**Self-healing mesh**: Thread nodes forward packets for each other. If a node disappears, the network reroutes around it automatically. There's no single point of failure.

**Border Router**: One or more border routers connect the Thread mesh to a standard IP network (typically Wi-Fi or Ethernet). The border router advertises routes and provides DNS services to Thread nodes.

**Device roles**: Full Thread devices (FTDs) participate in routing and can be border routers. Minimal Thread Devices (MTDs) are sleepy end devices that only talk to their parent—they conserve power by sleeping most of the time.

**6LoWPAN**: IPv6 packets are compressed using the 6LoWPAN header compression scheme to fit within the small frame sizes of 802.15.4. The details are handled by the Thread stack transparently.

OpenThread is the open-source Thread stack maintained by Google, used in virtually all commercial Thread implementations including Matter. It runs on Cortex-M33 or larger targets and is the natural starting point for any Thread project.

---

### Matter: The Application Layer

If Thread handles the network, Matter handles the application: device types, data models, commissioning, and interoperability between manufacturers. A Matter-compliant lightbulb should work with any Matter controller—Apple Home, Google Home, Amazon Alexa, Samsung SmartThings—without any vendor-specific configuration.

Matter runs over IP, which means it can run over Thread (for constrained devices), Wi-Fi (for mains-powered devices), and Ethernet. The protocol uses a binary encoding called TLV (Type-Length-Value) for messages, CoAP-like request/response semantics, and a device-type data model that defines what attributes and commands a lightbulb, thermostat, door lock, or sensor should expose.

**Commissioning** is the process of adding a new device to a Matter fabric. It uses Bluetooth LE as the commissioning transport: a new device advertises over BLE, the commissioner (typically a phone or hub) scans for it, performs a PAKE (Password-Authenticated Key Exchange) ceremony using a QR code or manual pairing code, and provisions the device with network credentials and a fabric identity. After commissioning, the device operates over its primary transport (Thread or Wi-Fi).

Matter 1.3 (released in May 2024) added energy management device types and expanded the sensor ecosystem. Matter 1.4 (October 2024) introduced enhanced multi-admin scenarios and batch commissioning improvements, which are relevant for commercial deployments with large numbers of devices.

---

### The Hardware Combination: nRF52 and nRF54 for Thread+Matter

Nordic's nRF52840 is the most widely deployed Thread+Matter chip. It has:
- 2.4GHz radio supporting IEEE 802.15.4 (Thread) and BLE 5.0 (for commissioning)
- 1MB flash + 256KB RAM (enough for OpenThread + Matter stack)
- Cortex-M4F core at 64 MHz

Nordic's nRF Connect SDK provides the full Thread+Matter application framework, which bundles OpenThread, the Matter SDK, and a Zephyr RTOS base. This is a large and complex software stack.

The nRF54L15, Nordic's newer chip in the nRF54 family, improves on the nRF52840 in several ways relevant to Matter devices: lower sleep current (discussed more in the next article), Cortex-M33 with TrustZone, and PSA Certified security level. For devices that need to pass Matter's security requirements, the hardware security features of the nRF54L15 provide a better foundation.

---

### OpenThread on Bare Metal Rust

Running OpenThread on a Rust-based bare-metal project requires an FFI layer. OpenThread is a C/C++ library and exposes a C API. A minimal integration sketch:

```rust
extern "C" {
    fn otInstanceInitSingle() -> *mut OtInstance;
    fn otIp6SetEnabled(instance: *mut OtInstance, enabled: bool) -> OtError;
    fn otThreadSetEnabled(instance: *mut OtInstance, enabled: bool) -> OtError;
    fn otTaskletsProcess(instance: *mut OtInstance);
    fn otSysProcessDrivers(instance: *mut OtInstance);
}

fn start_thread(instance: *mut OtInstance) {
    unsafe {
        otIp6SetEnabled(instance, true);
        otThreadSetEnabled(instance, true);
    }
}

fn main_loop(instance: *mut OtInstance) {
    loop {
        unsafe {
            otTaskletsProcess(instance);
            otSysProcessDrivers(instance);
        }
        // Handle application events
    }
}
```

In practice, most Thread+Matter embedded projects use Zephyr RTOS as the base (which OpenThread integrates with natively) rather than bare Rust. Zephyr's Rust support is improving, with the `zephyr-sys` crate providing bindings, but it's still early compared to Embassy for direct bare-metal development. For Thread specifically, the established path remains Zephyr + C/C++ for production work, with Rust components added at the application layer.

---

### What Rust Brings to a Thread/Matter System

Even if the lower layers (OpenThread, Matter SDK) are C/C++, there are meaningful places to apply Rust in a Thread/Matter stack:

**Application logic**: The business logic above the Matter data model—how your device responds to commands, manages state, controls actuators—can be written in Rust called via FFI from the C framework. This is the part most likely to have logic bugs, and Rust's type system helps.

**Gateways and border routers**: A Thread border router running on Linux (Raspberry Pi, OpenWrt router) is entirely fair game for Rust. The `openthread-ffi` bindings and network stack integration can be written in pure Rust, with OpenThread running as a library.

**Testing infrastructure**: Parsing and validating Matter TLV messages, simulating device behavior for integration testing, writing conformance test tools—all of this can be done in Rust on a host machine.

---

### The Bigger Picture

Thread and Matter represent a genuine maturation of the IoT connectivity landscape. The protocol complexity is real—commissioning flows, fabric management, multi-admin scenarios, and the interplay between Thread network topology and Matter fabric identities take time to understand deeply. But for device builders, the payoff is significant: devices built to the Matter specification work with any compliant ecosystem out of the box, which is increasingly what end customers expect.

For Rust developers specifically, the current situation is that the core Thread and Matter stacks are C/C++, but the ecosystem is moving toward better Rust integration. The Zephyr project's Rust support is improving, Embassy's radio support for 802.15.4 is maturing, and pure-Rust Matter implementations are in development. It's reasonable to expect that within a couple of years, a full Thread+Matter device built primarily in Rust will be a practical option rather than a research project.
