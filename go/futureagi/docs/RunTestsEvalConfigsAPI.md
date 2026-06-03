# \RunTestsEvalConfigsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**SimulateRunTestsEvalConfigsCreate**](RunTestsEvalConfigsAPI.md#SimulateRunTestsEvalConfigsCreate) | **Post** /simulate/run-tests/{run_test_id}/eval-configs/ | Add evaluation configurations
[**SimulateRunTestsEvalConfigsDelete**](RunTestsEvalConfigsAPI.md#SimulateRunTestsEvalConfigsDelete) | **Delete** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/ | Delete evaluation configuration
[**SimulateRunTestsEvalConfigsUpdateCreate**](RunTestsEvalConfigsAPI.md#SimulateRunTestsEvalConfigsUpdateCreate) | **Post** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/update/ | Update evaluation configuration
[**SimulateRunTestsRunNewEvalsCreate**](RunTestsEvalConfigsAPI.md#SimulateRunTestsRunNewEvalsCreate) | **Post** /simulate/run-tests/{run_test_id}/run-new-evals/ | Run new evaluations on test executions



## SimulateRunTestsEvalConfigsCreate

> AddEvalConfigsResponse SimulateRunTestsEvalConfigsCreate(ctx, runTestId).AddEvalConfigsRequest(addEvalConfigsRequest).Execute()

Add evaluation configurations



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
	addEvalConfigsRequest := *openapiclient.NewAddEvalConfigsRequest([]openapiclient.EvalConfigDefinition{*openapiclient.NewEvalConfigDefinition("TemplateId_example")}) // AddEvalConfigsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsCreate(context.Background(), runTestId).AddEvalConfigsRequest(addEvalConfigsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsEvalConfigsCreate`: AddEvalConfigsResponse
	fmt.Fprintf(os.Stdout, "Response from `RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsEvalConfigsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **addEvalConfigsRequest** | [**AddEvalConfigsRequest**](AddEvalConfigsRequest.md) |  | 

### Return type

[**AddEvalConfigsResponse**](AddEvalConfigsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsEvalConfigsDelete

> DeleteEvalConfigResponse SimulateRunTestsEvalConfigsDelete(ctx, runTestId, evalConfigId).Execute()

Delete evaluation configuration



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
	evalConfigId := "evalConfigId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsDelete(context.Background(), runTestId, evalConfigId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsEvalConfigsDelete`: DeleteEvalConfigResponse
	fmt.Fprintf(os.Stdout, "Response from `RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 
**evalConfigId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsEvalConfigsDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**DeleteEvalConfigResponse**](DeleteEvalConfigResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsEvalConfigsUpdateCreate

> EvalConfigUpdateResponse SimulateRunTestsEvalConfigsUpdateCreate(ctx, runTestId, evalConfigId).EvalConfigUpdateRequest(evalConfigUpdateRequest).Execute()

Update evaluation configuration



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
	evalConfigId := "evalConfigId_example" // string | 
	evalConfigUpdateRequest := *openapiclient.NewEvalConfigUpdateRequest() // EvalConfigUpdateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsUpdateCreate(context.Background(), runTestId, evalConfigId).EvalConfigUpdateRequest(evalConfigUpdateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsUpdateCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsEvalConfigsUpdateCreate`: EvalConfigUpdateResponse
	fmt.Fprintf(os.Stdout, "Response from `RunTestsEvalConfigsAPI.SimulateRunTestsEvalConfigsUpdateCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 
**evalConfigId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsEvalConfigsUpdateCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **evalConfigUpdateRequest** | [**EvalConfigUpdateRequest**](EvalConfigUpdateRequest.md) |  | 

### Return type

[**EvalConfigUpdateResponse**](EvalConfigUpdateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsRunNewEvalsCreate

> RunNewEvalsResponse SimulateRunTestsRunNewEvalsCreate(ctx, runTestId).RunNewEvalsOnTestExecution(runNewEvalsOnTestExecution).Execute()

Run new evaluations on test executions



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
	runNewEvalsOnTestExecution := *openapiclient.NewRunNewEvalsOnTestExecution([]string{"EvalConfigIds_example"}) // RunNewEvalsOnTestExecution | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.RunTestsEvalConfigsAPI.SimulateRunTestsRunNewEvalsCreate(context.Background(), runTestId).RunNewEvalsOnTestExecution(runNewEvalsOnTestExecution).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `RunTestsEvalConfigsAPI.SimulateRunTestsRunNewEvalsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsRunNewEvalsCreate`: RunNewEvalsResponse
	fmt.Fprintf(os.Stdout, "Response from `RunTestsEvalConfigsAPI.SimulateRunTestsRunNewEvalsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsRunNewEvalsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **runNewEvalsOnTestExecution** | [**RunNewEvalsOnTestExecution**](RunNewEvalsOnTestExecution.md) |  | 

### Return type

[**RunNewEvalsResponse**](RunNewEvalsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

