# \RunTestsEvalSummaryAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**SimulateRunTestsEvalSummaryComparisonList**](RunTestsEvalSummaryAPI.md#SimulateRunTestsEvalSummaryComparisonList) | **Get** /simulate/run-tests/{run_test_id}/eval-summary-comparison/ | Compare evaluation summaries
[**SimulateRunTestsEvalSummaryList**](RunTestsEvalSummaryAPI.md#SimulateRunTestsEvalSummaryList) | **Get** /simulate/run-tests/{run_test_id}/eval-summary/ | Get evaluation summary



## SimulateRunTestsEvalSummaryComparisonList

> EvalSummaryComparisonResponse SimulateRunTestsEvalSummaryComparisonList(ctx, runTestId).ExecutionIds(executionIds).Execute()

Compare evaluation summaries



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
	runTestId := "runTestId_example" // string | 
	executionIds := "executionIds_example" // string | JSON-encoded array of test execution UUIDs to compare. Example: [\"uuid1\",\"uuid2\"]. Must be URL-encoded.

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.RunTestsEvalSummaryAPI.SimulateRunTestsEvalSummaryComparisonList(context.Background(), runTestId).ExecutionIds(executionIds).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `RunTestsEvalSummaryAPI.SimulateRunTestsEvalSummaryComparisonList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsEvalSummaryComparisonList`: EvalSummaryComparisonResponse
	fmt.Fprintf(os.Stdout, "Response from `RunTestsEvalSummaryAPI.SimulateRunTestsEvalSummaryComparisonList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsEvalSummaryComparisonListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **executionIds** | **string** | JSON-encoded array of test execution UUIDs to compare. Example: [\&quot;uuid1\&quot;,\&quot;uuid2\&quot;]. Must be URL-encoded. | 

### Return type

[**EvalSummaryComparisonResponse**](EvalSummaryComparisonResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsEvalSummaryList

> EvalSummaryResponse SimulateRunTestsEvalSummaryList(ctx, runTestId).ExecutionId(executionId).Execute()

Get evaluation summary



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
	runTestId := "runTestId_example" // string | 
	executionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string | UUID of a specific test execution to scope the summary to. If omitted, aggregates across all executions. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.RunTestsEvalSummaryAPI.SimulateRunTestsEvalSummaryList(context.Background(), runTestId).ExecutionId(executionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `RunTestsEvalSummaryAPI.SimulateRunTestsEvalSummaryList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsEvalSummaryList`: EvalSummaryResponse
	fmt.Fprintf(os.Stdout, "Response from `RunTestsEvalSummaryAPI.SimulateRunTestsEvalSummaryList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsEvalSummaryListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **executionId** | **string** | UUID of a specific test execution to scope the summary to. If omitted, aggregates across all executions. | 

### Return type

[**EvalSummaryResponse**](EvalSummaryResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

