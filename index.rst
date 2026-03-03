IoT, Embedded Systems & DSP Writeups
=====================================

A treasure-trove of explorations focused on IoT, embedded systems, and DSP.
We break down intricate concepts, explore the use of Rust in IoT, and highlight
emerging trends. An enlightening ride for developers and tech enthusiasts alike.

.. mermaid::

   flowchart TB
       id1(IoT-Embedded-DSP-Writeups) -->|Focus| id2["IoT, Embedded Systems & DSP"]
       id2 -->|Components| id3["Rust, Concepts, and Trends"]
       subgraph sg1["In-depth Exploration"]
           id3 -->|Intricate Concepts| id4[Break Down & Understanding]
           id3 -->|Use of Rust in IoT| id5[Application & Efficiency]
           id3 -->|Highlight Trends| id6[Evolving Technology & Trends]
       end

.. raw:: html

   <style>
   .tag-cloud {
     display: flex; flex-wrap: wrap; justify-content: center;
     align-items: center; gap: 6px; padding: 1.5em 0;
   }
   .tag-cloud .tag {
     display: inline-block; padding: 5px 14px; border-radius: 20px;
     font-weight: 600; cursor: pointer; user-select: none;
     opacity: 0; transform: scale(0.3) rotate(-8deg);
     animation: tagPop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
     transition: transform 0.25s ease, box-shadow 0.25s ease, filter 0.25s ease;
   }
   .tag-cloud .tag:hover {
     transform: scale(1.15) rotate(0deg) !important;
     box-shadow: 0 4px 15px rgba(0,0,0,0.2);
     z-index: 1; position: relative;
   }
   .tag-cloud .tag.active {
     box-shadow: 0 0 0 3px currentColor;
     transform: scale(1.1) !important;
   }
   .tag-cloud .tag.dimmed { filter: grayscale(0.7) opacity(0.4); }
   @keyframes tagPop { to { opacity: 1; transform: scale(1) rotate(0deg); } }
   .tag-cloud .tag.sz-xl { font-size: 1.5em; }
   .tag-cloud .tag.sz-lg { font-size: 1.25em; }
   .tag-cloud .tag.sz-md { font-size: 1.05em; }
   .tag-cloud .tag.sz-sm { font-size: 0.88em; }
   .article-table tr.hidden { display: none; }
   .article-table tr { transition: opacity 0.2s ease; }
   .filter-info {
     text-align: center; padding: 8px; font-size: 0.9em;
     color: var(--color-foreground-muted, #888); display: none;
   }
   .filter-info.visible { display: block; }
   </style>

   <div class="tag-cloud" id="tagCloud">
     <span class="tag sz-xl" data-tag="Rust" style="background:#e8f5e9;color:#2e7d32;animation-delay:0.00s;">Rust</span>
     <span class="tag sz-xl" data-tag="Embedded" style="background:#e3f2fd;color:#1565c0;animation-delay:0.05s;">Embedded</span>
     <span class="tag sz-lg" data-tag="IoT" style="background:#fce4ec;color:#c62828;animation-delay:0.10s;">IoT</span>
     <span class="tag sz-md" data-tag="DSP" style="background:#f3e5f5;color:#6a1b9a;animation-delay:0.15s;">DSP</span>
     <span class="tag sz-xl" data-tag="TinyML" style="background:#fff3e0;color:#e65100;animation-delay:0.20s;">TinyML</span>
     <span class="tag sz-lg" data-tag="STM32" style="background:#e0f2f1;color:#00695c;animation-delay:0.25s;">STM32</span>
     <span class="tag sz-lg" data-tag="nRF52" style="background:#e8eaf6;color:#283593;animation-delay:0.30s;">nRF52</span>
     <span class="tag sz-md" data-tag="nRF54" style="background:#fbe9e7;color:#bf360c;animation-delay:0.35s;">nRF54</span>
     <span class="tag sz-lg" data-tag="RTOS" style="background:#e0f7fa;color:#00838f;animation-delay:0.40s;">RTOS</span>
     <span class="tag sz-md" data-tag="Security" style="background:#f1f8e9;color:#558b2f;animation-delay:0.45s;">Security</span>
     <span class="tag sz-md" data-tag="BLE" style="background:#ede7f6;color:#4527a0;animation-delay:0.50s;">BLE</span>
     <span class="tag sz-sm" data-tag="CAN Bus" style="background:#fff8e1;color:#f57f17;animation-delay:0.55s;">CAN Bus</span>
     <span class="tag sz-sm" data-tag="Thread/Matter" style="background:#e1f5fe;color:#0277bd;animation-delay:0.60s;">Thread / Matter</span>
     <span class="tag sz-md" data-tag="Power" style="background:#f9fbe7;color:#827717;animation-delay:0.65s;">Power Management</span>
     <span class="tag sz-sm" data-tag="C/C++" style="background:#efebe9;color:#4e342e;animation-delay:0.70s;">C / C++</span>
     <span class="tag sz-sm" data-tag="OTA" style="background:#e8eaf6;color:#1a237e;animation-delay:0.75s;">OTA</span>
     <span class="tag sz-lg" data-tag="Edge AI" style="background:#fce4ec;color:#880e4f;animation-delay:0.80s;">Edge AI</span>
   </div>
   <div class="filter-info" id="filterInfo"></div>

Articles
--------

.. raw:: html

   <table class="article-table" style="width:100%;border-collapse:collapse;">
   <tr style="border-bottom:2px solid var(--color-foreground-border,#ccc);">
     <th style="text-align:left;padding:8px;">Title</th>
     <th style="text-align:center;padding:8px;white-space:nowrap;">Read time</th>
     <th style="text-align:center;padding:8px;white-space:nowrap;">Date</th>
   </tr>
   <tr data-tags="Rust,IoT,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="EmergenceOfRust.html">Emergence of Rust</a></td><td style="text-align:center;padding:8px;">~3 min</td><td style="text-align:center;padding:8px;">01.10.23</td></tr>
   <tr data-tags="Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="BecomingAnExceptionalEmbeddedSoftwareArchitect.html">Becoming an Exceptional Embedded Software Architect</a></td><td style="text-align:center;padding:8px;">~5 min</td><td style="text-align:center;padding:8px;">08.10.23</td></tr>
   <tr data-tags="Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="NavigatingTheWorldOfEmbeddedSystemArchitecture.html">Navigating the World of Embedded System Architecture</a></td><td style="text-align:center;padding:8px;">~5 min</td><td style="text-align:center;padding:8px;">17.10.23</td></tr>
   <tr data-tags="Rust,DSP" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="DevelopingLowPassFilterInRust.html">Developing a Low Pass Filter in Rust</a></td><td style="text-align:center;padding:8px;">~5 min</td><td style="text-align:center;padding:8px;">20.10.23</td></tr>
   <tr data-tags="Rust,IoT,Security" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="SecuringIotDevicesWithRust.html">Securing IoT Devices with Rust</a></td><td style="text-align:center;padding:8px;">~5 min</td><td style="text-align:center;padding:8px;">16.10.23</td></tr>
   <tr data-tags="IoT,Power" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="UnderstandingPowerConstraintsInIot.html">Understanding Power Constraints in IoT</a></td><td style="text-align:center;padding:8px;">~7 min</td><td style="text-align:center;padding:8px;">09.09.24</td></tr>
   <tr data-tags="Rust,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="ExploringAdvancedConcurrencyPatternsInRust.html">Exploring Advanced Concurrency Patterns in Rust</a></td><td style="text-align:center;padding:8px;">~7 min</td><td style="text-align:center;padding:8px;">11.09.24</td></tr>
   <tr data-tags="Rust,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="OptimizingMemoryUsageInRust.html">Optimizing Memory Usage in Rust for Embedded Systems</a></td><td style="text-align:center;padding:8px;">~6 min</td><td style="text-align:center;padding:8px;">13.09.24</td></tr>
   <tr data-tags="Rust,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="MasteringInterrupt-DrivenDesignWithRust.html">Mastering Interrupt-Driven Design with Rust</a></td><td style="text-align:center;padding:8px;">~10 min</td><td style="text-align:center;padding:8px;">17.09.24</td></tr>
   <tr data-tags="DSP,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="HarnessingThePowerOfDSP.html">Harnessing the Power of DSP in Embedded Systems</a></td><td style="text-align:center;padding:8px;">~8 min</td><td style="text-align:center;padding:8px;">18.09.24</td></tr>
   <tr data-tags="Rust,DSP" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="LeveragingDspIntrinsicsInRust.html">Leveraging DSP Intrinsics in Rust</a></td><td style="text-align:center;padding:8px;">~8 min</td><td style="text-align:center;padding:8px;">23.09.24</td></tr>
   <tr data-tags="Rust,RTOS,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="IntegratingRustWithRealTimeOperatingSystems.html">Integrating Rust with RTOS in Embedded Systems</a></td><td style="text-align:center;padding:8px;">~10 min</td><td style="text-align:center;padding:8px;">25.09.24</td></tr>
   <tr data-tags="Rust,TinyML,Edge AI" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="GettingStartedWithTinyMLInRust.html">Getting Started with TinyML in Rust</a></td><td style="text-align:center;padding:8px;">~10 min</td><td style="text-align:center;padding:8px;">10.12.24</td></tr>
   <tr data-tags="Rust,TinyML,Edge AI" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="ComparingEdgeMlFrameworksForRust.html">Comparing Edge ML Frameworks for Rust</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">15.12.24</td></tr>
   <tr data-tags="Rust,TinyML,Edge AI" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="OptimizingModelInferencePerformanceAndMemoryFootprintInRust.html">Optimizing Model Inference Performance and Memory Footprint in Rust</a></td><td style="text-align:center;padding:8px;">~7 min</td><td style="text-align:center;padding:8px;">26.12.24</td></tr>
   <tr data-tags="Rust,TinyML" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="IntegratingHardwareAccelerationForTinyMLInRust.html">Integrating Hardware Acceleration for TinyML in Rust</a></td><td style="text-align:center;padding:8px;">~7 min</td><td style="text-align:center;padding:8px;">31.12.24</td></tr>
   <tr data-tags="Rust,TinyML,RTOS" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="EnsuringReal-TimeAndLow-LatencyInferenceWithRustAndRTOS.html">Ensuring Real-Time and Low-Latency Inference with Rust and RTOS</a></td><td style="text-align:center;padding:8px;">~7 min</td><td style="text-align:center;padding:8px;">09.12.24</td></tr>
   <tr data-tags="Rust,TinyML,Security,Edge AI" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="SecuringOnDeviceMLInRust.html">Securing On-Device Machine Learning in Rust</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">17.02.25</td></tr>
   <tr data-tags="Rust,TinyML,Edge AI" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="BuildingAnEndToEndTinyMLPipelineInRust.html">Building an End-to-End TinyML Pipeline in Rust</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">11.03.25</td></tr>
   <tr data-tags="Rust,TinyML,Power" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="PowerManagementForTinyMLInRust.html">Power Management Strategies for TinyML in Rust</a></td><td style="text-align:center;padding:8px;">~8 min</td><td style="text-align:center;padding:8px;">23.04.25</td></tr>
   <tr data-tags="Rust,TinyML,Edge AI" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="AnomalyDetectionAtTheEdgeWithRust.html">Anomaly Detection at the Edge with Rust and TinyML</a></td><td style="text-align:center;padding:8px;">~8 min</td><td style="text-align:center;padding:8px;">14.05.25</td></tr>
   <tr data-tags="Rust,OTA,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="OtaModelUpdatesForEmbeddedRust.html">Over-the-Air Model Updates for Embedded Rust Systems</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">07.06.25</td></tr>
   <tr data-tags="Rust,STM32,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="RustOnSTM32PracticalPeripherals.html">Rust on STM32: Practical Peripherals, HAL Abstractions, and the H7</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">26.07.25</td></tr>
   <tr data-tags="Rust,nRF52,BLE,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="RustOnnRF52BLEAndLowPower.html">Rust on nRF52: BLE, Low-Power Modes, and Embassy</a></td><td style="text-align:center;padding:8px;">~8 min</td><td style="text-align:center;padding:8px;">09.08.25</td></tr>
   <tr data-tags="IoT,Thread/Matter" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="ThreadAndMatterTheNewIoTStack.html">Thread and Matter: The New IoT Connectivity Stack</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">19.09.25</td></tr>
   <tr data-tags="Rust,nRF54,Power,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="nRF54UltraLowPowerEmbeddedRust.html">nRF54 and Ultra-Low Power Embedded Rust</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">31.10.25</td></tr>
   <tr data-tags="Rust,STM32,CAN Bus" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="CANBusWithSTM32InRust.html">CAN Bus with STM32 in Rust</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">15.11.25</td></tr>
   <tr data-tags="IoT,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="IoTPlatformsThingsBoardAndEmbeddedRust.html">IoT Platforms: ThingsBoard and Embedded Rust</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">28.12.25</td></tr>
   <tr data-tags="C/C++,Embedded" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="CppInEmbeddedSystems.html">C++ in Embedded Systems: Power, Pitfalls, and When to Use It</a></td><td style="text-align:center;padding:8px;">~9 min</td><td style="text-align:center;padding:8px;">19.01.26</td></tr>
   <tr data-tags="Rust,TinyML" style="border-bottom:1px solid var(--color-foreground-border,#eee);"><td style="padding:8px;"><a href="DebuggingAndProfilingTinyMLApplicationsInRust.html">Debugging and Profiling TinyML Applications in Rust</a></td><td style="text-align:center;padding:8px;">~8 min</td><td style="text-align:center;padding:8px;">24.02.26</td></tr>
   </table>

   <script>
   (function() {
     var activeTag = null;
     var tags = document.querySelectorAll('#tagCloud .tag');
     var rows = document.querySelectorAll('.article-table tr[data-tags]');
     var info = document.getElementById('filterInfo');

     if (!tags.length || !rows.length) { return; }

     tags.forEach(function(tag) {
       tag.addEventListener('click', function() {
         var clicked = this.getAttribute('data-tag');

         if (activeTag === clicked) {
           activeTag = null;
           tags.forEach(function(t) { t.classList.remove('active','dimmed'); });
           rows.forEach(function(r) { r.classList.remove('hidden'); });
           info.classList.remove('visible');
           return;
         }

         activeTag = clicked;
         var count = 0;
         tags.forEach(function(t) {
           if (t.getAttribute('data-tag') === clicked) {
             t.classList.add('active');
             t.classList.remove('dimmed');
           } else {
             t.classList.remove('active');
             t.classList.add('dimmed');
           }
         });

         rows.forEach(function(r) {
           var rowTags = r.getAttribute('data-tags').split(',');
           if (rowTags.indexOf(clicked) !== -1) {
             r.classList.remove('hidden');
             count++;
           } else {
             r.classList.add('hidden');
           }
         });

         info.textContent = 'Showing ' + count + ' article' + (count !== 1 ? 's' : '') + ' tagged "' + clicked + '" \u2014 click again to clear';
         info.classList.add('visible');
       });
     });
   })();
   </script>

.. toctree::
   :hidden:

   EmergenceOfRust
   BecomingAnExceptionalEmbeddedSoftwareArchitect
   NavigatingTheWorldOfEmbeddedSystemArchitecture
   DevelopingLowPassFilterInRust
   SecuringIotDevicesWithRust
   UnderstandingPowerConstraintsInIot
   ExploringAdvancedConcurrencyPatternsInRust
   OptimizingMemoryUsageInRust
   MasteringInterrupt-DrivenDesignWithRust
   HarnessingThePowerOfDSP
   LeveragingDspIntrinsicsInRust
   IntegratingRustWithRealTimeOperatingSystems
   GettingStartedWithTinyMLInRust
   ComparingEdgeMlFrameworksForRust
   OptimizingModelInferencePerformanceAndMemoryFootprintInRust
   IntegratingHardwareAccelerationForTinyMLInRust
   EnsuringReal-TimeAndLow-LatencyInferenceWithRustAndRTOS
   SecuringOnDeviceMLInRust
   BuildingAnEndToEndTinyMLPipelineInRust
   PowerManagementForTinyMLInRust
   AnomalyDetectionAtTheEdgeWithRust
   OtaModelUpdatesForEmbeddedRust
   RustOnSTM32PracticalPeripherals
   RustOnnRF52BLEAndLowPower
   ThreadAndMatterTheNewIoTStack
   nRF54UltraLowPowerEmbeddedRust
   CANBusWithSTM32InRust
   IoTPlatformsThingsBoardAndEmbeddedRust
   CppInEmbeddedSystems
   DebuggingAndProfilingTinyMLApplicationsInRust
   FromCToRust
