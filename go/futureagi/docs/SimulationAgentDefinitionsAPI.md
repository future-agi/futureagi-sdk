# \SimulationAgentDefinitionsAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**CreateAgentDefinition**](SimulationAgentDefinitionsAPI.md#CreateAgentDefinition) | **Post** /simulate/agent-definitions/create/ | 
[**DeleteAgentDefinition**](SimulationAgentDefinitionsAPI.md#DeleteAgentDefinition) | **Delete** /simulate/agent-definitions/{agent_id}/delete/ | 
[**GetAgentDefinition**](SimulationAgentDefinitionsAPI.md#GetAgentDefinition) | **Get** /simulate/agent-definitions/{agent_id}/ | 
[**ListAgentDefinitions**](SimulationAgentDefinitionsAPI.md#ListAgentDefinitions) | **Get** /simulate/agent-definitions/ | 
[**UpdateAgentDefinition**](SimulationAgentDefinitionsAPI.md#UpdateAgentDefinition) | **Put** /simulate/agent-definitions/{agent_id}/edit/ | 



## CreateAgentDefinition

> AgentDefinitionCreateResponse CreateAgentDefinition(ctx).AgentDefinitionCreateRequest(agentDefinitionCreateRequest).Execute()





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
	agentDefinitionCreateRequest := *openapiclient.NewAgentDefinitionCreateRequest("AgentName_example", "AgentType_example", "CommitMessage_example") // AgentDefinitionCreateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationAgentDefinitionsAPI.CreateAgentDefinition(context.Background()).AgentDefinitionCreateRequest(agentDefinitionCreateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationAgentDefinitionsAPI.CreateAgentDefinition``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `CreateAgentDefinition`: AgentDefinitionCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationAgentDefinitionsAPI.CreateAgentDefinition`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiCreateAgentDefinitionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agentDefinitionCreateRequest** | [**AgentDefinitionCreateRequest**](AgentDefinitionCreateRequest.md) |  | 

### Return type

[**AgentDefinitionCreateResponse**](AgentDefinitionCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## DeleteAgentDefinition

> AgentDefinitionDeleteResponse DeleteAgentDefinition(ctx, agentId).Execute()





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
	agentId := "agentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationAgentDefinitionsAPI.DeleteAgentDefinition(context.Background(), agentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationAgentDefinitionsAPI.DeleteAgentDefinition``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `DeleteAgentDefinition`: AgentDefinitionDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationAgentDefinitionsAPI.DeleteAgentDefinition`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiDeleteAgentDefinitionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**AgentDefinitionDeleteResponse**](AgentDefinitionDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetAgentDefinition

> AgentDefinitionResponse GetAgentDefinition(ctx, agentId).Execute()





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
	agentId := "agentId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationAgentDefinitionsAPI.GetAgentDefinition(context.Background(), agentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationAgentDefinitionsAPI.GetAgentDefinition``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAgentDefinition`: AgentDefinitionResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationAgentDefinitionsAPI.GetAgentDefinition`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAgentDefinitionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**AgentDefinitionResponse**](AgentDefinitionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## ListAgentDefinitions

> []AgentDefinitionListResponse ListAgentDefinitions(ctx).Search(search).AgentType(agentType).AgentDefinitionId(agentDefinitionId).Page(page).Limit(limit).Execute()





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
	agentType := "agentType_example" // string |  (optional)
	agentDefinitionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationAgentDefinitionsAPI.ListAgentDefinitions(context.Background()).Search(search).AgentType(agentType).AgentDefinitionId(agentDefinitionId).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationAgentDefinitionsAPI.ListAgentDefinitions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `ListAgentDefinitions`: []AgentDefinitionListResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationAgentDefinitionsAPI.ListAgentDefinitions`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiListAgentDefinitionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **string** |  | [default to &quot;&quot;]
 **agentType** | **string** |  | 
 **agentDefinitionId** | **string** |  | 
 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | 

### Return type

[**[]AgentDefinitionListResponse**](AgentDefinitionListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## UpdateAgentDefinition

> AgentDefinitionEditResponse UpdateAgentDefinition(ctx, agentId).AgentDefinitionEditRequest(agentDefinitionEditRequest).Execute()





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
	agentId := "agentId_example" // string | 
	agentDefinitionEditRequest := *openapiclient.NewAgentDefinitionEditRequest() // AgentDefinitionEditRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulationAgentDefinitionsAPI.UpdateAgentDefinition(context.Background(), agentId).AgentDefinitionEditRequest(agentDefinitionEditRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulationAgentDefinitionsAPI.UpdateAgentDefinition``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `UpdateAgentDefinition`: AgentDefinitionEditResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulationAgentDefinitionsAPI.UpdateAgentDefinition`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiUpdateAgentDefinitionRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **agentDefinitionEditRequest** | [**AgentDefinitionEditRequest**](AgentDefinitionEditRequest.md) |  | 

### Return type

[**AgentDefinitionEditResponse**](AgentDefinitionEditResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

