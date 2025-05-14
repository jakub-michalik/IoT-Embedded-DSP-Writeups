**Anomaly Detection at the Edge with Rust and TinyML**

Anomaly detection is one of the most practical TinyML applications: instead of classifying inputs into known categories, the system learns what "normal" looks like and flags deviations. This is useful precisely because you can't enumerate all failure modes in advance. A bearing that's starting to fail vibrates differently than a healthy one, but the specific failure signature might not match any labeled example in your training set. An unsupervised or semi-supervised approach can catch it anyway.

The edge is a particularly good fit for anomaly detection. You want low latency (catch problems before they escalate), continuous monitoring (anomalies are rare but you can't miss them), and you often want to avoid streaming raw sensor data to a cloud backend—the data volumes are high and the privacy concerns can be real. Rust's properties make implementing this well on embedded hardware more tractable than it might seem.

---

### Choosing the Right Algorithm

"Anomaly detection" covers a range of techniques with very different resource profiles:

**Statistical methods**: Track mean and variance online. Flag samples more than N standard deviations from the mean. Extremely cheap, works well for simple scalar signals, but fails when the normal signal has a complex multivariate structure or temporal pattern.

**Autoencoders**: Train a small neural network to reconstruct its input. A well-trained autoencoder reconstructs normal inputs with low error and fails on anomalies. The reconstruction error is your anomaly score. Medium cost—depends on network size.

**Isolation Forest**: Randomly partitions the feature space. Anomalies require fewer partitions to isolate. Can be implemented without deep learning. Classical ML, so Linfa in Rust can handle it.

**One-class SVM**: Learns the boundary of the normal class. Everything outside the boundary is anomalous. Also classical ML, with a Linfa implementation available.

For most embedded applications, I'd start with autoencoders or statistical methods. Autoencoders generalize better for multivariate time-series data (vibration, audio, multi-axis IMU). Statistical methods are appropriate when you have a single signal and the normal distribution is roughly Gaussian.

---

### Training an Autoencoder for Anomaly Detection

Training happens in Python, but the design decisions affect the Rust integration. For a vibration-based bearing monitor with a 3-axis accelerometer at 400Hz:

1. Collect several hours of normal operation data
2. Compute FFT features or use raw windowed samples as input
3. Train a small autoencoder (encoder: 3 dense layers down to a bottleneck; decoder: symmetric)
4. Quantize to int8 and export to TFLite

The key constraint is that the bottleneck dimension should be small enough that the network can't just memorize the input—it has to learn the underlying structure of normal data. For vibration data, a bottleneck of 8-16 dimensions for a 64-point input window often works well.

```python
# Python training sketch
import tensorflow as tf

input_dim = 64
bottleneck = 12

encoder = tf.keras.Sequential([
    tf.keras.layers.Dense(32, activation='relu', input_shape=(input_dim,)),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(bottleneck, activation='relu'),
])
decoder = tf.keras.Sequential([
    tf.keras.layers.Dense(16, activation='relu', input_shape=(bottleneck,)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(input_dim, activation='linear'),
])
autoencoder = tf.keras.Sequential([encoder, decoder])
autoencoder.compile(optimizer='adam', loss='mse')
autoencoder.fit(normal_data, normal_data, epochs=50, batch_size=32)
```

---

### Computing Reconstruction Error in Rust

Once deployed, the inference loop computes reconstruction error and compares it against a threshold. The threshold is typically the 95th or 99th percentile of reconstruction error on the validation set of normal data—you want enough headroom that normal variation doesn't trigger false alarms.

```rust
fn compute_anomaly_score(
    interpreter: &mut TflmInterpreter,
    input: &[f32; INPUT_DIM],
    output: &mut [f32; INPUT_DIM],
) -> f32 {
    interpreter.set_input(input);
    interpreter.invoke();
    interpreter.get_output(output);

    // Mean squared error between input and reconstruction
    let mse: f32 = input.iter()
        .zip(output.iter())
        .map(|(a, b)| (a - b).powi(2))
        .sum::<f32>() / INPUT_DIM as f32;

    mse
}

fn is_anomalous(score: f32) -> bool {
    score > ANOMALY_THRESHOLD
}
```

A common refinement: don't trigger on a single high score. Instead, use a sliding window of scores and trigger only when the moving average exceeds the threshold. This suppresses spurious alerts from single-sample noise:

```rust
struct AnomalyDetector {
    score_window: [f32; WINDOW_SIZE],
    window_pos: usize,
    window_sum: f32,
}

impl AnomalyDetector {
    fn update(&mut self, score: f32) -> bool {
        // Subtract the oldest value before overwriting
        self.window_sum -= self.score_window[self.window_pos];
        self.score_window[self.window_pos] = score;
        self.window_sum += score;
        self.window_pos = (self.window_pos + 1) % WINDOW_SIZE;

        let avg = self.window_sum / WINDOW_SIZE as f32;
        avg > ANOMALY_THRESHOLD
    }
}
```

The fixed-size array and manual circular buffer here are intentional—no heap allocation, predictable memory layout, and the compiler can optimize the arithmetic well.

---

### Statistical Baseline as a Complement

For a lightweight first stage (before running the autoencoder), a simple statistical check can filter out the obvious cases:

```rust
struct OnlineStats {
    n: u32,
    mean: f32,
    m2: f32,  // sum of squared deviations, for Welford's algorithm
}

impl OnlineStats {
    fn update(&mut self, value: f32) {
        self.n += 1;
        let delta = value - self.mean;
        self.mean += delta / self.n as f32;
        let delta2 = value - self.mean;
        self.m2 += delta * delta2;
    }

    fn variance(&self) -> f32 {
        if self.n < 2 { return 0.0; }
        self.m2 / (self.n - 1) as f32
    }

    fn is_outlier(&self, value: f32, sigma: f32) -> bool {
        let std_dev = self.variance().sqrt();
        (value - self.mean).abs() > sigma * std_dev
    }
}
```

Welford's online algorithm computes mean and variance in a single pass without storing all samples, making it suitable for a resource-constrained device.

---

### Threshold Calibration in the Field

One practical challenge with anomaly detection is that the threshold needs calibration. If it's too sensitive, you get alert fatigue—operators ignore the device because it cries wolf. If it's too permissive, real anomalies slip through.

A useful approach for initial deployments: log raw anomaly scores over the first few weeks in a known-normal operating period, transmit them in batch when a connection is available, and compute the threshold offline. Then push an updated threshold as part of a configuration update rather than a full firmware update. This keeps the threshold decoupled from the firmware release cycle, which is valuable because you'll want to adjust it as you learn more about the operating environment.

---

### Summary

Anomaly detection is a strong use case for edge ML precisely because it doesn't require labeled anomaly examples—hard to get by definition—and benefits from local, continuous processing. The combination of a lightweight first-stage filter, an autoencoder for structural anomaly scoring, and a sliding-window alerting policy gives you a practical system that can be implemented cleanly in Rust. The resource profile is manageable for most Cortex-M4 and above targets, and the lack of runtime allocation makes the behavior predictable. The main ongoing challenge is threshold calibration, which is an operational rather than a software problem—but one worth designing for from the start.
