# Changelog

## [0.8.0](https://github.com/future-agi/futureagi-sdk/compare/python-v0.7.0...python-v0.8.0) (2026-11-21)


### Features

* **sdkgen:** generate the platform SDK reference for docs.futureagi.com ([#42](https://github.com/future-agi/futureagi-sdk/issues/42)) ([d9625dc](https://github.com/future-agi/futureagi-sdk/commit/d9625dc2e150f82208b1cc586587f87477ce5f63))


### Bug Fixes

* handle UnboundLocalError in Prompt._handle_error on 400 responses ([5b8a98f](https://github.com/future-agi/futureagi-sdk/commit/5b8a98f8275812aa0e83afbf0929bf4dca126566))

## [0.7.0](https://github.com/future-agi/futureagi-sdk/compare/python-v0.6.14...python-v0.7.0) (2026-11-05)


### Features

* revamp eval template management routes and update namespace handling ([90e70a1](https://github.com/future-agi/futureagi-sdk/commit/90e70a1c800c96c3772a213035ad2412561a9659))
* **sdk:** add generated platform clients and guarded releases ([a2e781a](https://github.com/future-agi/futureagi-sdk/commit/a2e781a07d02bdb4b31c0328acd770408d2d5cd4))


### Bug Fixes

* custom eval resolution for evalId=0 and camelCase keys (TH-3610) ([866293e](https://github.com/future-agi/futureagi-sdk/commit/866293edb87362137bb2fc790f80d52a845bd3a8))
* custom eval resolution for evalId=0 and camelCase keys (TH-3610) ([7966bfa](https://github.com/future-agi/futureagi-sdk/commit/7966bfaa3ce6c7d45895f550282f9281cc40f92f))
* **datasets:** stop orphan datasets + exact by-name resolution ([1607f12](https://github.com/future-agi/futureagi-sdk/commit/1607f129bf50ba36c5120b86c0b498711b3e3d21))
* **datasets:** stop orphan datasets + exact by-name resolution (0.6.14) ([72cba35](https://github.com/future-agi/futureagi-sdk/commit/72cba3502206a3d5a114f52763c719dade4f589c))
* remove leaked credentials, restore null-safety and backward compat in dataset parsing ([8931496](https://github.com/future-agi/futureagi-sdk/commit/8931496fd3c9e0b3fe60925870e4079d8920a4a5))
