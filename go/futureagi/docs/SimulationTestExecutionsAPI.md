# \SimulationTestExecutionsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**CancelTestExecution**](SimulationTestExecutionsAPI.md#CancelTestExecution) | **Post** /simulate/test-executions/{test_execution_id}/cancel/ | 
[**GetTestExecution**](SimulationTestExecutionsAPI.md#GetTestExecution) | **Get** /simulate/test-executions/{test_execution_id}/ | 
[**GetTestExecutionAnalytics**](SimulationTestExecutionsAPI.md#GetTestExecutionAnalytics) | **Get** /simulate/test-executions/{test_execution_id}/analytics/ | 
[**GetTestExecutionKpis**](SimulationTestExecutionsAPI.md#GetTestExecutionKpis) | **Get** /simulate/test-executions/{test_execution_id}/kpis/ | 
[**GetTestExecutionPerformanceSummary**](SimulationTestExecutionsAPI.md#GetTestExecutionPerformanceSummary) | **Get** /simulate/test-executions/{test_execution_id}/performance-summary/ | 
[**GetTestExecutionTranscripts**](SimulationTestExecutionsAPI.md#GetTestExecutionTranscripts) | **Get** /simulate/test-executions/{test_execution_id}/transcripts/ | 
[**ListTestExecutions**](SimulationTestExecutionsAPI.md#ListTestExecutions) | **Get** /simulate/api/test-executions/ | 



## CancelTestExecution

> CancelTestExecutionResponse CancelTestExecution(ctx, testExecutionId).Body(body).Execute()





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
	testExecutionId := "testExecutionId_example" // string | 
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationTestExecutionsAPI.CancelTestExecution(context.Background(), testExecutionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationTestExecutionsAPI.CancelTestExecution``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CancelTestExecution`: CancelTestExecutionResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationTestExecutionsAPI.CancelTestExecution`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiCancelTestExecutionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**CancelTestExecutionResponse**](CancelTestExecutionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTestExecution

> TestExecutionDetailResponse GetTestExecution(ctx, testExecutionId).Search(search).Filters(filters).RowGroups(rowGroups).GroupKeys(groupKeys).Page(page).Limit(limit).Execute()





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
	testExecutionId := "testExecutionId_example" // string | 
	search := "search_example" // string |  (optional) (default to "")
	filters := "filters_example" // string |  (optional) (default to "[]")
	rowGroups := "rowGroups_example" // string |  (optional) (default to "[]")
	groupKeys := "groupKeys_example" // string |  (optional) (default to "[]")
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional) (default to 30)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationTestExecutionsAPI.GetTestExecution(context.Background(), testExecutionId).Search(search).Filters(filters).RowGroups(rowGroups).GroupKeys(groupKeys).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationTestExecutionsAPI.GetTestExecution``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTestExecution`: TestExecutionDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationTestExecutionsAPI.GetTestExecution`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetTestExecutionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **search** | **string** |  | [default to &quot;&quot;]
 **filters** | **string** |  | [default to &quot;[]&quot;]
 **rowGroups** | **string** |  | [default to &quot;[]&quot;]
 **groupKeys** | **string** |  | [default to &quot;[]&quot;]
 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | [default to 30]

### Return type

[**TestExecutionDetailResponse**](TestExecutionDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTestExecutionAnalytics

> TestExecutionAnalytics GetTestExecutionAnalytics(ctx, testExecutionId).Execute()





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
	testExecutionId := "testExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationTestExecutionsAPI.GetTestExecutionAnalytics(context.Background(), testExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationTestExecutionsAPI.GetTestExecutionAnalytics``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTestExecutionAnalytics`: TestExecutionAnalytics
	fmt.Fprintf(os.Stdout, "Response from `SimulationTestExecutionsAPI.GetTestExecutionAnalytics`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetTestExecutionAnalyticsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**TestExecutionAnalytics**](TestExecutionAnalytics.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTestExecutionKpis

> RunTestKPIsResponse GetTestExecutionKpis(ctx, testExecutionId).Execute()





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
	testExecutionId := "testExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationTestExecutionsAPI.GetTestExecutionKpis(context.Background(), testExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationTestExecutionsAPI.GetTestExecutionKpis``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTestExecutionKpis`: RunTestKPIsResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationTestExecutionsAPI.GetTestExecutionKpis`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetTestExecutionKpisRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**RunTestKPIsResponse**](RunTestKPIsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTestExecutionPerformanceSummary

> PerformanceSummary GetTestExecutionPerformanceSummary(ctx, testExecutionId).Execute()





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
	testExecutionId := "testExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationTestExecutionsAPI.GetTestExecutionPerformanceSummary(context.Background(), testExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationTestExecutionsAPI.GetTestExecutionPerformanceSummary``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTestExecutionPerformanceSummary`: PerformanceSummary
	fmt.Fprintf(os.Stdout, "Response from `SimulationTestExecutionsAPI.GetTestExecutionPerformanceSummary`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetTestExecutionPerformanceSummaryRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PerformanceSummary**](PerformanceSummary.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTestExecutionTranscripts

> TestExecutionTranscriptsResponse GetTestExecutionTranscripts(ctx, testExecutionId).Execute()





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
	testExecutionId := "testExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationTestExecutionsAPI.GetTestExecutionTranscripts(context.Background(), testExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationTestExecutionsAPI.GetTestExecutionTranscripts``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTestExecutionTranscripts`: TestExecutionTranscriptsResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationTestExecutionsAPI.GetTestExecutionTranscripts`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetTestExecutionTranscriptsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**TestExecutionTranscriptsResponse**](TestExecutionTranscriptsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListTestExecutions

> []TestExecution ListTestExecutions(ctx).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationTestExecutionsAPI.ListTestExecutions(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationTestExecutionsAPI.ListTestExecutions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListTestExecutions`: []TestExecution
	fmt.Fprintf(os.Stdout, "Response from `SimulationTestExecutionsAPI.ListTestExecutions`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiListTestExecutionsRequest struct via the builder pattern


### Return type

[**[]TestExecution**](TestExecution.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

