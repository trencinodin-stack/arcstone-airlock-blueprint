use example_no_std_gate::{decide, Mode, Verdict};

#[test]
fn safe_and_fault_modes_always_deny() {
    for &(budget, cost) in &[(0, 0), (10, 0), (10, 10), (10, 11), (u32::MAX, 0), (u32::MAX, u32::MAX)] {
        assert_eq!(decide(Mode::Safe, budget, cost) as u8, Verdict::Deny as u8);
        assert_eq!(decide(Mode::Fault, budget, cost) as u8, Verdict::Deny as u8);
    }
}

#[test]
fn armed_mode_enforces_budget_boundary() {
    // Exact boundary: cost == budget -> Allow
    assert_eq!(decide(Mode::Armed, 0, 0) as u8, Verdict::Allow as u8);
    assert_eq!(decide(Mode::Armed, 100, 100) as u8, Verdict::Allow as u8);
    assert_eq!(decide(Mode::Armed, u32::MAX, u32::MAX) as u8, Verdict::Allow as u8);

    // Strictly within budget: cost < budget -> Allow
    assert_eq!(decide(Mode::Armed, 1, 0) as u8, Verdict::Allow as u8);
    assert_eq!(decide(Mode::Armed, u32::MAX, u32::MAX - 1) as u8, Verdict::Allow as u8);

    // Exceeds budget: cost > budget -> Deny
    assert_eq!(decide(Mode::Armed, 0, 1) as u8, Verdict::Deny as u8);
    assert_eq!(decide(Mode::Armed, 100, 101) as u8, Verdict::Deny as u8);
    assert_eq!(decide(Mode::Armed, u32::MAX - 1, u32::MAX) as u8, Verdict::Deny as u8);
}
