# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 4.0.2

([Full Changelog](https://github.com/emscripten-forge/empack/compare/v4.0.1...897c502bea3fcb0eb837784a1dd679a1622cef6a))

### Merged PRs

- Revert "Change list-of-POSIX-paths to list-of-strings in yield of `iterate_pip_pkg_record()` function" [#106](https://github.com/emscripten-forge/empack/pull/106) ([@martinRenou](https://github.com/martinRenou))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/emscripten-forge/empack/graphs/contributors?from=2024-09-02&to=2024-09-05&type=c))

[@martinRenou](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3AmartinRenou+updated%3A2024-09-02..2024-09-05&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 4.0.1

([Full Changelog](https://github.com/emscripten-forge/empack/compare/v4.0.0...e2e881969207b2454f616e182ce68b4936f1d48b))

### Bugs fixed

- Change list-of-POSIX-paths to list-of-strings in yield of `iterate_pip_pkg_record()` function [#104](https://github.com/emscripten-forge/empack/pull/104) ([@michaelweinold](https://github.com/michaelweinold))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/emscripten-forge/empack/graphs/contributors?from=2024-06-17&to=2024-09-02&type=c))

[@DerThorsten](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3ADerThorsten+updated%3A2024-06-17..2024-09-02&type=Issues) | [@martinRenou](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3AmartinRenou+updated%3A2024-06-17..2024-09-02&type=Issues) | [@michaelweinold](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3Amichaelweinold+updated%3A2024-06-17..2024-09-02&type=Issues)

## 4.0.0

([Full Changelog](https://github.com/emscripten-forge/empack/compare/v3.3.4...d3360ca7a178ab442fc68c2e59d894b34923bb55))

The main highlight of this release is the new filtering logic. We used to filter out many files from the packed environment due to using very restrictive include rules. We now include **everything by default** fixing many reporting issues concerning package data. We only filter out files if there are explicit rules for filtering them.

### Enhancements made

- Filtering: Include everything by default [#98](https://github.com/emscripten-forge/empack/pull/98) ([@martinRenou](https://github.com/martinRenou))

### Maintenance and upkeep improvements

- Fix backward compat on config files [#102](https://github.com/emscripten-forge/empack/pull/102) ([@martinRenou](https://github.com/martinRenou))
- Update CI to using latest emscripten-forge platform and Python version [#99](https://github.com/emscripten-forge/empack/pull/99) ([@martinRenou](https://github.com/martinRenou))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/emscripten-forge/empack/graphs/contributors?from=2024-05-21&to=2024-06-17&type=c))

[@DerThorsten](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3ADerThorsten+updated%3A2024-05-21..2024-06-17&type=Issues) | [@martinRenou](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3AmartinRenou+updated%3A2024-05-21..2024-06-17&type=Issues)

## 3.3.4

([Full Changelog](https://github.com/emscripten-forge/empack/compare/v3.3.3...784118763a5fd903569df7b1ef686a9c54eaa1e4))

### Enhancements made

- Add Include/Exclude Patterns for `pint` Package to `empack_config` (#2) [#97](https://github.com/emscripten-forge/empack/pull/97) ([@michaelweinold](https://github.com/michaelweinold))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/emscripten-forge/empack/graphs/contributors?from=2024-04-26&to=2024-05-21&type=c))

[@martinRenou](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3AmartinRenou+updated%3A2024-04-26..2024-05-21&type=Issues) | [@michaelweinold](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3Amichaelweinold+updated%3A2024-04-26..2024-05-21&type=Issues)

## 3.3.3

([Full Changelog](https://github.com/emscripten-forge/empack/compare/v3.3.2...d6ae4fc42fe79aa7a60f4b70fa72245e1e7566a3))

### Enhancements made

- use abspath when comparing dirs [#95](https://github.com/emscripten-forge/empack/pull/95) ([@DerThorsten](https://github.com/DerThorsten))

### Bugs fixed

- Fix rules for pyvis [#96](https://github.com/emscripten-forge/empack/pull/96) ([@martinRenou](https://github.com/martinRenou))
- use abspath when comparing dirs [#95](https://github.com/emscripten-forge/empack/pull/95) ([@DerThorsten](https://github.com/DerThorsten))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/emscripten-forge/empack/graphs/contributors?from=2024-02-05&to=2024-04-26&type=c))

[@DerThorsten](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3ADerThorsten+updated%3A2024-02-05..2024-04-26&type=Issues) | [@martinRenou](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3AmartinRenou+updated%3A2024-02-05..2024-04-26&type=Issues)

## 3.3.2

([Full Changelog](https://github.com/emscripten-forge/empack/compare/v3.3.1...d742539ef5f7fdf4afb94561d4026a7976ebc629))

### Enhancements made

- Update config for urllib and certifi [#94](https://github.com/emscripten-forge/empack/pull/94) ([@martinRenou](https://github.com/martinRenou))

### Other merged PRs

- Update CI script [#93](https://github.com/emscripten-forge/empack/pull/93) ([@trungleduc](https://github.com/trungleduc))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/emscripten-forge/empack/graphs/contributors?from=2024-01-29&to=2024-02-05&type=c))

[@martinRenou](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3AmartinRenou+updated%3A2024-01-29..2024-02-05&type=Issues) | [@trungleduc](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3Atrungleduc+updated%3A2024-01-29..2024-02-05&type=Issues)

## 3.3.1

([Full Changelog](https://github.com/emscripten-forge/empack/compare/v3.3.0...d8d48c6779696aac0a695fe162fd7c38f698073e))

### Enhancements made

- fixes for voici windows build [#90](https://github.com/emscripten-forge/empack/pull/90) ([@pjaggi1](https://github.com/pjaggi1))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/emscripten-forge/empack/graphs/contributors?from=2024-01-03&to=2024-01-29&type=c))

[@pjaggi1](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3Apjaggi1+updated%3A2024-01-03..2024-01-29&type=Issues)

## 3.3.0

([Full Changelog](https://github.com/emscripten-forge/empack/compare/3.2.0...05620f8cb46b1455e1ac97050425356fe4346bac))

### Enhancements made

- Allow packing extra files into the output environment [#87](https://github.com/emscripten-forge/empack/pull/87) ([@DerThorsten](https://github.com/DerThorsten))

### Maintenance and upkeep improvements

- Releaser: Remove non needed step [#89](https://github.com/emscripten-forge/empack/pull/89) ([@martinRenou](https://github.com/martinRenou))
- Setup releaser [#88](https://github.com/emscripten-forge/empack/pull/88) ([@martinRenou](https://github.com/martinRenou))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/emscripten-forge/empack/graphs/contributors?from=2023-11-16&to=2024-01-03&type=c))

[@DerThorsten](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3ADerThorsten+updated%3A2023-11-16..2024-01-03&type=Issues) | [@martinRenou](https://github.com/search?q=repo%3Aemscripten-forge%2Fempack+involves%3AmartinRenou+updated%3A2023-11-16..2024-01-03&type=Issues)
