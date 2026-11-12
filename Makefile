.PHONY: quick lint check-pins airlock test-receipts clean

quick:
	cargo fmt --all -- --check
	cargo clippy -p example-no-std-gate --all-targets -- -D warnings
	cargo test -p example-no-std-gate --locked
	cargo build -p example-no-std-gate --locked --target thumbv7em-none-eabihf

lint:
	@! grep -rnE '(charon|aeneas|coqchk|Admitted)' crates/
	@test ! -f .zenodo.json
	@test ! -f crates/example-no-std-gate/build.rs

check-pins:
	./airlock/scripts/check-pins.sh

airlock: check-pins
	./airlock/scripts/run-airlock.sh

test-receipts:
	python3 -m unittest discover -s airlock/tests -p 'test_*.py' -v

clean:
	cargo clean
	rm -rf .airlock-work out
