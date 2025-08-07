@echo off
cargo build --manifest-path ../cse_server/Cargo.toml --target-dir ../cse_server/ --target wasm32-unknown-unknown
spacetime publish -c cse-server -b C:\Projects\CyberSynEve\cse_server\wasm32-wasip1\debug\spacetime_module.wasm