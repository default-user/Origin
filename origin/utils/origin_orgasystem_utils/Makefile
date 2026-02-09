.PHONY: all build test fmt clippy e2e release clean

all: fmt clippy test e2e

build:
	cargo build --workspace

test:
	cargo test --workspace

fmt:
	cargo fmt --all

fmt-check:
	cargo fmt --all -- --check

clippy:
	cargo clippy --workspace --all-targets -- -D warnings

e2e:
	cargo run --bin originctl -- e2e \
		--repo-root ./fixtures/sample_tree \
		--seed ./fixtures/sample_tree/spec/seed/denotum.seed.2i.yaml

release:
	cargo build --release --bin originctl
	@echo "Binary: target/release/originctl"
	@ls -lh target/release/originctl

clean:
	cargo clean
