# Understanding the task: `dynamo/tflite-int8-replay`

A plain-language walkthrough of the task we built that stumped Opus 4.8 (pass@5 = 0/5).
Read the story first, then use the glossary at the end whenever a term is unfamiliar.
Every **bold term** is defined in the glossary (§7).

---

## 1. What the task asks, in one sentence

"Here is a small **neural network** that has been **quantized** to run in whole numbers
(int8). Here are 48 input rows. Produce the exact whole-number output the network gives
for each row — matching the real TensorFlow Lite math exactly, down to the last digit."

That's it. It sounds boring. The difficulty is hidden in the words "**exact**" and "the
real TensorFlow Lite math."

---

## 2. The background you need (told simply)

### Neural networks normally use decimals
A neural network is just a big pile of multiply-and-add. Each **layer** takes a list of
numbers (the input), multiplies them by its **weights**, adds a **bias**, and passes the
result on. Normally these numbers are decimals (floats), like 0.0327.

### Phones can't afford decimals, so they "quantize"
Decimals are slow and power-hungry on phones/edge devices. So before shipping a model to
a phone, engineers **quantize** it: they convert every decimal into a small whole number
between −128 and 127 (that's what "**int8**" means — an 8-bit integer). The model then
runs using only integer add/multiply, which is much faster.

But integers can't represent 0.0327 directly. So quantization stores two extra numbers per
tensor:
- a **scale** (how much one integer step is worth in real units), and
- a **zero-point** (which integer represents "real value 0").

Real value ≈ `scale × (integer − zero_point)`. That's the whole trick.

### The hard part: "requantization"
Inside a layer you multiply int8 weights by int8 inputs and add them up. The running total
is a big number (int32). But the *next* layer expects small int8 numbers again. So you must
shrink that big total back down — this shrinking step is called **requantization**.

Requantization multiplies the big total by a fraction (like 0.7) and rounds to a whole
number. But you can't use a decimal 0.7 on a phone (no decimals allowed!). So TFLite stores
that fraction as **two integers**: a big `multiplier` and a `shift`. The real fraction is
`multiplier × 2^shift / 2^31`. Multiplying by this and rounding, using only integer
operations, is a famous little algorithm.

---

## 3. Where the trap lives

Rounding sounds trivial — "round to the nearest whole number." But **there are several
different, equally-real ways to round**, and they disagree at the exact halfway point:

- **Round half up**: 2.5 → 3, −2.5 → −2 (always toward +infinity on a tie)
- **Round half away from zero**: 2.5 → 3, −2.5 → −3 (away from zero on a tie)
- **Round half to even** (a.k.a. banker's rounding): 2.5 → 2, 3.5 → 4 (tie goes to the even one)

Python's built-in `round()` and NumPy's `rint()` both use **round half to even**. So the
*natural* thing any programmer (or AI) writes is subtly different from what TFLite actually
does.

TFLite's real algorithm (called **gemmlowp**) uses **round half away from zero**, plus a
tiny extra correction when the number is negative. If you get this one detail wrong, your
answer is off by exactly **1** (one **ULP** — one unit in the last place) — but *only* on
the rows where a value lands exactly on a halfway point. Most rows look perfect. A handful
are silently wrong.

**That is the whole trap:** the answer is off by 1 on ~15 of 48 rows, there's no error
message, and we gave the model no "sample answers" to check itself against.

---

## 4. Why this beat the AI (the interesting part)

When we ran the real **oracle** test, all 5 attempts by Opus 4.8 failed — and they *all
failed the same way*. The analysis was fascinating:

- The AI **correctly** rebuilt the entire pipeline: the multiply-add, the zero-points, the
  clamps, even most of the tricky rounding.
- Then it did something very human: it **remembered the C++ constant** from TensorFlow's
  source code (it has read gemmlowp during training) — but it paired that C++ constant with
  Python's division, which rounds differently than C++'s. C++ shifts (floors); Python's
  `//` and `int()` truncate toward zero. On negative numbers those disagree by 1.
- Result: every model got **33 of 48 rows right and 15 wrong, off by +1**, identical across
  all 5 runs.

The deep lesson (this is the reusable insight):

> The AI wasn't beaten by a *hard* problem. It was beaten by a **tiny detail of real-world
> knowledge it half-remembered and got slightly wrong** — with nothing in the environment
> to tell it it was wrong. It "knew" gemmlowp, retrieved the constant, and confidently
> shipped a 1-in-a-billion-looking bug.

Things the AI is GREAT at (so these never make a hard task): anything it can *derive* from
scratch (linear algebra, standard algorithms), anything you *spell out* in the instructions,
and anything it can *look up and copy*. Things that beat it: a subtle, specialized convention
it operationalizes slightly wrong, silently.

---

## 5. How the task is graded (fairly)

- We ship the **exact correct** gemmlowp code as the hidden **oracle** — it scores a perfect
  1.0, proving the task is solvable.
- We grade **exact match** on the whole-number outputs. Because the outputs are integers
  (not decimals), exact match is fair — there's no "close enough" to argue about.
- We give **no sample outputs** (so the AI can't check its rounding) and **no reference
  program** in the environment (so it can't just run the right answer). But the *method* is
  a public standard (TFLite), and the AI has open internet — so a real expert who reads the
  TFLite spec carefully would get it right. That's what makes it **hard but fair**.

---

## 6. The one-line mental model to keep

**"Reproduce a real, published computation *exactly*, where the popular shortcut is
*almost* right, and nothing tells you when you're wrong."** That single sentence is the
recipe that took the frontier model to 0/5.

---

## 7. Glossary — every term, in plain words

**AI / eval conventions**
- **oracle** — the reference correct solution the task author ships. If the oracle passes
  the grader, the task is provably solvable. (In our task: the exact gemmlowp code.)
- **nop agent** — "no-operation": an agent that does nothing. It must *fail* the grader,
  proving the grader isn't handing out free passes.
- **pass@k** — run the AI on the task *k* times; count how many it solves. "pass@5 = 0/5"
  means it was run 5 times and solved 0. For Dynamo, a *good* task has the AI **fail** most
  runs.
- **avg@k** — the average score across *k* runs (0.0 to 1.0). avg@5 = 0.000 means every run
  scored zero.
- **valid failure** — the AI genuinely tried, finished, and got the wrong answer (good). As
  opposed to failing because of a timeout or crash (doesn't count).
- **reward** — the grader's score, 1.0 (pass) or 0.0 (fail), written to a reward file.
- **verifier / grader** — the automated test that decides pass/fail by checking the agent's
  output file.
- **ULP** — "unit in the last place": the smallest possible difference between two adjacent
  representable numbers. "Off by 1 ULP" = off by the tiniest possible amount (here, ±1).

**Neural network basics**
- **neural network** — a stack of layers that turn an input list of numbers into an output
  list, via repeated multiply-add.
- **MLP (multi-layer perceptron)** — the simplest kind of neural network: fully-connected
  layers one after another. Our task uses a 2-layer MLP.
- **layer** — one multiply-add-then-transform stage. Takes a vector in, gives a vector out.
- **fully-connected / dense layer** — a layer where every output connects to every input
  (the plain matrix-multiply kind).
- **weights** — the learned multipliers inside a layer (a matrix of numbers).
- **bias** — a constant added to each output of a layer (a vector).
- **activation** — the output values of a layer after its transform; also the input to the
  next layer.
- **input vector / row** — one example fed to the network (here, a list of 16 numbers 0–255).
- **forward pass / inference** — running an input through the network to get an output. (No
  learning happens; the weights are fixed. "Inference" = "using a trained model.")
- **logits** — the raw output numbers of the final layer, before turning them into a decision.
- **argmax** — "which position has the biggest value?" Used to turn logits into a predicted
  class. (Not central to this task, but standard.)
- **ReLU** — "rectified linear unit": an activation function that clamps negatives to zero
  (`max(0, x)`). In the quantized world it clamps to the zero-point instead of 0.
- **clamp** — force a value to stay within a min/max range (e.g. keep it in [0, 255]).

**Quantization**
- **quantization** — converting a model from decimals (float) to small integers (int8) so it
  runs fast on phones/edge chips.
- **int8** — an 8-bit signed integer, range −128 to 127. **int32** — a 32-bit integer, used
  for the big running totals inside a layer.
- **uint8** — unsigned 8-bit integer, range 0 to 255 (our input pixels are uint8).
- **scale** — the real-world value of one integer step. `real ≈ scale × (int − zero_point)`.
- **zero-point** — the integer that stands for real value 0 (lets you represent asymmetric
  ranges without wasting bits).
- **requantization** — after a layer's int32 total, shrinking it back to int8 range by
  multiplying by a fraction and rounding — using only integers.
- **fixed-point** — representing a fraction using integers and a shift, instead of a float.
  TFLite stores the requant fraction as `multiplier × 2^shift / 2^31`.
- **multiplier / shift** — the two integers that encode the requant fraction per output
  channel.
- **per-channel** — each output neuron gets its own multiplier/shift (more accurate than one
  shared value).

**The TFLite rounding internals (the actual trap)**
- **TFLite (TensorFlow Lite)** — Google's framework for running models on phones/edge devices.
  Defines the exact integer math a quantized model must use.
- **gemmlowp** — the low-precision integer matrix-math library TFLite uses. Its rounding
  rules are the "standard" we made the AI reproduce.
- **SRDHM (SaturatingRoundingDoublingHighMul)** — gemmlowp's step that multiplies two int32s
  and keeps the high half, rounding to nearest (ties away from zero), with an overflow guard.
  This is where the AIs slipped (C++ vs Python rounding).
- **RDBPOT (RoundingDivideByPOT)** — "rounding divide by power of two": gemmlowp's step that
  divides by 2^n, rounding to nearest, ties away from zero — with a `+1` correction when the
  number is negative. (The reviewer caught us omitting this correction; fixing it made the
  task harder.)
- **round half to even (banker's rounding)** — on a tie, round to the nearest *even* number.
  Python's `round()` and NumPy default. The *wrong* convention here — the trap.
- **round half away from zero** — on a tie, round away from zero (2.5→3, −2.5→−3). What
  gemmlowp actually does. The *right* convention.
- **arithmetic right shift (`>>`)** — divide by a power of two, rounding *down* (toward
  −infinity) for negatives. C++ uses this. Python's `>>` on ints matches it. But Python's
  `//` and `int()` truncate *toward zero* — the mismatch that broke all 5 AI runs.

---

## 8. If you want to go deeper tomorrow

1. Open `task/solution/solve.py` in the task repo and read `srdhm` and `rdbpot` alongside
   this glossary — you'll now recognize every line.
2. Compare it to the "naive" version we tested (round-half-to-even) — the whole difference is
   a couple of characters, and that difference is the entire task.
3. Read §16 of `DYNAMO-REFERENCE.md` for the *general* recipe this task is an instance of.
4. Search "gemmlowp RoundingDivideByPOT" — you'll find the real C++ and see why the negative
   correction exists.
