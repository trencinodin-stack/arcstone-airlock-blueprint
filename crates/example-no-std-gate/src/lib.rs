#![no_std]
#![forbid(unsafe_code)]
#![deny(clippy::wildcard_enum_match_arm)]

/// The valid zero discriminant represents Deny.
/// Raw bytes must be validated before conversion to Verdict.
#[repr(u8)]
#[derive(Clone, Copy)]
pub enum Verdict {
    Deny = 0,
    Allow = 1,
}

#[derive(Clone, Copy)]
pub enum Mode {
    Safe,
    Armed,
    Fault,
}

/// Pure, total, allocation-free admission gate (C_ops = 0, M_alloc = 0).
pub fn decide(mode: Mode, budget: u32, cost: u32) -> Verdict {
    match mode {
        Mode::Armed if cost <= budget => Verdict::Allow,
        Mode::Armed | Mode::Safe | Mode::Fault => Verdict::Deny,
    }
}
