# \ScenariosAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**SimulateScenariosAddColumnsCreate**](ScenariosAPI.md#SimulateScenariosAddColumnsCreate) | **Post** /simulate/scenarios/{scenario_id}/add-columns/ | Add columns to scenario
[**SimulateScenariosAddRowsCreate**](ScenariosAPI.md#SimulateScenariosAddRowsCreate) | **Post** /simulate/scenarios/{scenario_id}/add-rows/ | Add rows to scenario
[**SimulateScenariosGetColumnsList**](ScenariosAPI.md#SimulateScenariosGetColumnsList) | **Get** /simulate/scenarios/get-columns/ | List scenarios
[**SimulateScenariosPromptsUpdate**](ScenariosAPI.md#SimulateScenariosPromptsUpdate) | **Put** /simulate/scenarios/{scenario_id}/prompts/ | Edit scenario prompts



## SimulateScenariosAddColumnsCreate

> ScenarioAddColumnsResponse SimulateScenariosAddColumnsCreate(ctx, scenarioId).ScenarioAddColumnsRequest(scenarioAddColumnsRequest).Execute()

Add columns to scenario



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
	scenarioId := "scenarioId_example" // string | 
	scenarioAddColumnsRequest := *openapiclient.NewScenarioAddColumnsRequest([]openapiclient.ColumnDefinition{*openapiclient.NewColumnDefinition("Name_example", "DataType_example", "Description_example")}) // ScenarioAddColumnsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ScenariosAPI.SimulateScenariosAddColumnsCreate(context.Background(), scenarioId).ScenarioAddColumnsRequest(scenarioAddColumnsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ScenariosAPI.SimulateScenariosAddColumnsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateScenariosAddColumnsCreate`: ScenarioAddColumnsResponse
	fmt.Fprintf(os.Stdout, "Response from `ScenariosAPI.SimulateScenariosAddColumnsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**scenarioId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateScenariosAddColumnsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **scenarioAddColumnsRequest** | [**ScenarioAddColumnsRequest**](ScenarioAddColumnsRequest.md) |  | 

### Return type

[**ScenarioAddColumnsResponse**](ScenarioAddColumnsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateScenariosAddRowsCreate

> ScenarioAddRowsResponse SimulateScenariosAddRowsCreate(ctx, scenarioId).ScenarioAddRowsRequest(scenarioAddRowsRequest).Execute()

Add rows to scenario



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
	scenarioId := "scenarioId_example" // string | 
	scenarioAddRowsRequest := *openapiclient.NewScenarioAddRowsRequest(int32(123)) // ScenarioAddRowsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ScenariosAPI.SimulateScenariosAddRowsCreate(context.Background(), scenarioId).ScenarioAddRowsRequest(scenarioAddRowsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ScenariosAPI.SimulateScenariosAddRowsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateScenariosAddRowsCreate`: ScenarioAddRowsResponse
	fmt.Fprintf(os.Stdout, "Response from `ScenariosAPI.SimulateScenariosAddRowsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**scenarioId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateScenariosAddRowsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **scenarioAddRowsRequest** | [**ScenarioAddRowsRequest**](ScenarioAddRowsRequest.md) |  | 

### Return type

[**ScenarioAddRowsResponse**](ScenarioAddRowsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateScenariosGetColumnsList

> ScenarioListResponse SimulateScenariosGetColumnsList(ctx).Search(search).AgentDefinitionId(agentDefinitionId).AgentType(agentType).Page(page).Limit(limit).Execute()

List scenarios



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
	search := "search_example" // string |  (optional) (default to "")
	agentDefinitionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	agentType := "agentType_example" // string |  (optional)
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ScenariosAPI.SimulateScenariosGetColumnsList(context.Background()).Search(search).AgentDefinitionId(agentDefinitionId).AgentType(agentType).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ScenariosAPI.SimulateScenariosGetColumnsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateScenariosGetColumnsList`: ScenarioListResponse
	fmt.Fprintf(os.Stdout, "Response from `ScenariosAPI.SimulateScenariosGetColumnsList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSimulateScenariosGetColumnsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **string** |  | [default to &quot;&quot;]
 **agentDefinitionId** | **string** |  | 
 **agentType** | **string** |  | 
 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | 

### Return type

[**ScenarioListResponse**](ScenarioListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateScenariosPromptsUpdate

> ScenarioPromptsUpdateResponse SimulateScenariosPromptsUpdate(ctx, scenarioId).ScenarioEditPromptsRequest(scenarioEditPromptsRequest).Execute()

Edit scenario prompts



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
	scenarioId := "scenarioId_example" // string | 
	scenarioEditPromptsRequest := *openapiclient.NewScenarioEditPromptsRequest("Prompts_example") // ScenarioEditPromptsRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.ScenariosAPI.SimulateScenariosPromptsUpdate(context.Background(), scenarioId).ScenarioEditPromptsRequest(scenarioEditPromptsRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `ScenariosAPI.SimulateScenariosPromptsUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateScenariosPromptsUpdate`: ScenarioPromptsUpdateResponse
	fmt.Fprintf(os.Stdout, "Response from `ScenariosAPI.SimulateScenariosPromptsUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**scenarioId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateScenariosPromptsUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **scenarioEditPromptsRequest** | [**ScenarioEditPromptsRequest**](ScenarioEditPromptsRequest.md) |  | 

### Return type

[**ScenarioPromptsUpdateResponse**](ScenarioPromptsUpdateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

