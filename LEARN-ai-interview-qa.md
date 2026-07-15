# AI Interview Prep — Q&A study doc

Built from the concepts used in the Project Dynamo tasks. Plain language first, then
interview-ready answers. Each module: **Concepts** (taught) → **Q&A** (drill) →
**Interview one-liners** (what to actually say).

Modules: 1 NN & inference foundations · 2 Quantization · 3 Rounding/porting crux ·
4 Interpretability & attribution · 5 Piecewise-linear geometry · 6 Evaluation & benchmarking ·
7 What makes a task hard for an LLM.

---

## Module 1 — Neural network & inference foundations

### Concepts (plain language)

A **neural network** is a function that turns an input list of numbers into an output list
of numbers, by repeated **multiply-add-then-bend**.

- **Layer:** one stage. It takes a vector `a` (the input to that layer), multiplies it by a
  **weight matrix** `W`, adds a **bias** vector `b`, giving `pre = W·a + b` ("pre-activation"),
  then applies a **non-linearity** (an "activation function") to bend it.
- **Weights & bias:** the *learned* numbers. Weights scale each input's influence; the bias
  shifts the result. Training sets these; **inference** (using the model) keeps them fixed.
- **Fully-connected / dense / MLP layer:** every output connects to every input — it's just
  a matrix multiply. **MLP** = multi-layer perceptron = a stack of these.
- **Activation function:** the "bend" that makes the network non-linear (without it, stacking
  layers collapses to one big matrix multiply — no extra power). The most common is **ReLU**:
  `ReLU(x) = max(0, x)` — pass positives through, clamp negatives to 0.
- **Forward pass / inference:** run the input through all layers to get the output. No
  learning happens; you're *using* a trained model.
- **Logits:** the raw output numbers of the final layer, *before* turning them into a
  decision. For a classifier with 5 classes, you get 5 logits.
- **argmax:** "which position holds the biggest value?" `argmax(logits)` = the predicted
  class. (A tie is broken by a rule, e.g. lowest index.)
- **Clamp:** force a value into a range, `clamp(x, lo, hi)`. ReLU is a clamp with `lo=0`.

**The whole picture for a 2-hidden-layer classifier:**
```
input x → [W1·x+b1 → ReLU] → [W2·+b2 → ReLU] → [W_out·+b_out] → logits → argmax → class
```

### Q&A

**Q1. What is a neural network, in one sentence?**
A stack of layers that map an input vector to an output vector via repeated linear
transforms (weight-multiply + bias) separated by non-linear activation functions.

**Q2. What's the difference between training and inference?**
Training *learns* the weights by adjusting them to reduce a loss on data (backprop +
gradient descent). Inference *uses* the fixed, already-learned weights to compute an output
for a new input. Our tasks were pure inference — weights given, no learning.

**Q3. Why do we need a non-linear activation (like ReLU)? What breaks without it?**
Without a non-linearity, stacking linear layers is still just one linear function
(`W2(W1x) = (W2W1)x`), so depth adds no representational power. The non-linearity lets the
network approximate complex, non-linear functions.

**Q4. What is ReLU and why is it popular?**
`ReLU(x) = max(0, x)`. It's cheap, doesn't saturate for positive inputs (helping gradients
flow, avoiding the "vanishing gradient" problem of sigmoid/tanh), and induces useful
sparsity. Its "kink" at 0 makes ReLU networks **piecewise-linear** (Module 5).

**Q5. What are logits, and how do you get a class prediction from them?**
Logits are the raw final-layer scores before normalization. `argmax` over the logits gives
the predicted class. (Softmax would turn them into probabilities, but argmax of logits =
argmax of softmax, so you don't need softmax just to pick the class.)

**Q6. In `pre = W·a + b`, what are the shapes?**
If layer input `a` has `n_in` features and the layer has `n_out` neurons, then `W` is
`[n_out × n_in]`, `b` is length `n_out`, and `pre` is length `n_out`. `W[j][i]` is the
weight from input feature `i` to output neuron `j`.

**Q7. What does "the output layer is linear (not activated)" mean?**
The final layer computes `W_out·a + b_out` and stops — no ReLU/clamp — so it can output any
real number (logits can be negative or large). Activations are for hidden layers.

### Interview one-liners
- "An MLP is repeated affine transforms (`Wx+b`) with a non-linearity between them; without
  the non-linearity depth is pointless because linear∘linear is linear."
- "ReLU makes the network a **piecewise-linear** function — linear inside each activation
  region, with kinks where neurons switch on/off."
- "Inference is just the forward pass with frozen weights; logits → argmax → class."
