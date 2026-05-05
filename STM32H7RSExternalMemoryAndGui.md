**STM32H7R/S: A 600 MHz STM32 That Expects You to Bring Your Own Memory**

---

I stumbled across the STM32H7R/S line recently and thought the design philosophy was interesting enough to jot down. It's not breaking news — ST announced these at the STM32 Summit back in March 2024 — but the approach is still a bit unusual for an STM32, so here are a few notes.

### The fast part

According to ST's blog post, the STM32H7R/S runs a Cortex-M7 at 600 MHz, which they call the fastest STM32 to date. That alone is a nice headline, but the more interesting bit is what ST decided *not* to put on the die.

### Bring your own memory

These chips ship with roughly 620 KB of SRAM and only 64 KB of boot flash. That's it for on-chip non-volatile storage. The idea, as ST frames it, is a "bring your own external memory" model: you wire up whatever xSPI flash (serial or parallel) you actually need for your application instead of paying for a fixed, oversized internal flash you may never fill.

The 64 KB boot flash is there to get the part up and running — it boots, then pulls your real firmware from external memory. CNX Software notes this is meant to lower BOM cost, since you size the external memory to the job rather than buying silicon with flash baked in. Whether that nets out cheaper obviously depends on your volumes and how the external memory pricing lands for you, but the *intent* is clearly cost flexibility.

It's a different mental model than the usual "pick the STM32 with enough flash and move on." Here the flash is a board-level decision.

### The GUI angle

The other thing ST leans on heavily is graphics. The H7R/S includes a NeoChrom GPU, and ST claims it can offload the Cortex-M7 by up to ~90% during animations and drawing-heavy work. I haven't tested that number — it's ST's figure — but the direction makes sense: keep the M7 free for application logic while the GPU pushes pixels. It's supported by TouchGFX, so if you're already in that ecosystem the path is reasonably paved.

Given the external-memory-first design, this all hangs together: fast core, GPU for the UI, and external xSPI flash/RAM to hold the framebuffers, fonts, and assets that a rich GUI tends to eat.

### R vs S

The naming had me look twice. The split, per ST, is mostly about security:

- **STM32H7R** — the base variant.
- **STM32H7S** — adds on-the-fly RAM encryption/decryption. ST says this is the first STM32H7 to do encryption/decryption of RAM on the fly.

That on-the-fly encryption is the part worth flagging. When your code and data live in *external* memory, the bus between the MCU and that memory is exposed, and "on-the-fly" decryption means the contents can stay encrypted off-chip and get decrypted as they're used. So the S variant's security story is a fairly natural complement to the external-memory model — if you're putting your firmware off-chip, you probably care about who can read it off the wire.

The shape of it, roughly:

```
[ STM32H7S ] --(encrypted)--> [ external xSPI flash / RAM ]
      ^
   on-the-fly decrypt as code/data is fetched
```

(That's my sketch of the concept, not an ST diagram — treat it as a mental model.)

### Why I bothered writing this down

Nothing here is a benchmark or a hands-on review — I just liked the trade-off ST made. Instead of another "more flash, more RAM" iteration, they pulled the non-volatile storage off-chip, handed you a GPU for the UI, and on the S parts added encryption to make the external-memory approach defensible. For a GUI-heavy embedded product, that's a coherent story.

Worth repeating the caveat: this was announced in March 2024, so it's not the newest news on the block. But if you, like me, only just bumped into these parts, the "bring your own memory" angle is a fun one to chew on.

### Source

- ST blog: https://blog.st.com/stm32h7r-stm32h7s/
- CNX Software: https://www.cnx-software.com/2024/03/13/600-mhz-stm32h7r-s-cortex-m7-mcu-620kb-sram-64kb-boot-flash-neochrom-gpu/
