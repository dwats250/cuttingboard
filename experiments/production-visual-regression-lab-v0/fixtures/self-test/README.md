# Browser self-test fixtures

These standalone documents intentionally encode raw browser conditions for visual-regression checks. They contain no runner, external assets, scripts, or network dependencies.

- `horizontal-overflow.html`: at a 360px viewport, the document has `scrollWidth > clientWidth` because the body is at least 800px wide.
- `cell-clipping.html`: the visible `[data-lab-key="critical"]` element has a fixed narrow width, `white-space: nowrap`, `overflow: hidden`, and text whose `scrollWidth > clientWidth`.
- `wrapped-readable.html`: the same critical key is narrow but wraps normally, has automatic height, and does not clip overflow.
- `hidden-critical.html`: the critical element exists but has `visibility: hidden`.
- `wrong-order.html`: the `second` keyed element occurs before `first` in document order.
- `missing-expected.html`: `first` is present and no element is keyed `missing`.
- `breakpoint.html`: `[data-lab-key="boundary"]` has different computed `--lab-boundary` values and widths at `max-width: 430px` versus 431px and wider.
