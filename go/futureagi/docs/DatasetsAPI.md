# \DatasetsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**AddDatasetColumns**](DatasetsAPI.md#AddDatasetColumns) | **Post** /model-hub/develops/{dataset_id}/add_columns/ | 
[**AddDatasetRows**](DatasetsAPI.md#AddDatasetRows) | **Post** /model-hub/develops/{dataset_id}/add_rows/ | 
[**CreateDatasetFromLocalFile**](DatasetsAPI.md#CreateDatasetFromLocalFile) | **Post** /model-hub/develops/create-dataset-from-local-file/ | 
[**CreateDatasetManually**](DatasetsAPI.md#CreateDatasetManually) | **Post** /model-hub/develops/create-dataset-manually/ | 
[**CreateEmptyDataset**](DatasetsAPI.md#CreateEmptyDataset) | **Post** /model-hub/develops/create-empty-dataset/ | 
[**DeleteDatasetColumn**](DatasetsAPI.md#DeleteDatasetColumn) | **Delete** /model-hub/develops/{dataset_id}/delete_column/{column_id}/ | 
[**DeleteDatasetRow**](DatasetsAPI.md#DeleteDatasetRow) | **Delete** /model-hub/develops/{dataset_id}/delete_row/ | 
[**DownloadDataset**](DatasetsAPI.md#DownloadDataset) | **Get** /model-hub/develops/{dataset_id}/download_dataset/ | 
[**DuplicateDataset**](DatasetsAPI.md#DuplicateDataset) | **Post** /model-hub/datasets/{dataset_id}/duplicate/ | 
[**GetDatasetAnnotationSummary**](DatasetsAPI.md#GetDatasetAnnotationSummary) | **Get** /model-hub/dataset/{dataset_id}/annotation-summary/ | 
[**GetDatasetColumns**](DatasetsAPI.md#GetDatasetColumns) | **Get** /model-hub/dataset/columns/{dataset_id}/ | 
[**GetDatasetEvalStats**](DatasetsAPI.md#GetDatasetEvalStats) | **Get** /model-hub/dataset/{dataset_id}/eval-stats/ | 
[**GetDatasetJsonSchema**](DatasetsAPI.md#GetDatasetJsonSchema) | **Get** /model-hub/dataset/{dataset_id}/json-schema/ | 
[**GetDatasetRow**](DatasetsAPI.md#GetDatasetRow) | **Post** /model-hub/develops/{dataset_id}/get-row-data/ | 
[**GetDatasetTable**](DatasetsAPI.md#GetDatasetTable) | **Get** /model-hub/develops/{dataset_id}/get-dataset-table/ | 
[**ListDatasetBaseColumns**](DatasetsAPI.md#ListDatasetBaseColumns) | **Get** /model-hub/datasets/get-base-columns/ | 
[**ListDatasetDerivedVariables**](DatasetsAPI.md#ListDatasetDerivedVariables) | **Get** /model-hub/datasets/{dataset_id}/derived-variables/ | Get all derived variables from all run prompt columns in a dataset.
[**ListDatasetNames**](DatasetsAPI.md#ListDatasetNames) | **Get** /model-hub/develops/get-datasets-names/ | 
[**ListDatasets**](DatasetsAPI.md#ListDatasets) | **Get** /model-hub/develops/get-datasets/ | 
[**UpdateDatasetCell**](DatasetsAPI.md#UpdateDatasetCell) | **Post** /model-hub/develops/{dataset_id}/update_cell_value/ | 



## AddDatasetColumns

> DatasetColumnsMutationResponse AddDatasetColumns(ctx, datasetId).DatasetAddColumnsRequest(datasetAddColumnsRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetAddColumnsRequest := *openapiclient.NewDatasetAddColumnsRequest([]map[string]interface{}{map[string]interface{}{"key": interface{}(123)}}) // DatasetAddColumnsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.AddDatasetColumns(context.Background(), datasetId).DatasetAddColumnsRequest(datasetAddColumnsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.AddDatasetColumns``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AddDatasetColumns`: DatasetColumnsMutationResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.AddDatasetColumns`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiAddDatasetColumnsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetAddColumnsRequest** | [**DatasetAddColumnsRequest**](DatasetAddColumnsRequest.md) |  | 

### Return type

[**DatasetColumnsMutationResponse**](DatasetColumnsMutationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## AddDatasetRows

> DevelopDatasetMessageResponse AddDatasetRows(ctx, datasetId).DatasetAddRowsRequest(datasetAddRowsRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetAddRowsRequest := *openapiclient.NewDatasetAddRowsRequest([]map[string]interface{}{map[string]interface{}{"key": interface{}(123)}}) // DatasetAddRowsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.AddDatasetRows(context.Background(), datasetId).DatasetAddRowsRequest(datasetAddRowsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.AddDatasetRows``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `AddDatasetRows`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.AddDatasetRows`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiAddDatasetRowsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetAddRowsRequest** | [**DatasetAddRowsRequest**](DatasetAddRowsRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## CreateDatasetFromLocalFile

> LocalFileDatasetCreateStartedResponse CreateDatasetFromLocalFile(ctx).CreateDatasetFromLocalFileRequest(createDatasetFromLocalFileRequest).Execute()





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
	createDatasetFromLocalFileRequest := *openapiclient.NewCreateDatasetFromLocalFileRequest() // CreateDatasetFromLocalFileRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.CreateDatasetFromLocalFile(context.Background()).CreateDatasetFromLocalFileRequest(createDatasetFromLocalFileRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.CreateDatasetFromLocalFile``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateDatasetFromLocalFile`: LocalFileDatasetCreateStartedResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.CreateDatasetFromLocalFile`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateDatasetFromLocalFileRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **createDatasetFromLocalFileRequest** | [**CreateDatasetFromLocalFileRequest**](CreateDatasetFromLocalFileRequest.md) |  | 

### Return type

[**LocalFileDatasetCreateStartedResponse**](LocalFileDatasetCreateStartedResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## CreateDatasetManually

> ManualDatasetCreateResponse CreateDatasetManually(ctx).ManualDatasetCreateRequest(manualDatasetCreateRequest).Execute()





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
	manualDatasetCreateRequest := *openapiclient.NewManualDatasetCreateRequest("DatasetName_example") // ManualDatasetCreateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.CreateDatasetManually(context.Background()).ManualDatasetCreateRequest(manualDatasetCreateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.CreateDatasetManually``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateDatasetManually`: ManualDatasetCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.CreateDatasetManually`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateDatasetManuallyRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **manualDatasetCreateRequest** | [**ManualDatasetCreateRequest**](ManualDatasetCreateRequest.md) |  | 

### Return type

[**ManualDatasetCreateResponse**](ManualDatasetCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## CreateEmptyDataset

> DatasetCreateStartedResponse CreateEmptyDataset(ctx).CreateEmptyDatasetRequest(createEmptyDatasetRequest).Execute()





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
	createEmptyDatasetRequest := *openapiclient.NewCreateEmptyDatasetRequest("NewDatasetName_example") // CreateEmptyDatasetRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.CreateEmptyDataset(context.Background()).CreateEmptyDatasetRequest(createEmptyDatasetRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.CreateEmptyDataset``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateEmptyDataset`: DatasetCreateStartedResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.CreateEmptyDataset`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateEmptyDatasetRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **createEmptyDatasetRequest** | [**CreateEmptyDatasetRequest**](CreateEmptyDatasetRequest.md) |  | 

### Return type

[**DatasetCreateStartedResponse**](DatasetCreateStartedResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## DeleteDatasetColumn

> DeleteDatasetColumn(ctx, datasetId, columnId).Execute()





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
	datasetId := "datasetId_example" // string | 
	columnId := "columnId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.DatasetsAPI.DeleteDatasetColumn(context.Background(), datasetId, columnId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.DeleteDatasetColumn``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 
**columnId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiDeleteDatasetColumnRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



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


## DeleteDatasetRow

> DeleteDatasetRow(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.DatasetsAPI.DeleteDatasetRow(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.DeleteDatasetRow``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiDeleteDatasetRowRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


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


## DownloadDataset

> *os.File DownloadDataset(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.DownloadDataset(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.DownloadDataset``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `DownloadDataset`: *os.File
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.DownloadDataset`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiDownloadDatasetRequest struct via the builder pattern


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


## DuplicateDataset

> DuplicateDatasetResponse DuplicateDataset(ctx, datasetId).DuplicateDatasetRequest(duplicateDatasetRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	duplicateDatasetRequest := *openapiclient.NewDuplicateDatasetRequest("Name_example") // DuplicateDatasetRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.DuplicateDataset(context.Background(), datasetId).DuplicateDatasetRequest(duplicateDatasetRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.DuplicateDataset``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `DuplicateDataset`: DuplicateDatasetResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.DuplicateDataset`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiDuplicateDatasetRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **duplicateDatasetRequest** | [**DuplicateDatasetRequest**](DuplicateDatasetRequest.md) |  | 

### Return type

[**DuplicateDatasetResponse**](DuplicateDatasetResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetDatasetAnnotationSummary

> AnnotationSummaryResponse GetDatasetAnnotationSummary(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.GetDatasetAnnotationSummary(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.GetDatasetAnnotationSummary``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetDatasetAnnotationSummary`: AnnotationSummaryResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.GetDatasetAnnotationSummary`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetDatasetAnnotationSummaryRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**AnnotationSummaryResponse**](AnnotationSummaryResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetDatasetColumns

> DatasetColumnDetailResponse GetDatasetColumns(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.GetDatasetColumns(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.GetDatasetColumns``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetDatasetColumns`: DatasetColumnDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.GetDatasetColumns`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetDatasetColumnsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetColumnDetailResponse**](DatasetColumnDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetDatasetEvalStats

> DatasetEvalStatsResponse GetDatasetEvalStats(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.GetDatasetEvalStats(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.GetDatasetEvalStats``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetDatasetEvalStats`: DatasetEvalStatsResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.GetDatasetEvalStats`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetDatasetEvalStatsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetEvalStatsResponse**](DatasetEvalStatsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetDatasetJsonSchema

> DatasetJsonSchemaResponse GetDatasetJsonSchema(ctx, datasetId).Execute()





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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.GetDatasetJsonSchema(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.GetDatasetJsonSchema``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetDatasetJsonSchema`: DatasetJsonSchemaResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.GetDatasetJsonSchema`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetDatasetJsonSchemaRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetJsonSchemaResponse**](DatasetJsonSchemaResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetDatasetRow

> DatasetRowDataResponse GetDatasetRow(ctx, datasetId).DatasetRowDataRequest(datasetRowDataRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetRowDataRequest := *openapiclient.NewDatasetRowDataRequest("RowId_example") // DatasetRowDataRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.GetDatasetRow(context.Background(), datasetId).DatasetRowDataRequest(datasetRowDataRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.GetDatasetRow``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetDatasetRow`: DatasetRowDataResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.GetDatasetRow`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetDatasetRowRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetRowDataRequest** | [**DatasetRowDataRequest**](DatasetRowDataRequest.md) |  | 

### Return type

[**DatasetRowDataResponse**](DatasetRowDataResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetDatasetTable

> DatasetTableResponse GetDatasetTable(ctx, datasetId).Filters(filters).Sort(sort).Search(search).PageSize(pageSize).CurrentPageIndex(currentPageIndex).ColumnConfigOnly(columnConfigOnly).Execute()





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
	datasetId := "datasetId_example" // string | 
	filters := "filters_example" // string |  (optional) (default to "[]")
	sort := "sort_example" // string |  (optional) (default to "[]")
	search := "search_example" // string |  (optional)
	pageSize := int32(56) // int32 |  (optional) (default to 10)
	currentPageIndex := int32(56) // int32 |  (optional) (default to 0)
	columnConfigOnly := true // bool |  (optional) (default to false)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.GetDatasetTable(context.Background(), datasetId).Filters(filters).Sort(sort).Search(search).PageSize(pageSize).CurrentPageIndex(currentPageIndex).ColumnConfigOnly(columnConfigOnly).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.GetDatasetTable``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetDatasetTable`: DatasetTableResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.GetDatasetTable`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetDatasetTableRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **filters** | **string** |  | [default to &quot;[]&quot;]
 **sort** | **string** |  | [default to &quot;[]&quot;]
 **search** | **string** |  | 
 **pageSize** | **int32** |  | [default to 10]
 **currentPageIndex** | **int32** |  | [default to 0]
 **columnConfigOnly** | **bool** |  | [default to false]

### Return type

[**DatasetTableResponse**](DatasetTableResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListDatasetBaseColumns

> BaseColumnsResponse ListDatasetBaseColumns(ctx).Execute()





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
	resp, r, err := apiClient.DatasetsAPI.ListDatasetBaseColumns(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.ListDatasetBaseColumns``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListDatasetBaseColumns`: BaseColumnsResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.ListDatasetBaseColumns`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiListDatasetBaseColumnsRequest struct via the builder pattern


### Return type

[**BaseColumnsResponse**](BaseColumnsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListDatasetDerivedVariables

> DatasetDerivedVariablesResponse ListDatasetDerivedVariables(ctx, datasetId).Execute()

Get all derived variables from all run prompt columns in a dataset.



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
	datasetId := "datasetId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.ListDatasetDerivedVariables(context.Background(), datasetId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.ListDatasetDerivedVariables``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListDatasetDerivedVariables`: DatasetDerivedVariablesResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.ListDatasetDerivedVariables`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiListDatasetDerivedVariablesRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**DatasetDerivedVariablesResponse**](DatasetDerivedVariablesResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListDatasetNames

> DatasetNamesResponse ListDatasetNames(ctx).Execute()





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
	resp, r, err := apiClient.DatasetsAPI.ListDatasetNames(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.ListDatasetNames``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListDatasetNames`: DatasetNamesResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.ListDatasetNames`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiListDatasetNamesRequest struct via the builder pattern


### Return type

[**DatasetNamesResponse**](DatasetNamesResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListDatasets

> DatasetListResponse ListDatasets(ctx).SearchText(searchText).Page(page).PageSize(pageSize).Sort(sort).Execute()





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
	searchText := "searchText_example" // string |  (optional) (default to "")
	page := int32(56) // int32 |  (optional) (default to 0)
	pageSize := int32(56) // int32 |  (optional) (default to 10)
	sort := "sort_example" // string |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.ListDatasets(context.Background()).SearchText(searchText).Page(page).PageSize(pageSize).Sort(sort).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.ListDatasets``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListDatasets`: DatasetListResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.ListDatasets`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListDatasetsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **searchText** | **string** |  | [default to &quot;&quot;]
 **page** | **int32** |  | [default to 0]
 **pageSize** | **int32** |  | [default to 10]
 **sort** | **string** |  | 

### Return type

[**DatasetListResponse**](DatasetListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## UpdateDatasetCell

> DevelopDatasetMessageResponse UpdateDatasetCell(ctx, datasetId).DatasetUpdateCellValueRequest(datasetUpdateCellValueRequest).Execute()





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
	datasetId := "datasetId_example" // string | 
	datasetUpdateCellValueRequest := *openapiclient.NewDatasetUpdateCellValueRequest("RowId_example", "ColumnId_example") // DatasetUpdateCellValueRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DatasetsAPI.UpdateDatasetCell(context.Background(), datasetId).DatasetUpdateCellValueRequest(datasetUpdateCellValueRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DatasetsAPI.UpdateDatasetCell``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateDatasetCell`: DevelopDatasetMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `DatasetsAPI.UpdateDatasetCell`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**datasetId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateDatasetCellRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **datasetUpdateCellValueRequest** | [**DatasetUpdateCellValueRequest**](DatasetUpdateCellValueRequest.md) |  | 

### Return type

[**DevelopDatasetMessageResponse**](DevelopDatasetMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

