# \SimulationScenariosAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**CreateScenario**](SimulationScenariosAPI.md#CreateScenario) | **Post** /simulate/scenarios/create/ | Create scenario
[**DeleteScenario**](SimulationScenariosAPI.md#DeleteScenario) | **Delete** /simulate/scenarios/{scenario_id}/delete/ | Delete scenario
[**GetScenario**](SimulationScenariosAPI.md#GetScenario) | **Get** /simulate/scenarios/{scenario_id}/ | Get scenario detail
[**ListScenarios**](SimulationScenariosAPI.md#ListScenarios) | **Get** /simulate/scenarios/ | List scenarios
[**UpdateScenario**](SimulationScenariosAPI.md#UpdateScenario) | **Put** /simulate/scenarios/{scenario_id}/edit/ | Edit scenario



## CreateScenario

> ScenarioCreateResponse CreateScenario(ctx).ScenarioCreateRequest(scenarioCreateRequest).Execute()

Create scenario



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
	scenarioCreateRequest := *openapiclient.NewScenarioCreateRequest("Name_example") // ScenarioCreateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationScenariosAPI.CreateScenario(context.Background()).ScenarioCreateRequest(scenarioCreateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationScenariosAPI.CreateScenario``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateScenario`: ScenarioCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationScenariosAPI.CreateScenario`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateScenarioRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **scenarioCreateRequest** | [**ScenarioCreateRequest**](ScenarioCreateRequest.md) |  | 

### Return type

[**ScenarioCreateResponse**](ScenarioCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## DeleteScenario

> ScenarioDeleteResponse DeleteScenario(ctx, scenarioId).Execute()

Delete scenario



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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationScenariosAPI.DeleteScenario(context.Background(), scenarioId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationScenariosAPI.DeleteScenario``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `DeleteScenario`: ScenarioDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationScenariosAPI.DeleteScenario`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**scenarioId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiDeleteScenarioRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ScenarioDeleteResponse**](ScenarioDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetScenario

> ScenarioDetailResponse GetScenario(ctx, scenarioId).Execute()

Get scenario detail



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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationScenariosAPI.GetScenario(context.Background(), scenarioId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationScenariosAPI.GetScenario``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetScenario`: ScenarioDetailResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationScenariosAPI.GetScenario`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**scenarioId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetScenarioRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ScenarioDetailResponse**](ScenarioDetailResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListScenarios

> ScenarioListResponse ListScenarios(ctx).Search(search).AgentDefinitionId(agentDefinitionId).AgentType(agentType).Page(page).Limit(limit).Execute()

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
	resp, r, err := apiClient.SimulationScenariosAPI.ListScenarios(context.Background()).Search(search).AgentDefinitionId(agentDefinitionId).AgentType(agentType).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationScenariosAPI.ListScenarios``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListScenarios`: ScenarioListResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationScenariosAPI.ListScenarios`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListScenariosRequest struct via the builder pattern


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


## UpdateScenario

> ScenarioEditResponse UpdateScenario(ctx, scenarioId).ScenarioEditRequest(scenarioEditRequest).Execute()

Edit scenario



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
	scenarioEditRequest := *openapiclient.NewScenarioEditRequest() // ScenarioEditRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationScenariosAPI.UpdateScenario(context.Background(), scenarioId).ScenarioEditRequest(scenarioEditRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationScenariosAPI.UpdateScenario``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateScenario`: ScenarioEditResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationScenariosAPI.UpdateScenario`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**scenarioId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateScenarioRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **scenarioEditRequest** | [**ScenarioEditRequest**](ScenarioEditRequest.md) |  | 

### Return type

[**ScenarioEditResponse**](ScenarioEditResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

