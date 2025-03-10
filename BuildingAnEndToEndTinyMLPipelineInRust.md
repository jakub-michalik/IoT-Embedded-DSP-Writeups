**Building an End-to-End TinyML Pipeline in Rust**

Most TinyML tutorials stop at the point where you have a model running on a microcontroller and producing some output. That's the interesting part, sure, but it's not the whole job. In a real deployment you need to think about the full chain: how you collect and label training data, how you train and optimize the model, how you package it for the target device, how you integrate it into firmware, and how you handle updates when the model needs to change. This article walks through each of those stages with a focus on where Rust fits and where it doesn't.

---

### The Pipeline at a Glance

A complete TinyML pipeline has roughly five stages:

1. **Data collection and labeling** — gathering sensor data from the target hardware and annotating it
2. **Model training and optimization** — training in Python, then quantizing and pruning for the target device
3. **Packaging** — converting the model to a deployment format and embedding it in the firmware
4. **Firmware integration** — writing the Rust inference code that loads and runs the model
5. **Deployment and update** — getting the firmware onto devices and managing subsequent updates

Rust is relevant mainly in stages 3, 4, and parts of 5. Stages 1 and 2 are firmly in Python territory—the training ecosystem is there, the tooling is there, and there's no good reason to fight it. The boundary between Python and Rust is the `.tflite` (or `.onnx`) file that comes out of stage 2.

---

### Stage 1: Data Collection from Rust Firmware

This is often overlooked, but the data collection firmware matters more than people think. If your training data was collected under different conditions than your production firmware, you'll have distribution shift—the model will see inputs at inference time that don't look like what it was trained on, and accuracy drops.

For this reason, it's worth writing the data collection firmware in Rust, using the same preprocessing code that your production firmware will use. Capture raw sensor readings, apply the same normalization and windowing that the model will see, and serialize to a format you can pull off the device:

```rust
fn collect_sample(sensor: &mut impl Sensor, window: &mut SampleWindow) {
    let raw = sensor.read_raw();
    let normalized = normalize(raw, SENSOR_MIN, SENSOR_MAX);
    window.push(normalized);

    if window.is_full() {
        // Serialize and transmit over UART for offline labeling
        uart_send_sample(window.as_slice());
        window.reset();
    }
}
```

If you write the data collection and the inference preprocessing separately (data collection in a quick Python script, inference in Rust), you'll almost certainly introduce subtle differences that hurt model accuracy. Shared code is the safest approach.

---

### Stage 2: Training and Optimization

This is Python's domain. Use TensorFlow, PyTorch, or whatever framework fits your use case. The key decisions that affect the Rust side:

**Model format**: TensorFlow Lite (`.tflite`) has the best embedded support through TFLM. ONNX is also well-supported through Tract (pure Rust) or ONNX Runtime. For bare-metal targets without an OS, TFLM via FFI is usually the most practical path.

**Quantization**: Apply post-training quantization before exporting. An int8-quantized model is 4x smaller than float32 and often 3-5x faster with CMSIS-NN. Quantization-aware training gives better accuracy if post-training quantization hurts your metrics too much.

**Model size constraints**: Know your target's RAM and flash budgets before training, not after. A model that barely fits leaves no room for the arena, stack, and other firmware components. A rough rule: total flash budget ÷ 3 for the model, with the rest for firmware and scratch space.

---

### Stage 3: Packaging the Model into Firmware

The typical approach is to include the `.tflite` file as a byte array using the `include_bytes!` macro:

```rust
static MODEL_DATA: &[u8] = include_bytes!("../models/gesture_model_int8.tflite");
```

This embeds the model directly into the firmware binary, placed in flash. For larger models that don't fit alongside firmware, you might store the model in a separate flash partition and load it at runtime—but this requires a more complex boot process.

A useful `build.rs` step is to automatically generate some metadata at build time:

```rust
// build.rs
fn main() {
    let model_path = "models/gesture_model_int8.tflite";
    let metadata = std::fs::metadata(model_path).unwrap();
    println!("cargo:rustc-env=MODEL_SIZE={}", metadata.len());
    println!("cargo:rerun-if-changed={}", model_path);
}
```

Then in your firmware:

```rust
const MODEL_SIZE: usize = env!("MODEL_SIZE", "MODEL_SIZE must be set by build.rs")
    .parse()
    .unwrap_or(0);
```

This makes the model size available as a constant, useful for arena sizing and capacity checks.

---

### Stage 4: Firmware Integration

This is where most of the Rust work happens. The structure I've found most maintainable is to separate concerns into three layers:

**Sensor layer**: reads raw data, applies hardware-specific normalization, and produces a fixed-size float array.

**Inference layer**: owns the TFLM interpreter (or Tract session), takes preprocessed inputs, runs inference, and returns output probabilities or class indices.

**Application layer**: decides what to do with inference results—trigger actuators, log events, update a state machine.

```rust
pub struct InferencePipeline {
    interpreter: TflmInterpreter,
    input_buffer: [f32; INPUT_SIZE],
    output_buffer: [f32; OUTPUT_SIZE],
}

impl InferencePipeline {
    pub fn run(&mut self, sensor: &mut impl Sensor) -> ClassificationResult {
        sensor.read_normalized(&mut self.input_buffer);
        self.interpreter.set_input(&self.input_buffer);
        self.interpreter.invoke();
        self.interpreter.get_output(&mut self.output_buffer);
        ClassificationResult::from_scores(&self.output_buffer)
    }
}
```

Keeping the three layers cleanly separated makes it straightforward to test the inference layer independently—you can write unit tests that feed known inputs directly to the interpreter without needing actual sensor hardware.

---

### Stage 5: Deployment and Updates

Getting initial firmware onto devices is usually handled by your hardware vendor's flashing tool. The more interesting problem is updates: when you retrain the model (more data, corrected labels, new target classes), how do you push the updated model to deployed devices?

There are two broad approaches:

**Full firmware update**: Package the new model with an updated firmware binary and push a full OTA update. This is simpler—you're replacing the entire firmware image, and your existing OTA infrastructure handles it. The downside is that a full firmware image is larger to transfer and apply.

**Model-only update**: Define a dedicated partition in your flash layout for the model, separate from the application firmware. Update only that partition when the model changes. This requires more upfront design—you need a model partition header with size and version fields, integrity checking before applying, and fallback logic if the new model fails validation:

```rust
fn try_load_model(partition: &ModelPartition) -> Result<&[u8], ModelError> {
    let header = partition.read_header()?;
    if header.magic != MODEL_MAGIC {
        return Err(ModelError::InvalidMagic);
    }
    let model_bytes = partition.read_model(header.size)?;
    verify_signature(model_bytes, &header.signature)?;
    Ok(model_bytes)
}
```

For most projects, full firmware updates are the right starting point—model-only updates add significant complexity and are only worth it when you're updating models frequently or bandwidth is severely constrained.

---

### Putting It Together

A complete TinyML pipeline in Rust isn't just about the inference code. The data collection firmware, the preprocessing logic, the packaging step, and the update mechanism all matter for the quality and reliability of the end system. Rust's strengths—memory safety, explicit resource management, fearless concurrency—pay off across all these stages, not just in the inference hot path. Building the full pipeline with consistency across stages, rather than treating the firmware as an afterthought to the model training, is what separates a demo from a deployable product.
