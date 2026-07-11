# Build And Delivery

PL1CompInPy includes a `Makefile` for repeatable local checks, sample compiler outputs, binary container generation, and delivery packaging.

## Main Commands

```bash
make help
make compile
make docs
make test
make test-binary
make examples
make check
make build-text
make build-binaries
make build-libraries
make deliver
```

## Delivery Sequence

The complete delivery sequence is:

```bash
make deliver
```

That target:

- removes generated build and distribution folders
- compiles Python sources and tests for syntax validation
- regenerates `docs/API.md`
- runs the full unit test suite
- runs dedicated binary compile/result tests
- runs example parsing/compilation checks
- emits sample Python, JVM-style, and .NET IL text outputs
- emits sample PE, ELF, and Mach-O binary containers
- emits sample static/shared library containers
- writes `dist/PL1CompInPy-delivery.tar.gz` with the source tree and generated `build/` artifacts

## Binary Test Contract

The dedicated binary tests compile PL/I source into binary container artifacts and verify:

- platform signatures such as `MZ`, `ELF`, and Mach-O magic bytes
- embedded PL1 runtime-link manifests
- source-derived machine-code bytes for the current starter native encoders
- the same source program's semantic result through the direct runtime visitor

The current binary emitters are starter executable/container writers. They verify lowering and container formation; full host execution through platform linkers remains a future integration-test layer.
