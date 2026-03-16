**ETSI EN 303 645: Navigating Europe's Consumer IoT Security Standard**

If you've been following IoT security regulation in Europe, you've seen ETSI EN 303 645 referenced everywhere—in policy documents, in certification schemes, and increasingly in procurement requirements. It's the European standard for baseline security in consumer IoT devices, and it's rapidly becoming the de facto checklist that manufacturers need to satisfy. With the EU Cyber Resilience Act pointing to harmonised standards for conformity assessment, EN 303 645 is positioned to be the primary benchmark for proving your consumer IoT product meets European security requirements.

I've been working through the standard's provisions in the context of actual embedded projects, and what stands out is how practical it is. Unlike some security standards that read like academic exercises, EN 303 645 was written by people who understand that IoT devices run on microcontrollers with 256KB of flash and that "implement a full PKI" is not a realistic recommendation for a battery-powered sensor. The requirements are achievable, but they do demand deliberate engineering decisions—especially around authentication, update mechanisms, and data protection.

---

### The Thirteen Provisions

EN 303 645 organizes its requirements into thirteen provisions. Each one addresses a specific aspect of device security:

1. **No universal default passwords** — Every device must have a unique password, or the user must set one during setup. Hardcoded credentials shared across units are explicitly prohibited.

2. **Implement a means to manage reports of vulnerabilities** — Manufacturers must publish a vulnerability disclosure policy and act on reports in a timely manner.

3. **Keep software updated** — Devices must support secure updates. Users should be informed about security updates, and updates addressing critical vulnerabilities should be delivered automatically where possible.

4. **Securely store sensitive security parameters** — Credentials, keys, and tokens stored on the device must be protected. Plaintext storage of secrets in firmware images is a direct violation.

5. **Communicate securely** — Network communication must use encryption appropriate to the sensitivity of the data. This applies to all external communication—cloud connections, local API endpoints, device-to-device protocols.

6. **Minimize exposed attack surfaces** — Unused ports, interfaces, and services must be disabled. Debug interfaces must not be accessible in production.

7. **Ensure software integrity** — The device must verify the integrity of its software. If unauthorized modification is detected, the device should alert the user or restrict functionality.

8. **Ensure that personal data is secure** — Personal data collected, stored, or transmitted by the device must be protected with appropriate security measures.

9. **Make systems resilient to outages** — The device should continue to function (possibly with reduced capability) when network connectivity is lost. Cloud dependency for basic operation is discouraged.

10. **Examine system telemetry data** — If the device collects telemetry, it should be possible for the user to review what data is being collected.

11. **Make it easy for users to delete user data** — There must be a clear mechanism for users to erase their personal data from the device.

12. **Make installation and maintenance of devices easy** — Security-relevant setup steps should be straightforward and well-documented.

13. **Validate input data** — Data received via APIs, network interfaces, or user inputs must be validated before processing.

---

### What "No Universal Default Passwords" Really Requires

Provision 1 sounds simple, but the implementation details matter. The standard doesn't just say "don't use admin/admin." It requires that each device instance has a unique pre-programmed password, or that the setup flow forces the user to create one before the device becomes operational.

For devices provisioned in manufacturing, this means your production line needs to generate and program unique credentials per unit. This has implications for your manufacturing process, your firmware flashing tooling, and your device registration system. A common approach is to generate a random credential during factory provisioning, print it on a label or card included with the device, and store it in a protected region of flash (or in a secure element if available).

In Rust, handling per-device credentials from a protected flash region:

```rust
const CREDENTIAL_FLASH_ADDR: u32 = 0x0803_F800; // Last page of flash on STM32F4

fn read_device_credential() -> &'static [u8; 32] {
    unsafe { &*(CREDENTIAL_FLASH_ADDR as *const [u8; 32]) }
}

fn validate_credential(provided: &[u8], stored: &[u8; 32]) -> bool {
    // Constant-time comparison to prevent timing attacks
    let mut diff: u8 = 0;
    for (a, b) in provided.iter().zip(stored.iter()) {
        diff |= a ^ b;
    }
    diff == 0
}
```

---

### Secure Communication: What's Sufficient

Provision 5 requires encrypted communication, but it's pragmatic about what "appropriate" means. For a device communicating with a cloud backend over TCP, TLS 1.2 or 1.3 is the expected baseline. For constrained devices using CoAP, DTLS is the expected transport security layer. For Bluetooth Low Energy devices, the standard expects at least BLE Security Mode 1, Level 3 (authenticated pairing with encryption).

The practical challenge for constrained devices is TLS library size and RAM usage. On a Cortex-M4 with 128KB of RAM, a full TLS handshake with certificate validation is feasible but tight. Libraries like `mbedtls` (with its Rust bindings) or `rustls` (for devices with enough resources) handle the protocol, but you need to account for:

- Certificate storage (root CA certificates take space—typically 1-4KB each)
- Handshake buffer memory (the TLS handshake requires temporary buffers of 4-16KB depending on configuration)
- Session resumption (critical for battery-powered devices to avoid repeated full handshakes)

For BLE-only devices, the communication security requirements are simpler but still non-trivial. The standard expects that pairing uses a method that provides MITM protection—passkey entry or numeric comparison, not Just Works pairing (which provides encryption but no authentication).

---

### Software Integrity: Secure Boot in Practice

Provision 7 requires the device to verify the integrity of its own software. In practice, this means secure boot—a chain of trust that starts from an immutable root (usually ROM or OTP-fused bootloader code) and verifies each subsequent stage before executing it.

Many modern microcontrollers have hardware support for secure boot:

- **STM32L4/H7**: The Secure Boot and Secure Firmware Update (SBSFU) reference implementation provides a complete secure boot chain with firmware authentication and encrypted update support.
- **nRF52/nRF53**: The nRF Secure Immutable Bootloader (NSIB) combined with MCUboot provides a verified boot chain.
- **ESP32-S3/C3**: Secure Boot V2 uses RSA-3072 or ECDSA signature verification with key burning to eFuse.

If your target doesn't have hardware secure boot support, a software-only approach using a signed bootloader is the fallback. The bootloader verifies the application image signature before jumping to it:

```rust
use p256::ecdsa::{signature::Verifier, Signature, VerifyingKey};
use sha2::{Sha256, Digest};

fn verify_firmware_image(
    image: &[u8],
    signature: &Signature,
    public_key: &VerifyingKey,
) -> bool {
    let mut hasher = Sha256::new();
    hasher.update(image);
    let digest = hasher.finalize();

    public_key.verify(&digest, signature).is_ok()
}
```

The important detail: the verification key must be stored in a way that the application firmware cannot modify. If the application can overwrite the bootloader or the public key, the entire chain of trust collapses. Use flash write protection, OTP memory, or a hardware secure element for key storage.

---

### Testing Against the Standard: ETSI TS 103 701

ETSI published a companion document, TS 103 701, which defines test procedures for each provision of EN 303 645. If you're preparing for certification or self-assessment, this is the document that tells you exactly what a test lab will check.

The test procedures are surprisingly specific. For Provision 1 (no default passwords), the test involves:
1. Resetting the device to factory state
2. Attempting to access the device with commonly known default credentials
3. Verifying that the device either has a unique credential or requires the user to set one during setup
4. Verifying that the credential mechanism is not trivially bypassable

For Provision 6 (minimize attack surfaces), the test involves network scanning the device in its default configuration and verifying that only documented and necessary services are accessible.

Running these tests internally before submitting for certification saves time and money. Tools like `nmap` for network scanning, `btlejack` for BLE analysis, and custom scripts for API testing cover most of the test procedures.

---

### Certification Schemes Built on EN 303 645

Several European certification schemes reference EN 303 645 as the technical baseline:

- **ETSI Consumer IoT Cybersecurity Assessment**: Direct assessment against the standard, offered by accredited test labs across Europe.
- **BSI IT Security Label (Germany)**: Uses EN 303 645 as the technical baseline for its consumer IoT label. The label is valid for two years and requires ongoing vulnerability management.
- **Finnish Cybersecurity Label**: One of the first national schemes in Europe, also based on EN 303 645.

The trend is clear: national schemes are converging on EN 303 645 as the common technical baseline, and the CRA will likely formalize this by referencing it (or its successor) as a harmonised standard.

---

### Practical Compliance for Embedded Teams

If you're an embedded engineer looking at EN 303 645 for the first time, the actionable steps are:

1. **Audit your default configuration**: Are there any shared default passwords? Are debug interfaces disabled? Are unnecessary network services running?
2. **Review your communication security**: Is all external communication encrypted? Are you using appropriate pairing methods for BLE?
3. **Implement or verify secure boot**: Can your device verify the integrity of its firmware at startup?
4. **Set up a vulnerability disclosure process**: Even a simple `security.txt` file and a monitored email address counts as a starting point.
5. **Document everything**: EN 303 645 compliance is as much about documentation as implementation. Your technical file needs to describe how each provision is addressed.

The standard is achievable for small teams. It doesn't require exotic hardware or enterprise-grade infrastructure. What it does require is deliberate design—thinking about security as a first-class requirement rather than hoping that "we're too small to be a target" will hold up.
