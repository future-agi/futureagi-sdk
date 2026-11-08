# \ExperimentsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**CompareExperiments**](ExperimentsAPI.md#CompareExperiments) | **Post** /model-hub/experiments/v2/{experiment_id}/compare-experiments/ | 
[**CreateExperiment**](ExperimentsAPI.md#CreateExperiment) | **Post** /model-hub/experiments/v2/ | 
[**DeleteExperiments**](ExperimentsAPI.md#DeleteExperiments) | **Delete** /model-hub/experiments/v2/delete/ | 
[**DownloadExperiment**](ExperimentsAPI.md#DownloadExperiment) | **Get** /model-hub/experiments/v2/{experiment_id}/download/ | 
[**GetExperiment**](ExperimentsAPI.md#GetExperiment) | **Get** /model-hub/experiments/v2/{experiment_id}/ | 
[**GetExperimentJsonSchema**](ExperimentsAPI.md#GetExperimentJsonSchema) | **Get** /model-hub/experiments/v2/{experiment_id}/json-schema/ | 
[**GetExperimentRow**](ExperimentsAPI.md#GetExperimentRow) | **Get** /model-hub/experiments/v2/{experiment_id}/rows/{row_id}/ | 
[**GetExperimentStats**](ExperimentsAPI.md#GetExperimentStats) | **Get** /model-hub/experiments/v2/{experiment_id}/stats/ | 
[**ListExperimentComparisons**](ExperimentsAPI.md#ListExperimentComparisons) | **Get** /model-hub/experiments/v2/{experiment_id}/comparisons/ | 
[**ListExperimentRows**](ExperimentsAPI.md#ListExperimentRows) | **Get** /model-hub/experiments/v2/{experiment_id}/rows/ | 
[**ListExperiments**](ExperimentsAPI.md#ListExperiments) | **Get** /model-hub/experiments/v2/list/ | 
[**RerunExperiment**](ExperimentsAPI.md#RerunExperiment) | **Post** /model-hub/experiments/v2/re-run/ | V2 re-run: org-scoped, uses V2 Temporal workflow.
[**StopExperiment**](ExperimentsAPI.md#StopExperiment) | **Post** /model-hub/experiments/v2/{experiment_id}/stop/ | Stop a running V2 experiment.
[**UpdateExperiment**](ExperimentsAPI.md#UpdateExperiment) | **Put** /model-hub/experiments/v2/{experiment_id}/ | Update a V2 experiment with diff-based selective re-run.



## CompareExperiments

> ExperimentDatasetComparisonResponse CompareExperiments(ctx, experimentId).ExperimentComparisonWeightsRequest(experimentComparisonWeightsRequest).Execute()





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
	experimentId := "experimentId_example" // string | 
	experimentComparisonWeightsRequest := *openapiclient.NewExperimentComparisonWeightsRequest() // ExperimentComparisonWeightsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.CompareExperiments(context.Background(), experimentId).ExperimentComparisonWeightsRequest(experimentComparisonWeightsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.CompareExperiments``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CompareExperiments`: ExperimentDatasetComparisonResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.CompareExperiments`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiCompareExperimentsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **experimentComparisonWeightsRequest** | [**ExperimentComparisonWeightsRequest**](ExperimentComparisonWeightsRequest.md) |  | 

### Return type

[**ExperimentDatasetComparisonResponse**](ExperimentDatasetComparisonResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## CreateExperiment

> ExperimentStringResultResponse CreateExperiment(ctx).ExperimentCreateV2(experimentCreateV2).Execute()





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
	experimentCreateV2 := *openapiclient.NewExperimentCreateV2("Name_example", "DatasetId_example", []openapiclient.PromptConfigEntry{*openapiclient.NewPromptConfigEntry()}, []openapiclient.EvalMetricEntry{*openapiclient.NewEvalMetricEntry("TemplateId_example", "Name_example", map[string]interface{}{"key": interface{}(123)})}) // ExperimentCreateV2 | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.CreateExperiment(context.Background()).ExperimentCreateV2(experimentCreateV2).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.CreateExperiment``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateExperiment`: ExperimentStringResultResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.CreateExperiment`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateExperimentRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **experimentCreateV2** | [**ExperimentCreateV2**](ExperimentCreateV2.md) |  | 

### Return type

[**ExperimentStringResultResponse**](ExperimentStringResultResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## DeleteExperiments

> DeleteExperiments(ctx).Execute()





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
	r, err := apiClient.ExperimentsAPI.DeleteExperiments(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.DeleteExperiments``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiDeleteExperimentsRequest struct via the builder pattern


### Return type

 (empty response body)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## DownloadExperiment

> *os.File DownloadExperiment(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.DownloadExperiment(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.DownloadExperiment``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `DownloadExperiment`: *os.File
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.DownloadExperiment`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiDownloadExperimentRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[***os.File**](*os.File.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetExperiment

> ExperimentV2DetailResponse GetExperiment(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.GetExperiment(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.GetExperiment``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetExperiment`: ExperimentV2DetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.GetExperiment`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetExperimentRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentV2DetailResponse**](ExperimentV2DetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetExperimentJsonSchema

> ExperimentJsonSchemaResponse GetExperimentJsonSchema(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.GetExperimentJsonSchema(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.GetExperimentJsonSchema``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetExperimentJsonSchema`: ExperimentJsonSchemaResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.GetExperimentJsonSchema`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetExperimentJsonSchemaRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentJsonSchemaResponse**](ExperimentJsonSchemaResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetExperimentRow

> ExperimentTableRowsResponse GetExperimentRow(ctx, experimentId, rowId).Execute()





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
	experimentId := "experimentId_example" // string | 
	rowId := "rowId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.GetExperimentRow(context.Background(), experimentId, rowId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.GetExperimentRow``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetExperimentRow`: ExperimentTableRowsResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.GetExperimentRow`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 
**rowId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetExperimentRowRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**ExperimentTableRowsResponse**](ExperimentTableRowsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetExperimentStats

> ExperimentStatsResponse GetExperimentStats(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.GetExperimentStats(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.GetExperimentStats``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetExperimentStats`: ExperimentStatsResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.GetExperimentStats`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetExperimentStatsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentStatsResponse**](ExperimentStatsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListExperimentComparisons

> ExperimentComparisonDetailsResponse ListExperimentComparisons(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.ListExperimentComparisons(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.ListExperimentComparisons``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListExperimentComparisons`: ExperimentComparisonDetailsResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.ListExperimentComparisons`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiListExperimentComparisonsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentComparisonDetailsResponse**](ExperimentComparisonDetailsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListExperimentRows

> ExperimentTableRowsResponse ListExperimentRows(ctx, experimentId).Execute()





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
	experimentId := "experimentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.ListExperimentRows(context.Background(), experimentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.ListExperimentRows``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListExperimentRows`: ExperimentTableRowsResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.ListExperimentRows`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiListExperimentRowsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ExperimentTableRowsResponse**](ExperimentTableRowsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListExperiments

> ListExperiments200Response ListExperiments(ctx).CreatedAt(createdAt).Status(status).DatasetId(datasetId).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()





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
	createdAt := "createdAt_example" // string |  (optional)
	status := "status_example" // string |  (optional)
	datasetId := "datasetId_example" // string |  (optional)
	search := "search_example" // string | A search term. (optional)
	ordering := "ordering_example" // string | Which field to use when ordering the results. (optional)
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.ListExperiments(context.Background()).CreatedAt(createdAt).Status(status).DatasetId(datasetId).Search(search).Ordering(ordering).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.ListExperiments``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListExperiments`: ListExperiments200Response
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.ListExperiments`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListExperimentsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **createdAt** | **string** |  | 
 **status** | **string** |  | 
 **datasetId** | **string** |  | 
 **search** | **string** | A search term. | 
 **ordering** | **string** | Which field to use when ordering the results. | 
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**ListExperiments200Response**](ListExperiments200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## RerunExperiment

> ExperimentStringResultResponse RerunExperiment(ctx).ExperimentRerunRequest(experimentRerunRequest).Execute()

V2 re-run: org-scoped, uses V2 Temporal workflow.



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
	experimentRerunRequest := *openapiclient.NewExperimentRerunRequest([]string{"ExperimentIds_example"}) // ExperimentRerunRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.RerunExperiment(context.Background()).ExperimentRerunRequest(experimentRerunRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.RerunExperiment``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `RerunExperiment`: ExperimentStringResultResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.RerunExperiment`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiRerunExperimentRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **experimentRerunRequest** | [**ExperimentRerunRequest**](ExperimentRerunRequest.md) |  | 

### Return type

[**ExperimentStringResultResponse**](ExperimentStringResultResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## StopExperiment

> ExperimentStopResponse StopExperiment(ctx, experimentId).Body(body).Execute()

Stop a running V2 experiment.



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
	experimentId := "experimentId_example" // string | 
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.StopExperiment(context.Background(), experimentId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.StopExperiment``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `StopExperiment`: ExperimentStopResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.StopExperiment`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiStopExperimentRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**ExperimentStopResponse**](ExperimentStopResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## UpdateExperiment

> ExperimentV2DetailResponse UpdateExperiment(ctx, experimentId).ExperimentUpdateV2(experimentUpdateV2).Execute()

Update a V2 experiment with diff-based selective re-run.



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
	experimentId := "experimentId_example" // string | 
	experimentUpdateV2 := *openapiclient.NewExperimentUpdateV2() // ExperimentUpdateV2 | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ExperimentsAPI.UpdateExperiment(context.Background(), experimentId).ExperimentUpdateV2(experimentUpdateV2).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ExperimentsAPI.UpdateExperiment``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateExperiment`: ExperimentV2DetailResponse
	fmt.Fprintf(os.Stdout, "Response from `ExperimentsAPI.UpdateExperiment`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**experimentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateExperimentRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **experimentUpdateV2** | [**ExperimentUpdateV2**](ExperimentUpdateV2.md) |  | 

### Return type

[**ExperimentV2DetailResponse**](ExperimentV2DetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

