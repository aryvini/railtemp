.PHONY: build test

build:
	uv run maturin develop

test:
	cargo test --manifest-path src/railtemp_core/Cargo.toml
	uv run pytest
