# \SimulationsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**GetSimulationAnalytics**](SimulationsAPI.md#GetSimulationAnalytics) | **Get** /sdk/api/v1/simulation/analytics/ | GET /simulation/analytics/
[**ListSimulationMetrics**](SimulationsAPI.md#ListSimulationMetrics) | **Get** /sdk/api/v1/simulation/metrics/ | GET /simulation/metrics/
[**ListSimulationRuns**](SimulationsAPI.md#ListSimulationRuns) | **Get** /sdk/api/v1/simulation/runs/ | GET /simulation/runs/



## GetSimulationAnalytics

> SDKSimulationAnalyticsResponse GetSimulationAnalytics(ctx).RunTestName(runTestName).ExecutionId(executionId).EvalName(evalName).Summary(summary).Execute()

GET /simulation/analytics/



### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
	openapiclient "github.com/future-agi/futureagi-sdk/go/futureagi"
)

func main() {
	runTestName := "runTestName_example" // string |  (optional)
	executionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	evalName := "evalName_example" // string |  (optional)
	summary := true // bool |  (optional) (default to true)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationsAPI.GetSimulationAnalytics(context.Background()).RunTestName(runTestName).ExecutionId(executionId).EvalName(evalName).Summary(summary).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationsAPI.GetSimulationAnalytics``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetSimulationAnalytics`: SDKSimulationAnalyticsResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationsAPI.GetSimulationAnalytics`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiGetSimulationAnalyticsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **runTestName** | **string** |  | 
 **executionId** | **string** |  | 
 **evalName** | **string** |  | 
 **summary** | **bool** |  | [default to true]

### Return type

[**SDKSimulationAnalyticsResponse**](SDKSimulationAnalyticsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListSimulationMetrics

> SDKSimulationMetricsResponse ListSimulationMetrics(ctx).RunTestName(runTestName).ExecutionId(executionId).CallExecutionId(callExecutionId).Execute()

GET /simulation/metrics/



### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
	openapiclient "github.com/future-agi/futureagi-sdk/go/futureagi"
)

func main() {
	runTestName := "runTestName_example" // string |  (optional)
	executionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	callExecutionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationsAPI.ListSimulationMetrics(context.Background()).RunTestName(runTestName).ExecutionId(executionId).CallExecutionId(callExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationsAPI.ListSimulationMetrics``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListSimulationMetrics`: SDKSimulationMetricsResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationsAPI.ListSimulationMetrics`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListSimulationMetricsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **runTestName** | **string** |  | 
 **executionId** | **string** |  | 
 **callExecutionId** | **string** |  | 

### Return type

[**SDKSimulationMetricsResponse**](SDKSimulationMetricsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListSimulationRuns

> SDKSimulationRunsResponse ListSimulationRuns(ctx).RunTestName(runTestName).ExecutionId(executionId).CallExecutionId(callExecutionId).EvalName(evalName).Summary(summary).Execute()

GET /simulation/runs/



### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
	openapiclient "github.com/future-agi/futureagi-sdk/go/futureagi"
)

func main() {
	runTestName := "runTestName_example" // string |  (optional)
	executionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	callExecutionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	evalName := "evalName_example" // string |  (optional)
	summary := true // bool |  (optional) (default to false)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationsAPI.ListSimulationRuns(context.Background()).RunTestName(runTestName).ExecutionId(executionId).CallExecutionId(callExecutionId).EvalName(evalName).Summary(summary).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationsAPI.ListSimulationRuns``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListSimulationRuns`: SDKSimulationRunsResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationsAPI.ListSimulationRuns`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListSimulationRunsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **runTestName** | **string** |  | 
 **executionId** | **string** |  | 
 **callExecutionId** | **string** |  | 
 **evalName** | **string** |  | 
 **summary** | **bool** |  | [default to false]

### Return type

[**SDKSimulationRunsResponse**](SDKSimulationRunsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

