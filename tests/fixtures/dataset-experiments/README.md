# Dataset and experiment fixtures

`run-comparison-trial-stability.json` is a synthetic contract fixture, not a
captured HTTP response. It follows the scenario and response schema in core
`32ea09fa63d0ffa2e5178d1ede94f0f8b5796b7a`: one example has two assessed
trials (`[0, 1]` versus `[0.5, 0.5]`), and a second example is missing both
planned trials on both sides. It checks typed decoding and wire preservation,
including the difference between zero observed spread and missing statistics.

These SDK transport tests do not certify backend calculations or a hosted API.
