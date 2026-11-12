# Bare-Metal `#![no_std]` Patterns & Aeneas Safe Subset Guide

## 1. Supported `v0.1.0` Sequential Safe Subset
Aeneas translates Charon LLBC into pure functional Coq models. Keep extracted kernels inside this sequential safe fragment:
- **Zero Heap Allocation (`M_alloc = 0`):** Use `#![no_std]` with zero external dependencies and no `alloc` crate.
- **Minimal Derives (`Clone, Copy` only):** Avoid `#[derive(Debug)]` or `#[derive(PartialEq)]` on extracted types so `core::fmt` and discriminant intrinsics do not enter MIR.
- **Explicit Fail-Closed Enum Discriminants:** Assign `Deny = 0` on decision enums and enforce `#![deny(clippy::wildcard_enum_match_arm)]` so newly added variants require explicit policy handling.
- **Library-Only Extraction:** Run `charon cargo --preset=aeneas --locked -- --lib` so host-only integration tests (`tests/*.rs`) remain outside the extracted LLBC graph.

## 2. Roadmap for `v0.2.0` & `v0.3.0` Patterns
- **Fixed-Size Stack Buffers (`[u8; N]`, `v0.2.0`):** Use `.get(i)` with `None => Verdict::Deny` or index-bounded `while i < N` loops with explicit decreasing measures rather than unchecked `buf[i]` indexing.
- **Checked & Saturating Arithmetic (`v0.2.0`):** Map `checked_add`/`checked_sub` overflow (`None`) to `Verdict::Deny`; reserve `saturating_add` for metrics where clamping preserves safety invariants.
- **Pure Value State Machines (`v0.2.0`):** Model transitions as `fn step(state: State, event: Event) -> (State, Verdict)` over `Copy` values rather than `&mut self` borrows.
- **Unsafe MMIO / Hardware Boundaries (`v0.3.0`):** Isolate volatile register reads in a separate platform adapter (`crates/example-mmio-shim`) excluded from extraction, passing plain value structs into the `#[forbid(unsafe_code)]` decision core.
