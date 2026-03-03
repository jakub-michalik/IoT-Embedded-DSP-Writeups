**IoT Platforms in Practice: ThingsBoard, Data Pipelines, and Connecting Embedded Rust to the Cloud**

Getting data off an embedded device and into a place where it can be visualized, alerted on, and acted upon is the second half of any IoT project. The firmware is one side of the equation; the platform infrastructure is the other. ThingsBoard is one of the most capable open-source IoT platforms available—it handles device management, telemetry ingestion, rule engines, dashboards, and integrations, and you can self-host it on your own infrastructure. This article covers how to connect an embedded Rust device to ThingsBoard, what the data model looks like, and how to build a practical end-to-end pipeline from sensor to dashboard.

---

### Why ThingsBoard

ThingsBoard positions itself between simple MQTT brokers and heavyweight enterprise IoT platforms. It's genuinely powerful: the rule chain engine can do complex event processing, the widget library is extensive, and the REST API is comprehensive. The Community Edition is open-source (Apache 2.0) and runs on a single server for smaller deployments. The Professional Edition adds multi-tenancy, white-labeling, and integrations with enterprise systems.

For an embedded engineer building a sensor network, ThingsBoard handles the things you don't want to build yourself: time-series storage with configurable retention, user authentication and access control, alarm management, and a dashboard builder that non-engineers can use. The protocol support (MQTT, HTTP, CoAP, LwM2M) covers virtually any embedded device.

---

### The ThingsBoard Data Model

Understanding the data model before you write firmware is worth the time. ThingsBoard organizes data around a few key concepts:

**Devices**: Represent individual physical devices. Each device has a unique access token (for MQTT/HTTP authentication).

**Telemetry**: Time-series key-value pairs. A temperature sensor sends `{"temperature": 23.4, "humidity": 61}` and ThingsBoard stores each value with a timestamp. You can query historical telemetry, aggregate it, and visualize it.

**Attributes**: Static or semi-static metadata. Server attributes are set by the platform (firmware version, configuration), client attributes are set by the device (battery level, signal strength), and shared attributes flow both ways. The device can subscribe to shared attribute changes to receive configuration updates from the server.

**Telemetry vs attributes**: Telemetry is append-only time-series data. Attributes are the current state—when you update a client attribute, it replaces the previous value rather than adding a new time-series entry.

---

### MQTT Connectivity from Embedded Rust

For devices with Wi-Fi or Ethernet, MQTT over TCP is the primary connectivity path. The `rust-mqtt` crate or `mqttrust` provide MQTT client implementations suitable for embedded use. For an ESP32 or similar Wi-Fi-capable device running Embassy or a thin RTOS:

```rust
use mqttrust::{Mqtt, PublishRequest, QoS};

async fn connect_and_publish(
    client: &mut impl Mqtt,
    device_token: &str,
    temperature: f32,
    humidity: f32,
) {
    // ThingsBoard telemetry topic
    let topic = "v1/devices/me/telemetry";

    // ThingsBoard expects JSON
    let payload = format!(
        r#"{{"temperature":{:.1},"humidity":{:.1}}}"#,
        temperature, humidity
    );

    client.publish(PublishRequest {
        topic_name: topic,
        payload: payload.as_bytes(),
        qos: QoS::AtLeastOnce,
        retain: false,
    }).await.unwrap();
}
```

For devices without dynamic memory allocation (`no_std` without an allocator), you'll need to format the JSON into a fixed-size buffer:

```rust
use core::fmt::Write;

fn format_telemetry(
    buf: &mut heapless::String<128>,
    temperature: f32,
    humidity: f32,
) {
    buf.clear();
    write!(buf, r#"{{"temperature":{:.1},"humidity":{:.1}}}"#,
           temperature, humidity).unwrap();
}
```

The `heapless` crate provides stack-allocated String and Vec types, essential for MQTT payloads in no_std environments.

---

### Receiving Shared Attribute Updates

ThingsBoard's shared attributes mechanism is how you push configuration to devices. A device subscribes to the attribute topic and receives updates when you change an attribute from the server side:

```rust
// Subscribe to shared attribute updates
let sub_topic = "v1/devices/me/attributes";
client.subscribe(sub_topic, QoS::AtLeastOnce).await.unwrap();

// In receive loop:
async fn handle_message(topic: &str, payload: &[u8]) {
    if topic == "v1/devices/me/attributes" {
        if let Ok(text) = core::str::from_utf8(payload) {
            // Parse JSON to extract configuration values
            // e.g., {"sampleInterval": 5000, "alertThreshold": 80.0}
            update_config_from_json(text);
        }
    }
}
```

This creates a bi-directional communication channel: the device sends telemetry up, the platform sends configuration down. Combined with ThingsBoard's rule engine, you can implement complex logic like "if temperature exceeds threshold for 5 minutes, update the device's polling interval to 10 seconds" without touching the firmware.

---

### Building a Rule Chain for Alerting

ThingsBoard's rule engine processes telemetry through a directed graph of nodes. A typical alerting rule chain for a temperature sensor:

1. **Message Type Switch** → routes telemetry messages to the processing branch
2. **Originator Attributes** → enriches the message with device metadata (location, alert threshold)
3. **Script filter** → evaluates `msg.temperature > metadata.alertThreshold`
4. **Create Alarm** (if filter passes) → creates a HIGH_TEMPERATURE alarm
5. **Clear Alarm** (if filter fails) → clears the alarm when temperature drops
6. **Send Email / Push Notification** → triggered by alarm create/update events

The rule engine is configured through the web UI (no coding required), but for complex scenarios you can write JavaScript transformation nodes. The combination gives you the flexibility to implement sophisticated event processing without building a custom backend.

---

### CoAP for Constrained Devices

For devices on Thread networks or other low-power protocols, CoAP (Constrained Application Protocol) is more appropriate than MQTT. ThingsBoard supports CoAP natively with the same topic structure:

```
coap://thingsboard.example.com/api/v1/{ACCESS_TOKEN}/telemetry
```

The `coap-lite` crate provides a CoAP implementation for no_std Rust, suitable for devices running on Thread/IPv6. A Thread end-device can POST telemetry directly to the ThingsBoard CoAP gateway:

```rust
use coap_lite::{CoapRequest, RequestType};

fn send_coap_telemetry(
    socket: &mut UdpSocket,
    server_addr: core::net::SocketAddrV6,
    token: &str,
    payload: &[u8],
) {
    let mut request = CoapRequest::new();
    request.set_method(RequestType::Post);
    request.set_path(&format!("/api/v1/{}/telemetry", token));
    request.message.payload = payload.to_vec();

    let packet = request.message.to_bytes().unwrap();
    socket.send_to(&packet, server_addr).unwrap();
}
```

---

### Self-Hosted vs Cloud ThingsBoard

For development and small-scale production, self-hosting ThingsBoard on a VPS or local server is the most practical path. A modest VPS (2 vCPU, 4GB RAM) running Docker handles hundreds of devices comfortably. The official Docker Compose configuration makes initial deployment straightforward.

For larger scale or when you don't want to manage infrastructure, ThingsBoard Cloud provides the same feature set as a managed service. The device-side code is identical—same MQTT topics, same JSON format, same rule engine.

One advantage of self-hosting: you can run ThingsBoard on a local network, keeping all telemetry data on-premises. This is relevant for industrial deployments with data residency requirements or network-isolated production environments.

---

### Other Platforms Worth Knowing

ThingsBoard isn't the only option:

**InfluxDB + Grafana**: For pure time-series monitoring without device management, this combination is hard to beat. InfluxDB stores time-series data efficiently, Grafana provides excellent visualization, and the Flux query language is expressive. From embedded Rust, you'd write to the InfluxDB line protocol over HTTP. Less opinionated than ThingsBoard but more work to assemble a complete solution.

**Home Assistant**: The de facto standard for smart home IoT, with MQTT and ESPHome integration. If your devices target the consumer smart home market, Home Assistant compatibility is increasingly expected.

**AWS IoT Core / Azure IoT Hub**: For enterprises already on those cloud platforms. The embedded SDKs are mature. Pricing can be a concern at scale.

For most embedded engineers building their own IoT infrastructure, ThingsBoard + MQTT provides the best balance of capability, operational simplicity, and open-source flexibility.

---

### Summary

The platform side of IoT is as important as the device side, and ThingsBoard provides a complete solution—telemetry storage, rule-based alerting, dashboards, and device management—that a small team can deploy and maintain. Connecting embedded Rust devices via MQTT or CoAP is straightforward with the available crates, and the bi-directional attribute mechanism gives you a clean channel for pushing configuration to devices without bespoke protocols. Building this infrastructure early in a project, rather than after the firmware is mature, pays off as the system scales.
