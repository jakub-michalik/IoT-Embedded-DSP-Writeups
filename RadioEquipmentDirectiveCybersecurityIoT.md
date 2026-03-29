**Radio Equipment Directive: The New Cybersecurity Requirements for IoT Devices**

The Radio Equipment Directive (RED) has been regulating wireless devices in Europe since 2014, but until recently it was primarily about radio spectrum management—ensuring your device doesn't interfere with other radio equipment, meets EMC requirements, and uses the spectrum efficiently. That changed with the delegated acts under Articles 3.3(d), 3.3(e), and 3.3(f), which add mandatory cybersecurity, privacy, and fraud protection requirements to any radio equipment sold in the EU. If your IoT device uses Wi-Fi, Bluetooth, Zigbee, LoRa, cellular, Thread, or any other radio technology, these new requirements apply to you.

This is a big deal for IoT manufacturers, and the timing is important. The delegated acts were adopted in 2022, with a transition period originally set for August 2025. The interplay with the Cyber Resilience Act has shifted some timelines, but the requirements themselves are real, and compliance planning needs to happen now.

---

### What the Delegated Acts Require

The three delegated acts add new "essential requirements" to the RED:

**Article 3.3(d) — Network Protection**: Radio equipment must not harm the network or its functioning, nor misuse network resources. In practice, this means your device must implement safeguards against being used in DDoS attacks, must not allow unauthorized network access, and must protect the integrity of network communications.

**Article 3.3(e) — Privacy and Personal Data Protection**: Radio equipment that processes personal data must include safeguards for privacy. This overlaps with GDPR but adds a product-level requirement—the device itself must have technical features that protect personal data, not just the manufacturer's backend services.

**Article 3.3(f) — Fraud Protection**: Radio equipment must support features that ensure protection from fraud. This applies to devices that handle payments, access control, or other financial transactions, but the scope is interpreted broadly to include any device that could be exploited for fraudulent purposes.

For most IoT devices, Article 3.3(d) is the one with the broadest impact. The network protection requirement translates to a set of concrete technical measures.

---

### Technical Requirements Under 3.3(d)

The harmonised standards for Article 3.3(d) are being developed by ETSI and CEN/CENELEC. The draft standards point to requirements that will be familiar to anyone who has looked at EN 303 645 or the CRA:

**Access control and authentication**: The device must authenticate users and other devices before granting access. Default passwords must be unique per device. This mirrors EN 303 645 Provision 1.

**Secure communication**: Network traffic must be encrypted using current best-practice algorithms. Plaintext protocols are not acceptable for any communication that carries sensitive data or control commands.

**Software update capability**: The device must support secure software updates. The update mechanism must verify the authenticity and integrity of updates before applying them.

**Secure default configuration**: The device must ship with a secure default configuration. Unnecessary services and interfaces must be disabled by default.

**Input validation**: The device must validate all data received from external sources to prevent injection attacks, buffer overflows, and other exploitation techniques.

For embedded devices, input validation is one area where Rust provides a tangible advantage. The language's type system and bounds checking eliminate entire categories of input validation bugs:

```rust
/// Parsing a network command with strict validation
#[derive(Debug)]
enum Command {
    SetThreshold(u16),
    ReadSensor(u8),
    Reset,
}

#[derive(Debug)]
enum ParseError {
    InvalidOpcode,
    PayloadTooShort,
    ValueOutOfRange,
}

fn parse_command(data: &[u8]) -> Result<Command, ParseError> {
    if data.is_empty() {
        return Err(ParseError::PayloadTooShort);
    }

    match data[0] {
        0x01 => {
            if data.len() < 3 {
                return Err(ParseError::PayloadTooShort);
            }
            let value = u16::from_le_bytes([data[1], data[2]]);
            if value > 4095 {
                return Err(ParseError::ValueOutOfRange);
            }
            Ok(Command::SetThreshold(value))
        }
        0x02 => {
            if data.len() < 2 {
                return Err(ParseError::PayloadTooShort);
            }
            if data[1] > 7 {
                return Err(ParseError::ValueOutOfRange);
            }
            Ok(Command::ReadSensor(data[1]))
        }
        0x03 => Ok(Command::Reset),
        _ => Err(ParseError::InvalidOpcode),
    }
}
```

---

### The Conformity Assessment Problem

Here's where the RED cybersecurity requirements get complicated. Under the RED, conformity assessment follows a modular system:

- **Module A (Internal Production Control)**: Self-assessment. The manufacturer declares conformity based on internal testing and documentation.
- **Module B + C**: Type examination by a notified body (Module B) followed by internal production control or type conformity (Module C).
- **Module H**: Full quality assurance with notified body involvement throughout.

For the existing RED requirements (radio and EMC), most IoT devices use Module A or Module B+C. The question for the cybersecurity delegated acts is which assessment modules will be required—and this depends on the harmonised standards.

If harmonised standards are published and referenced in the Official Journal of the EU before the application date, manufacturers can use self-assessment (Module A). If harmonised standards are not yet referenced, third-party assessment becomes mandatory. This is a significant distinction because third-party assessment adds cost (€10,000-€50,000+), time (months), and requires engaging a notified body with cybersecurity expertise.

The current situation is fluid. Standards development is progressing but the timeline for formal publication and referencing in the OJEU is uncertain. Manufacturers should plan for both scenarios.

---

### RED vs. CRA: Understanding the Overlap

The Cyber Resilience Act and the RED cybersecurity delegated acts have significant overlap in their requirements. Both require secure defaults, update mechanisms, vulnerability handling, and protected communication. The European Commission has acknowledged this overlap and has indicated that the CRA will eventually supersede the RED cybersecurity requirements—but the transition is not instantaneous.

In practical terms:

- Products that comply with the CRA are expected to meet the RED cybersecurity requirements as well (the CRA requirements are a superset)
- During the transition period, both sets of requirements may apply simultaneously
- The CRA's conformity assessment procedures will eventually replace the RED's for cybersecurity aspects
- Until the CRA fully applies (December 2027), the RED delegated acts remain relevant

For manufacturers, the pragmatic approach is to target CRA compliance as the primary goal. If you meet the CRA requirements, you'll satisfy the RED cybersecurity requirements as well. But if you need to place products on the market before the CRA fully applies, you need to address the RED requirements independently.

---

### Privacy Requirements Under 3.3(e)

The privacy delegated act requires devices to include technical measures for data protection. This is distinct from GDPR compliance (which is about organizational practices and data processing agreements) and focuses on the product itself:

- **Data minimization in firmware**: The device should only collect and transmit data that is necessary for its function. If your sensor device is sending MAC addresses, device identifiers, or usage patterns to the cloud that aren't needed for the core function, you have a compliance issue.

- **User consent mechanisms**: If the device collects personal data, there must be a mechanism for obtaining and managing user consent. For devices with limited UI, this might be handled through a companion app or web interface.

- **Data deletion capability**: Users must be able to delete their personal data from the device. A factory reset that verifiably erases user data satisfies this requirement.

- **Transparency**: Users must be informed about what data the device collects and how it's used. This can be addressed through documentation, but the device itself should provide indicators when it's actively collecting data (microphones, cameras, location).

For embedded engineers, the data minimization principle is the most relevant. Review what your device actually transmits and strip out anything that's not necessary:

```rust
/// Telemetry payload — only include necessary operational data
struct TelemetryPayload {
    temperature_c: i16,      // Needed: core sensor function
    humidity_pct: u8,         // Needed: core sensor function
    battery_mv: u16,          // Needed: device health
    uptime_secs: u32,         // Needed: diagnostics
    // NOT included: device MAC address, user-identifiable info,
    // precise timestamps, or usage patterns
}
```

---

### Practical Compliance Checklist

For an IoT device manufacturer preparing for RED cybersecurity compliance:

**Immediate actions:**
1. Inventory all wireless interfaces and determine which delegated acts apply
2. Review default configuration against the secure defaults requirements
3. Verify that the device supports authenticated, integrity-checked firmware updates
4. Audit data collection and transmission against the data minimization principle

**Short-term (3-6 months):**
5. Implement or verify input validation on all external interfaces
6. Ensure communication encryption meets current standards (TLS 1.2+ for TCP, DTLS for UDP)
7. Establish a vulnerability handling process if you don't have one
8. Prepare technical documentation for the conformity assessment

**Medium-term (6-12 months):**
9. Engage with a notified body for preliminary consultation on the assessment path
10. Align your RED compliance work with CRA preparation to avoid duplication
11. Build conformity assessment evidence (test reports, design documentation, risk assessment)

The RED cybersecurity requirements are not going away. Even as the CRA eventually absorbs the cybersecurity aspects, the overlap period means manufacturers need to address both. Starting now—especially on the fundamentals of secure defaults, update mechanisms, and input validation—positions you well regardless of how the regulatory landscape evolves.
