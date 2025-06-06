**Over-the-Air Model Updates for Embedded Rust Systems**

The model you deploy today won't be the model you want six months from now. Conditions change, you collect more representative training data, you discover the model has blind spots, or you add new target classes. In a cloud system, you just redeploy. In an embedded deployment with devices scattered across a factory floor, a farm, or a city, you need over-the-air update capability. And when the "payload" being updated is a machine learning model rather than just configuration data, there are some additional design considerations worth thinking through carefully.

---

### The Basic Architecture

An OTA system for embedded devices has a few core components regardless of what's being updated:

**Transport**: How bits get from your infrastructure to the device. Common options include BLE, Wi-Fi, LoRaWAN, Zigbee, or a wired network interface.

**Bootloader**: A separate piece of firmware that runs before the main application and decides what to load. It manages the download partition, validates received images, and performs the swap.

**Partition scheme**: How flash is divided between the running firmware, the download partition, and any persistent storage.

**Security**: Cryptographic verification that the update is authentic and untampered. For ML models specifically, this is especially important—a tampered model could be subtly miscalibrated in ways that are hard to detect.

Rust fits most naturally in the application-level update client and the model loading/verification code. The bootloader is often handled by established tools like MCUboot, which has a well-maintained C implementation and works well alongside Rust application firmware.

---

### MCUboot + Rust Application

MCUboot is a standard bootloader for embedded systems that supports firmware signing, rollback protection, and A/B partition schemes. Using MCUboot with a Rust application means your firmware image is signed with your private key during the build process, and MCUboot verifies the signature before booting.

The signing step integrates naturally into a Rust build pipeline via `build.rs` or a post-build step in your CI:

```bash
# Sign the firmware image after building
imgtool sign \
  --key signing_key.pem \
  --header-size 0x200 \
  --align 4 \
  --version 1.2.3 \
  --slot-size 0x60000 \
  target/thumbv7em-none-eabihf/release/my_firmware.bin \
  my_firmware_signed.bin
```

From the Rust firmware perspective, MCUboot handles the boot decision transparently. The application just needs to call the "image ok" confirmation after successful boot to prevent MCUboot from rolling back:

```rust
fn confirm_successful_boot() {
    // Mark the current image as confirmed so MCUboot doesn't roll back
    // Exact API depends on your MCUboot integration crate
    mcuboot_confirm::mark_image_ok();
}
```

Call this only after you've verified that the application is actually working—after sensors initialize, connectivity is established, and the ML model loads successfully. If the new firmware crashes before this call, MCUboot rolls back to the previous image on the next reboot.

---

### Separating Model Updates from Firmware Updates

A full firmware update works, but it's wasteful when only the model changes. A 200KB firmware binary plus a 40KB model means sending 240KB for a model change. If your transport is LoRaWAN at 250 bytes/second, that's 16 minutes of continuous transmission per update.

A better architecture for model-heavy applications: dedicate a partition in flash exclusively to the model, separate from the firmware image.

```
Flash layout:
+--------------------+  0x08000000
| Bootloader (MCUboot)|
+--------------------+  0x08010000
| Application FW     |
| (slot 0, primary)  |
+--------------------+  0x08060000
| Application FW     |
| (slot 1, secondary)|
+--------------------+  0x080B0000
| Model partition    |  <- updated independently
+--------------------+  0x080F0000
| Config/NVS         |
+--------------------+
```

The model partition has its own header structure:

```rust
#[repr(C)]
struct ModelPartitionHeader {
    magic: u32,          // 0xML_MODEL or similar sentinel
    version: u32,
    model_size: u32,
    timestamp: u64,
    signature: [u8; 64], // Ed25519 signature over the model bytes
    _reserved: [u8; 16],
}
```

The firmware reads the header, verifies the signature, and only then passes the model pointer to the inference engine:

```rust
fn load_verified_model(partition_base: *const u8) -> Result<&'static [u8], ModelError> {
    let header = unsafe { &*(partition_base as *const ModelPartitionHeader) };

    if header.magic != MODEL_MAGIC {
        return Err(ModelError::BadMagic);
    }
    let model_start = unsafe {
        partition_base.add(core::mem::size_of::<ModelPartitionHeader>())
    };
    let model_bytes = unsafe {
        core::slice::from_raw_parts(model_start, header.model_size as usize)
    };
    verify_ed25519_signature(model_bytes, &header.signature, VENDOR_PUBLIC_KEY)?;
    Ok(model_bytes)
}
```

The `unsafe` blocks are unavoidable here—you're reading from raw flash memory—but they're localized and wrapped in a safe function that returns a `Result`. The rest of the application works with the verified `&[u8]` slice safely.

---

### Delta Updates for Large Models

If your model is large (tens of kilobytes) and bandwidth is expensive, consider delta updates: instead of sending the full new model, send only the differences from the current version. Tools like `bsdiff`/`bspatch` or `xdelta` can generate and apply binary patches.

The receiver needs enough RAM or flash staging area to apply the patch. On very constrained devices this may not be feasible, but on Cortex-M7 targets with external flash it's worth considering. The size savings can be dramatic: a model retrained with additional data but similar architecture might have 90% of its bytes unchanged, yielding a patch that's one-tenth the size of the full model.

---

### Handling Update Failures Gracefully

Any step of the update process can fail: the download might be interrupted, flash writes might fail, or the new model might produce unexpectedly poor results after deployment. Each failure mode needs a defined response.

A simple state machine in the update client:

```rust
enum UpdateState {
    Idle,
    Downloading { bytes_received: usize, total: usize },
    Validating,
    Applying,
    Confirming,
    RollingBack,
}
```

The transitions and error handling:
- **Download interrupted**: resume from offset on next connection, or restart from zero if the transport doesn't support resumption
- **Validation failure** (bad signature, truncated): discard the download, keep running the current model, log the failure and report it
- **Post-apply failure** (model loads but produces garbage output): detect this via a validation inference pass on a known test input, roll back to the previous model partition
- **Unrecoverable**: if no valid model exists in the partition, fall back to a minimal "safe mode" behavior without ML inference

The key principle is that the device should never be left in a state where it has no valid behavior. The rollback path must be as well-tested as the happy path.

---

### Testing Update Flows

Update logic is notoriously hard to test on the bench. A few approaches that work:

**Simulated flash partitions in hosted tests**: Write a thin abstraction over the flash read/write operations, implement a version that uses RAM for tests, and run your update state machine against it. You can simulate download interruptions, corruption, and verification failures cheaply.

**Integration testing with physical hardware**: Keep a few devices running previous model versions and verify that your update pipeline can upgrade them. Test rollback by deliberately deploying a model with a known bad signature.

**Canary deployments**: If you have enough devices, update a small fraction first, monitor their behavior for 24-48 hours, then roll out to the rest. Build this into your update server infrastructure.

---

### Summary

OTA model updates require thinking through the full chain: transport security, partition layout, signature verification, rollback handling, and update testing. The combination of MCUboot for firmware updates and a dedicated model partition for model-only updates gives a flexible architecture that keeps update payloads as small as possible while maintaining strong security guarantees. Rust's type system and explicit error handling make it practical to implement the update client with the kind of robustness that field deployments require—where a failure at 3am in a remote location needs to self-heal, not wait for an on-site visit.
