# \SimulateAPI

All URIs are relative to *https://api.futureagi.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**SimulateAgentDefinitionsDelete**](SimulateAPI.md#SimulateAgentDefinitionsDelete) | **Delete** /simulate/agent-definitions/ | 
[**SimulateAgentDefinitionsVersionsActivateCreate**](SimulateAPI.md#SimulateAgentDefinitionsVersionsActivateCreate) | **Post** /simulate/agent-definitions/{agent_id}/versions/{version_id}/activate/ | 
[**SimulateAgentDefinitionsVersionsCallExecutionsList**](SimulateAPI.md#SimulateAgentDefinitionsVersionsCallExecutionsList) | **Get** /simulate/agent-definitions/{agent_id}/versions/{version_id}/call-executions/ | 
[**SimulateAgentDefinitionsVersionsCreateCreate**](SimulateAPI.md#SimulateAgentDefinitionsVersionsCreateCreate) | **Post** /simulate/agent-definitions/{agent_id}/versions/create/ | 
[**SimulateAgentDefinitionsVersionsDeleteDelete**](SimulateAPI.md#SimulateAgentDefinitionsVersionsDeleteDelete) | **Delete** /simulate/agent-definitions/{agent_id}/versions/{version_id}/delete/ | 
[**SimulateAgentDefinitionsVersionsEvalSummaryList**](SimulateAPI.md#SimulateAgentDefinitionsVersionsEvalSummaryList) | **Get** /simulate/agent-definitions/{agent_id}/versions/{version_id}/eval-summary/ | 
[**SimulateAgentDefinitionsVersionsList**](SimulateAPI.md#SimulateAgentDefinitionsVersionsList) | **Get** /simulate/agent-definitions/{agent_id}/versions/ | 
[**SimulateAgentDefinitionsVersionsRead**](SimulateAPI.md#SimulateAgentDefinitionsVersionsRead) | **Get** /simulate/agent-definitions/{agent_id}/versions/{version_id}/ | 
[**SimulateAgentDefinitionsVersionsRestoreCreate**](SimulateAPI.md#SimulateAgentDefinitionsVersionsRestoreCreate) | **Post** /simulate/agent-definitions/{agent_id}/versions/{version_id}/restore/ | 
[**SimulateApiCallExecutionsList**](SimulateAPI.md#SimulateApiCallExecutionsList) | **Get** /simulate/api/call-executions/ | 
[**SimulateApiPersonasDuplicate**](SimulateAPI.md#SimulateApiPersonasDuplicate) | **Post** /simulate/api/personas/{id}/duplicate/ | 
[**SimulateApiPersonasDuplicateCreate**](SimulateAPI.md#SimulateApiPersonasDuplicateCreate) | **Post** /simulate/api/personas/duplicate/{persona_id}/ | 
[**SimulateApiPersonasFieldOptions**](SimulateAPI.md#SimulateApiPersonasFieldOptions) | **Get** /simulate/api/personas/field-options/ | 
[**SimulateApiPersonasSystemPersonas**](SimulateAPI.md#SimulateApiPersonasSystemPersonas) | **Get** /simulate/api/personas/system/ | 
[**SimulateApiPersonasUpdate**](SimulateAPI.md#SimulateApiPersonasUpdate) | **Put** /simulate/api/personas/{id}/ | 
[**SimulateApiPersonasWorkspacePersonas**](SimulateAPI.md#SimulateApiPersonasWorkspacePersonas) | **Get** /simulate/api/personas/workspace/ | 
[**SimulateApiRunTestsList**](SimulateAPI.md#SimulateApiRunTestsList) | **Get** /simulate/api/run-tests/ | 
[**SimulateCallExecutionsBranchAnalysisCreate**](SimulateAPI.md#SimulateCallExecutionsBranchAnalysisCreate) | **Post** /simulate/call-executions/{call_execution_id}/branch-analysis/ | 
[**SimulateCallExecutionsBranchAnalysisList**](SimulateAPI.md#SimulateCallExecutionsBranchAnalysisList) | **Get** /simulate/call-executions/{call_execution_id}/branch-analysis/ | 
[**SimulateCallExecutionsChatSendMessageCreate**](SimulateAPI.md#SimulateCallExecutionsChatSendMessageCreate) | **Post** /simulate/call-executions/{call_execution_id}/chat/send-message/ | 
[**SimulateCallExecutionsDeleteDelete**](SimulateAPI.md#SimulateCallExecutionsDeleteDelete) | **Delete** /simulate/call-executions/{call_execution_id}/delete/ | 
[**SimulateCallExecutionsErrorLocalizerTasksList**](SimulateAPI.md#SimulateCallExecutionsErrorLocalizerTasksList) | **Get** /simulate/call-executions/{call_execution_id}/error-localizer-tasks/ | 
[**SimulateCallExecutionsLogsList**](SimulateAPI.md#SimulateCallExecutionsLogsList) | **Get** /simulate/call-executions/{call_execution_id}/logs/ | 
[**SimulateCallExecutionsPartialUpdate**](SimulateAPI.md#SimulateCallExecutionsPartialUpdate) | **Patch** /simulate/call-executions/{call_execution_id}/ | 
[**SimulateCallExecutionsRead**](SimulateAPI.md#SimulateCallExecutionsRead) | **Get** /simulate/call-executions/{call_execution_id}/ | 
[**SimulateCallExecutionsSessionComparisonList**](SimulateAPI.md#SimulateCallExecutionsSessionComparisonList) | **Get** /simulate/call-executions/{call_execution_id}/session-comparison/ | 
[**SimulateCallExecutionsTranscriptsList**](SimulateAPI.md#SimulateCallExecutionsTranscriptsList) | **Get** /simulate/call-executions/{call_execution_id}/transcripts/ | 
[**SimulateExportRead**](SimulateAPI.md#SimulateExportRead) | **Get** /simulate/export/{item_id}/ | 
[**SimulatePromptSimulationsScenariosList**](SimulateAPI.md#SimulatePromptSimulationsScenariosList) | **Get** /simulate/prompt-simulations/scenarios/ | Get list of scenarios available for prompt simulations.
[**SimulatePromptTemplatesSimulationsCreate**](SimulateAPI.md#SimulatePromptTemplatesSimulationsCreate) | **Post** /simulate/prompt-templates/{prompt_template_id}/simulations/ | Create a new prompt-based simulation run.
[**SimulatePromptTemplatesSimulationsDelete**](SimulateAPI.md#SimulatePromptTemplatesSimulationsDelete) | **Delete** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ | 
[**SimulatePromptTemplatesSimulationsExecuteCreate**](SimulateAPI.md#SimulatePromptTemplatesSimulationsExecuteCreate) | **Post** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/execute/ | Execute a prompt-based simulation run.
[**SimulatePromptTemplatesSimulationsList**](SimulateAPI.md#SimulatePromptTemplatesSimulationsList) | **Get** /simulate/prompt-templates/{prompt_template_id}/simulations/ | Get paginated list of simulation runs for a specific prompt template.
[**SimulatePromptTemplatesSimulationsPartialUpdate**](SimulateAPI.md#SimulatePromptTemplatesSimulationsPartialUpdate) | **Patch** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ | 
[**SimulatePromptTemplatesSimulationsRead**](SimulateAPI.md#SimulatePromptTemplatesSimulationsRead) | **Get** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ | 
[**SimulateRunTestsActiveList**](SimulateAPI.md#SimulateRunTestsActiveList) | **Get** /simulate/run-tests/active/ | 
[**SimulateRunTestsChatExecuteCreate**](SimulateAPI.md#SimulateRunTestsChatExecuteCreate) | **Post** /simulate/run-tests/{run_test_id}/chat-execute/ | 
[**SimulateRunTestsComponentsPartialUpdate**](SimulateAPI.md#SimulateRunTestsComponentsPartialUpdate) | **Patch** /simulate/run-tests/{run_test_id}/components/ | 
[**SimulateRunTestsDeleteDelete**](SimulateAPI.md#SimulateRunTestsDeleteDelete) | **Delete** /simulate/run-tests/{run_test_id}/delete/ | 
[**SimulateRunTestsDeleteTestExecutionsCreate**](SimulateAPI.md#SimulateRunTestsDeleteTestExecutionsCreate) | **Post** /simulate/run-tests/{run_test_id}/delete-test-executions/ | 
[**SimulateRunTestsEvalConfigsGetStructureList**](SimulateAPI.md#SimulateRunTestsEvalConfigsGetStructureList) | **Get** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/get-structure/ | 
[**SimulateRunTestsGetIdByNameRead**](SimulateAPI.md#SimulateRunTestsGetIdByNameRead) | **Get** /simulate/run-tests/get-id-by-name/{run_test_name}/ | 
[**SimulateRunTestsRerunTestExecutionsCreate**](SimulateAPI.md#SimulateRunTestsRerunTestExecutionsCreate) | **Post** /simulate/run-tests/{run_test_id}/rerun-test-executions/ | 
[**SimulateRunTestsScenariosList**](SimulateAPI.md#SimulateRunTestsScenariosList) | **Get** /simulate/run-tests/{run_test_id}/scenarios/ | 
[**SimulateRunTestsSdkCodeList**](SimulateAPI.md#SimulateRunTestsSdkCodeList) | **Get** /simulate/run-tests/{run_test_id}/sdk-code/ | 
[**SimulateSimulatorAgentsCreateCreate**](SimulateAPI.md#SimulateSimulatorAgentsCreateCreate) | **Post** /simulate/simulator-agents/create/ | 
[**SimulateSimulatorAgentsDeleteDelete**](SimulateAPI.md#SimulateSimulatorAgentsDeleteDelete) | **Delete** /simulate/simulator-agents/{agent_id}/delete/ | 
[**SimulateSimulatorAgentsEditUpdate**](SimulateAPI.md#SimulateSimulatorAgentsEditUpdate) | **Put** /simulate/simulator-agents/{agent_id}/edit/ | 
[**SimulateSimulatorAgentsList**](SimulateAPI.md#SimulateSimulatorAgentsList) | **Get** /simulate/simulator-agents/ | 
[**SimulateSimulatorAgentsRead**](SimulateAPI.md#SimulateSimulatorAgentsRead) | **Get** /simulate/simulator-agents/{agent_id}/ | 
[**SimulateTestExecutionsChatCallExecutionsBatchCreate**](SimulateAPI.md#SimulateTestExecutionsChatCallExecutionsBatchCreate) | **Post** /simulate/test-executions/{test_execution_id}/chat/call-executions/batch/ | Create a batch of CallExecution records for chat execution (exactly 10 per API call).
[**SimulateTestExecutionsColumnOrderUpdate**](SimulateAPI.md#SimulateTestExecutionsColumnOrderUpdate) | **Put** /simulate/test-executions/{test_execution_id}/column-order/ | 
[**SimulateTestExecutionsDeleteDelete**](SimulateAPI.md#SimulateTestExecutionsDeleteDelete) | **Delete** /simulate/test-executions/{test_execution_id}/delete/ | 
[**SimulateTestExecutionsEvalExplanationSummaryList**](SimulateAPI.md#SimulateTestExecutionsEvalExplanationSummaryList) | **Get** /simulate/test-executions/{test_execution_id}/eval-explanation-summary/ | 
[**SimulateTestExecutionsEvalExplanationSummaryRefreshCreate**](SimulateAPI.md#SimulateTestExecutionsEvalExplanationSummaryRefreshCreate) | **Post** /simulate/test-executions/{test_execution_id}/eval-explanation-summary/refresh/ | 
[**SimulateTestExecutionsOptimiserAnalysisList**](SimulateAPI.md#SimulateTestExecutionsOptimiserAnalysisList) | **Get** /simulate/test-executions/{test_execution_id}/optimiser-analysis/ | 
[**SimulateTestExecutionsOptimiserAnalysisRefreshCreate**](SimulateAPI.md#SimulateTestExecutionsOptimiserAnalysisRefreshCreate) | **Post** /simulate/test-executions/{test_execution_id}/optimiser-analysis/refresh/ | 
[**SimulateTestExecutionsRerunCallsCreate**](SimulateAPI.md#SimulateTestExecutionsRerunCallsCreate) | **Post** /simulate/test-executions/{test_execution_id}/rerun-calls/ | 



## SimulateAgentDefinitionsDelete

> AgentDefinitionBulkDeleteResponse SimulateAgentDefinitionsDelete(ctx).AgentDefinitionBulkDeleteRequest(agentDefinitionBulkDeleteRequest).Execute()





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
	agentDefinitionBulkDeleteRequest := *openapiclient.NewAgentDefinitionBulkDeleteRequest([]string{"AgentIds_example"}) // AgentDefinitionBulkDeleteRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsDelete(context.Background()).AgentDefinitionBulkDeleteRequest(agentDefinitionBulkDeleteRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsDelete`: AgentDefinitionBulkDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsDelete`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agentDefinitionBulkDeleteRequest** | [**AgentDefinitionBulkDeleteRequest**](AgentDefinitionBulkDeleteRequest.md) |  | 

### Return type

[**AgentDefinitionBulkDeleteResponse**](AgentDefinitionBulkDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateAgentDefinitionsVersionsActivateCreate

> AgentVersionActivateResponse SimulateAgentDefinitionsVersionsActivateCreate(ctx, agentId, versionId).Body(body).Execute()





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
	versionId := "versionId_example" // string | 
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsVersionsActivateCreate(context.Background(), agentId, versionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsVersionsActivateCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsVersionsActivateCreate`: AgentVersionActivateResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsVersionsActivateCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 
**versionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsVersionsActivateCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **body** | **map[string]interface{}** |  | 

### Return type

[**AgentVersionActivateResponse**](AgentVersionActivateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateAgentDefinitionsVersionsCallExecutionsList

> []CallExecution SimulateAgentDefinitionsVersionsCallExecutionsList(ctx, agentId, versionId).Execute()





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
	versionId := "versionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsVersionsCallExecutionsList(context.Background(), agentId, versionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsVersionsCallExecutionsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsVersionsCallExecutionsList`: []CallExecution
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsVersionsCallExecutionsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 
**versionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsVersionsCallExecutionsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**[]CallExecution**](CallExecution.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateAgentDefinitionsVersionsCreateCreate

> AgentVersionCreateResponse SimulateAgentDefinitionsVersionsCreateCreate(ctx, agentId).AgentVersionCreateRequest(agentVersionCreateRequest).Execute()





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
	agentVersionCreateRequest := *openapiclient.NewAgentVersionCreateRequest() // AgentVersionCreateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsVersionsCreateCreate(context.Background(), agentId).AgentVersionCreateRequest(agentVersionCreateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsVersionsCreateCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsVersionsCreateCreate`: AgentVersionCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsVersionsCreateCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsVersionsCreateCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **agentVersionCreateRequest** | [**AgentVersionCreateRequest**](AgentVersionCreateRequest.md) |  | 

### Return type

[**AgentVersionCreateResponse**](AgentVersionCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateAgentDefinitionsVersionsDeleteDelete

> AgentVersionDeleteResponse SimulateAgentDefinitionsVersionsDeleteDelete(ctx, agentId, versionId).Execute()





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
	versionId := "versionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsVersionsDeleteDelete(context.Background(), agentId, versionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsVersionsDeleteDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsVersionsDeleteDelete`: AgentVersionDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsVersionsDeleteDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 
**versionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsVersionsDeleteDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**AgentVersionDeleteResponse**](AgentVersionDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateAgentDefinitionsVersionsEvalSummaryList

> EvalSummaryResponse SimulateAgentDefinitionsVersionsEvalSummaryList(ctx, agentId, versionId).Execute()





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
	versionId := "versionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsVersionsEvalSummaryList(context.Background(), agentId, versionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsVersionsEvalSummaryList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsVersionsEvalSummaryList`: EvalSummaryResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsVersionsEvalSummaryList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 
**versionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsVersionsEvalSummaryListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



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


## SimulateAgentDefinitionsVersionsList

> []AgentVersionListResponse SimulateAgentDefinitionsVersionsList(ctx, agentId).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsVersionsList(context.Background(), agentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsVersionsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsVersionsList`: []AgentVersionListResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsVersionsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsVersionsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**[]AgentVersionListResponse**](AgentVersionListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateAgentDefinitionsVersionsRead

> AgentVersionResponse SimulateAgentDefinitionsVersionsRead(ctx, agentId, versionId).Execute()





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
	versionId := "versionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsVersionsRead(context.Background(), agentId, versionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsVersionsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsVersionsRead`: AgentVersionResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsVersionsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 
**versionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsVersionsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**AgentVersionResponse**](AgentVersionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateAgentDefinitionsVersionsRestoreCreate

> AgentVersionRestoreResponse SimulateAgentDefinitionsVersionsRestoreCreate(ctx, agentId, versionId).Body(body).Execute()





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
	versionId := "versionId_example" // string | 
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateAgentDefinitionsVersionsRestoreCreate(context.Background(), agentId, versionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateAgentDefinitionsVersionsRestoreCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateAgentDefinitionsVersionsRestoreCreate`: AgentVersionRestoreResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateAgentDefinitionsVersionsRestoreCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 
**versionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateAgentDefinitionsVersionsRestoreCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **body** | **map[string]interface{}** |  | 

### Return type

[**AgentVersionRestoreResponse**](AgentVersionRestoreResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateApiCallExecutionsList

> []CallExecution SimulateApiCallExecutionsList(ctx).Search(search).Status(status).TestExecutionId(testExecutionId).Page(page).Limit(limit).Execute()





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
	status := "status_example" // string |  (optional) (default to "")
	testExecutionId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateApiCallExecutionsList(context.Background()).Search(search).Status(status).TestExecutionId(testExecutionId).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateApiCallExecutionsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateApiCallExecutionsList`: []CallExecution
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateApiCallExecutionsList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSimulateApiCallExecutionsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **string** |  | [default to &quot;&quot;]
 **status** | **string** |  | [default to &quot;&quot;]
 **testExecutionId** | **string** |  | 
 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | 

### Return type

[**[]CallExecution**](CallExecution.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateApiPersonasDuplicate

> PersonaDuplicateResponse SimulateApiPersonasDuplicate(ctx, id).PersonaDuplicateRequest(personaDuplicateRequest).Execute()





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
	id := "id_example" // string | 
	personaDuplicateRequest := *openapiclient.NewPersonaDuplicateRequest("Name_example") // PersonaDuplicateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateApiPersonasDuplicate(context.Background(), id).PersonaDuplicateRequest(personaDuplicateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateApiPersonasDuplicate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateApiPersonasDuplicate`: PersonaDuplicateResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateApiPersonasDuplicate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateApiPersonasDuplicateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **personaDuplicateRequest** | [**PersonaDuplicateRequest**](PersonaDuplicateRequest.md) |  | 

### Return type

[**PersonaDuplicateResponse**](PersonaDuplicateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateApiPersonasDuplicateCreate

> PersonaDuplicateResponse SimulateApiPersonasDuplicateCreate(ctx, personaId).PersonaDuplicateRequest(personaDuplicateRequest).Execute()





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
	personaId := "personaId_example" // string | 
	personaDuplicateRequest := *openapiclient.NewPersonaDuplicateRequest("Name_example") // PersonaDuplicateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateApiPersonasDuplicateCreate(context.Background(), personaId).PersonaDuplicateRequest(personaDuplicateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateApiPersonasDuplicateCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateApiPersonasDuplicateCreate`: PersonaDuplicateResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateApiPersonasDuplicateCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**personaId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateApiPersonasDuplicateCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **personaDuplicateRequest** | [**PersonaDuplicateRequest**](PersonaDuplicateRequest.md) |  | 

### Return type

[**PersonaDuplicateResponse**](PersonaDuplicateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateApiPersonasFieldOptions

> SimulateApiPersonasFieldOptions200Response SimulateApiPersonasFieldOptions(ctx).Page(page).Limit(limit).Execute()





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
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateApiPersonasFieldOptions(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateApiPersonasFieldOptions``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateApiPersonasFieldOptions`: SimulateApiPersonasFieldOptions200Response
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateApiPersonasFieldOptions`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSimulateApiPersonasFieldOptionsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**SimulateApiPersonasFieldOptions200Response**](SimulateApiPersonasFieldOptions200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateApiPersonasSystemPersonas

> SimulateApiPersonasSystemPersonas200Response SimulateApiPersonasSystemPersonas(ctx).Page(page).Limit(limit).Execute()





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
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateApiPersonasSystemPersonas(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateApiPersonasSystemPersonas``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateApiPersonasSystemPersonas`: SimulateApiPersonasSystemPersonas200Response
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateApiPersonasSystemPersonas`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSimulateApiPersonasSystemPersonasRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**SimulateApiPersonasSystemPersonas200Response**](SimulateApiPersonasSystemPersonas200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateApiPersonasUpdate

> Persona SimulateApiPersonasUpdate(ctx, id).Persona(persona).Execute()





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
	id := "id_example" // string | 
	persona := *openapiclient.NewPersona("Name_example") // Persona | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateApiPersonasUpdate(context.Background(), id).Persona(persona).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateApiPersonasUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateApiPersonasUpdate`: Persona
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateApiPersonasUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**id** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateApiPersonasUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **persona** | [**Persona**](Persona.md) |  | 

### Return type

[**Persona**](Persona.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateApiPersonasWorkspacePersonas

> SimulateApiPersonasSystemPersonas200Response SimulateApiPersonasWorkspacePersonas(ctx).Page(page).Limit(limit).Execute()





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
	page := int32(56) // int32 | A page number within the paginated result set. (optional)
	limit := int32(56) // int32 | Number of results to return per page. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateApiPersonasWorkspacePersonas(context.Background()).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateApiPersonasWorkspacePersonas``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateApiPersonasWorkspacePersonas`: SimulateApiPersonasSystemPersonas200Response
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateApiPersonasWorkspacePersonas`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSimulateApiPersonasWorkspacePersonasRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32** | A page number within the paginated result set. | 
 **limit** | **int32** | Number of results to return per page. | 

### Return type

[**SimulateApiPersonasSystemPersonas200Response**](SimulateApiPersonasSystemPersonas200Response.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateApiRunTestsList

> []RunTestResponse SimulateApiRunTestsList(ctx).Search(search).SimulationType(simulationType).PromptTemplateId(promptTemplateId).Page(page).Limit(limit).Execute()





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
	simulationType := "simulationType_example" // string |  (optional)
	promptTemplateId := "38400000-8cf0-11bd-b23e-10b96e4ef00d" // string |  (optional)
	page := int32(56) // int32 |  (optional) (default to 1)
	limit := int32(56) // int32 |  (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateApiRunTestsList(context.Background()).Search(search).SimulationType(simulationType).PromptTemplateId(promptTemplateId).Page(page).Limit(limit).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateApiRunTestsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateApiRunTestsList`: []RunTestResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateApiRunTestsList`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSimulateApiRunTestsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **string** |  | [default to &quot;&quot;]
 **simulationType** | **string** |  | 
 **promptTemplateId** | **string** |  | 
 **page** | **int32** |  | [default to 1]
 **limit** | **int32** |  | 

### Return type

[**[]RunTestResponse**](RunTestResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsBranchAnalysisCreate

> CallBranchDeviationCreateResponse SimulateCallExecutionsBranchAnalysisCreate(ctx, callExecutionId).Body(body).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsBranchAnalysisCreate(context.Background(), callExecutionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsBranchAnalysisCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsBranchAnalysisCreate`: CallBranchDeviationCreateResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsBranchAnalysisCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsBranchAnalysisCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**CallBranchDeviationCreateResponse**](CallBranchDeviationCreateResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsBranchAnalysisList

> CallBranchAnalysisResponse SimulateCallExecutionsBranchAnalysisList(ctx, callExecutionId).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsBranchAnalysisList(context.Background(), callExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsBranchAnalysisList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsBranchAnalysisList`: CallBranchAnalysisResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsBranchAnalysisList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsBranchAnalysisListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CallBranchAnalysisResponse**](CallBranchAnalysisResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsChatSendMessageCreate

> ChatSendMessageResponse SimulateCallExecutionsChatSendMessageCreate(ctx, callExecutionId).SendChatRequest(sendChatRequest).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 
	sendChatRequest := *openapiclient.NewSendChatRequest() // SendChatRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsChatSendMessageCreate(context.Background(), callExecutionId).SendChatRequest(sendChatRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsChatSendMessageCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsChatSendMessageCreate`: ChatSendMessageResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsChatSendMessageCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsChatSendMessageCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **sendChatRequest** | [**SendChatRequest**](SendChatRequest.md) |  | 

### Return type

[**ChatSendMessageResponse**](ChatSendMessageResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsDeleteDelete

> CallExecutionDeleteResponse SimulateCallExecutionsDeleteDelete(ctx, callExecutionId).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsDeleteDelete(context.Background(), callExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsDeleteDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsDeleteDelete`: CallExecutionDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsDeleteDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsDeleteDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CallExecutionDeleteResponse**](CallExecutionDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsErrorLocalizerTasksList

> CallExecutionErrorLocalizerTasksResponse SimulateCallExecutionsErrorLocalizerTasksList(ctx, callExecutionId).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsErrorLocalizerTasksList(context.Background(), callExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsErrorLocalizerTasksList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsErrorLocalizerTasksList`: CallExecutionErrorLocalizerTasksResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsErrorLocalizerTasksList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsErrorLocalizerTasksListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CallExecutionErrorLocalizerTasksResponse**](CallExecutionErrorLocalizerTasksResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsLogsList

> CallExecutionLogsResponse SimulateCallExecutionsLogsList(ctx, callExecutionId).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsLogsList(context.Background(), callExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsLogsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsLogsList`: CallExecutionLogsResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsLogsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsLogsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CallExecutionLogsResponse**](CallExecutionLogsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsPartialUpdate

> CallExecution SimulateCallExecutionsPartialUpdate(ctx, callExecutionId).CallExecutionStatusUpdate(callExecutionStatusUpdate).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 
	callExecutionStatusUpdate := *openapiclient.NewCallExecutionStatusUpdate("Status_example") // CallExecutionStatusUpdate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsPartialUpdate(context.Background(), callExecutionId).CallExecutionStatusUpdate(callExecutionStatusUpdate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsPartialUpdate`: CallExecution
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **callExecutionStatusUpdate** | [**CallExecutionStatusUpdate**](CallExecutionStatusUpdate.md) |  | 

### Return type

[**CallExecution**](CallExecution.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsRead

> CallExecutionDetail SimulateCallExecutionsRead(ctx, callExecutionId).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsRead(context.Background(), callExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsRead`: CallExecutionDetail
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CallExecutionDetail**](CallExecutionDetail.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsSessionComparisonList

> SessionComparisonResponse SimulateCallExecutionsSessionComparisonList(ctx, callExecutionId).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsSessionComparisonList(context.Background(), callExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsSessionComparisonList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsSessionComparisonList`: SessionComparisonResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsSessionComparisonList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsSessionComparisonListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**SessionComparisonResponse**](SessionComparisonResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateCallExecutionsTranscriptsList

> CallTranscriptResponse SimulateCallExecutionsTranscriptsList(ctx, callExecutionId).Execute()





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
	callExecutionId := "callExecutionId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateCallExecutionsTranscriptsList(context.Background(), callExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateCallExecutionsTranscriptsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateCallExecutionsTranscriptsList`: CallTranscriptResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateCallExecutionsTranscriptsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**callExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateCallExecutionsTranscriptsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**CallTranscriptResponse**](CallTranscriptResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateExportRead

> *os.File SimulateExportRead(ctx, itemId).Type_(type_).Search(search).Status(status).Execute()





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
	itemId := "itemId_example" // string | 
	type_ := "type__example" // string | Export source type.
	search := "search_example" // string | Optional call-execution search term. (optional)
	status := "status_example" // string | Optional call-execution status filter. (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateExportRead(context.Background(), itemId).Type_(type_).Search(search).Status(status).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateExportRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateExportRead`: *os.File
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateExportRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**itemId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateExportReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **type_** | **string** | Export source type. | 
 **search** | **string** | Optional call-execution search term. | 
 **status** | **string** | Optional call-execution status filter. | 

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


## SimulatePromptSimulationsScenariosList

> PromptSimulationScenariosResponse SimulatePromptSimulationsScenariosList(ctx).Execute()

Get list of scenarios available for prompt simulations.



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
	resp, r, err := apiClient.SimulateAPI.SimulatePromptSimulationsScenariosList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulatePromptSimulationsScenariosList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulatePromptSimulationsScenariosList`: PromptSimulationScenariosResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulatePromptSimulationsScenariosList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiSimulatePromptSimulationsScenariosListRequest struct via the builder pattern


### Return type

[**PromptSimulationScenariosResponse**](PromptSimulationScenariosResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulatePromptTemplatesSimulationsCreate

> PromptSimulationRunResponse SimulatePromptTemplatesSimulationsCreate(ctx, promptTemplateId).CreatePromptSimulationRequest(createPromptSimulationRequest).Execute()

Create a new prompt-based simulation run.



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
	promptTemplateId := "promptTemplateId_example" // string | 
	createPromptSimulationRequest := *openapiclient.NewCreatePromptSimulationRequest("Name_example", "PromptVersionId_example", []string{"ScenarioIds_example"}) // CreatePromptSimulationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulatePromptTemplatesSimulationsCreate(context.Background(), promptTemplateId).CreatePromptSimulationRequest(createPromptSimulationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulatePromptTemplatesSimulationsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulatePromptTemplatesSimulationsCreate`: PromptSimulationRunResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulatePromptTemplatesSimulationsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptTemplateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulatePromptTemplatesSimulationsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **createPromptSimulationRequest** | [**CreatePromptSimulationRequest**](CreatePromptSimulationRequest.md) |  | 

### Return type

[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulatePromptTemplatesSimulationsDelete

> SimulatePromptTemplatesSimulationsDelete(ctx, promptTemplateId, runTestId).Execute()





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
	promptTemplateId := "promptTemplateId_example" // string | 
	runTestId := "runTestId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.SimulateAPI.SimulatePromptTemplatesSimulationsDelete(context.Background(), promptTemplateId, runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulatePromptTemplatesSimulationsDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptTemplateId** | **string** |  | 
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulatePromptTemplatesSimulationsDeleteRequest struct via the builder pattern


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


## SimulatePromptTemplatesSimulationsExecuteCreate

> ExecutePromptSimulationResponse SimulatePromptTemplatesSimulationsExecuteCreate(ctx, promptTemplateId, runTestId).ExecutePromptSimulationRequest(executePromptSimulationRequest).Execute()

Execute a prompt-based simulation run.



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
	promptTemplateId := "promptTemplateId_example" // string | 
	runTestId := "runTestId_example" // string | 
	executePromptSimulationRequest := *openapiclient.NewExecutePromptSimulationRequest() // ExecutePromptSimulationRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulatePromptTemplatesSimulationsExecuteCreate(context.Background(), promptTemplateId, runTestId).ExecutePromptSimulationRequest(executePromptSimulationRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulatePromptTemplatesSimulationsExecuteCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulatePromptTemplatesSimulationsExecuteCreate`: ExecutePromptSimulationResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulatePromptTemplatesSimulationsExecuteCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptTemplateId** | **string** |  | 
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulatePromptTemplatesSimulationsExecuteCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **executePromptSimulationRequest** | [**ExecutePromptSimulationRequest**](ExecutePromptSimulationRequest.md) |  | 

### Return type

[**ExecutePromptSimulationResponse**](ExecutePromptSimulationResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulatePromptTemplatesSimulationsList

> PromptSimulationListResponse SimulatePromptTemplatesSimulationsList(ctx, promptTemplateId).Execute()

Get paginated list of simulation runs for a specific prompt template.



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
	promptTemplateId := "promptTemplateId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulatePromptTemplatesSimulationsList(context.Background(), promptTemplateId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulatePromptTemplatesSimulationsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulatePromptTemplatesSimulationsList`: PromptSimulationListResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulatePromptTemplatesSimulationsList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptTemplateId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulatePromptTemplatesSimulationsListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**PromptSimulationListResponse**](PromptSimulationListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulatePromptTemplatesSimulationsPartialUpdate

> PromptSimulationRunResponse SimulatePromptTemplatesSimulationsPartialUpdate(ctx, promptTemplateId, runTestId).PromptSimulationUpdateRequest(promptSimulationUpdateRequest).Execute()





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
	promptTemplateId := "promptTemplateId_example" // string | 
	runTestId := "runTestId_example" // string | 
	promptSimulationUpdateRequest := *openapiclient.NewPromptSimulationUpdateRequest() // PromptSimulationUpdateRequest | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulatePromptTemplatesSimulationsPartialUpdate(context.Background(), promptTemplateId, runTestId).PromptSimulationUpdateRequest(promptSimulationUpdateRequest).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulatePromptTemplatesSimulationsPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulatePromptTemplatesSimulationsPartialUpdate`: PromptSimulationRunResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulatePromptTemplatesSimulationsPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptTemplateId** | **string** |  | 
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulatePromptTemplatesSimulationsPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


 **promptSimulationUpdateRequest** | [**PromptSimulationUpdateRequest**](PromptSimulationUpdateRequest.md) |  | 

### Return type

[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulatePromptTemplatesSimulationsRead

> PromptSimulationRunResponse SimulatePromptTemplatesSimulationsRead(ctx, promptTemplateId, runTestId).Execute()





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
	promptTemplateId := "promptTemplateId_example" // string | 
	runTestId := "runTestId_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulatePromptTemplatesSimulationsRead(context.Background(), promptTemplateId, runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulatePromptTemplatesSimulationsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulatePromptTemplatesSimulationsRead`: PromptSimulationRunResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulatePromptTemplatesSimulationsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**promptTemplateId** | **string** |  | 
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulatePromptTemplatesSimulationsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsActiveList

> AllActiveTests SimulateRunTestsActiveList(ctx).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsActiveList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsActiveList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsActiveList`: AllActiveTests
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsActiveList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsActiveListRequest struct via the builder pattern


### Return type

[**AllActiveTests**](AllActiveTests.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsChatExecuteCreate

> RunTestChatExecutionResponse SimulateRunTestsChatExecuteCreate(ctx, runTestId).Body(body).Execute()





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
	body := map[string]interface{}{ ... } // map[string]interface{} | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsChatExecuteCreate(context.Background(), runTestId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsChatExecuteCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsChatExecuteCreate`: RunTestChatExecutionResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsChatExecuteCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsChatExecuteCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**RunTestChatExecutionResponse**](RunTestChatExecutionResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsComponentsPartialUpdate

> RunTestResponse SimulateRunTestsComponentsPartialUpdate(ctx, runTestId).RunTestComponentsUpdate(runTestComponentsUpdate).Execute()





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
	runTestComponentsUpdate := *openapiclient.NewRunTestComponentsUpdate() // RunTestComponentsUpdate | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsComponentsPartialUpdate(context.Background(), runTestId).RunTestComponentsUpdate(runTestComponentsUpdate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsComponentsPartialUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsComponentsPartialUpdate`: RunTestResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsComponentsPartialUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsComponentsPartialUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **runTestComponentsUpdate** | [**RunTestComponentsUpdate**](RunTestComponentsUpdate.md) |  | 

### Return type

[**RunTestResponse**](RunTestResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsDeleteDelete

> SimulateRunTestsDeleteDelete(ctx, runTestId).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	r, err := apiClient.SimulateAPI.SimulateRunTestsDeleteDelete(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsDeleteDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsDeleteDeleteRequest struct via the builder pattern


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


## SimulateRunTestsDeleteTestExecutionsCreate

> TestExecutionBulkDeleteResponse SimulateRunTestsDeleteTestExecutionsCreate(ctx, runTestId).TestExecutionBulkDelete(testExecutionBulkDelete).Execute()





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
	testExecutionBulkDelete := *openapiclient.NewTestExecutionBulkDelete() // TestExecutionBulkDelete | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsDeleteTestExecutionsCreate(context.Background(), runTestId).TestExecutionBulkDelete(testExecutionBulkDelete).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsDeleteTestExecutionsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsDeleteTestExecutionsCreate`: TestExecutionBulkDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsDeleteTestExecutionsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsDeleteTestExecutionsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **testExecutionBulkDelete** | [**TestExecutionBulkDelete**](TestExecutionBulkDelete.md) |  | 

### Return type

[**TestExecutionBulkDeleteResponse**](TestExecutionBulkDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsEvalConfigsGetStructureList

> EvalConfigStructureResponse SimulateRunTestsEvalConfigsGetStructureList(ctx, runTestId, evalConfigId).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsEvalConfigsGetStructureList(context.Background(), runTestId, evalConfigId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsEvalConfigsGetStructureList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsEvalConfigsGetStructureList`: EvalConfigStructureResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsEvalConfigsGetStructureList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 
**evalConfigId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsEvalConfigsGetStructureListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------



### Return type

[**EvalConfigStructureResponse**](EvalConfigStructureResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsGetIdByNameRead

> RunTestNameResponse SimulateRunTestsGetIdByNameRead(ctx, runTestName).Execute()





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
	runTestName := "runTestName_example" // string | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsGetIdByNameRead(context.Background(), runTestName).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsGetIdByNameRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsGetIdByNameRead`: RunTestNameResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsGetIdByNameRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestName** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsGetIdByNameReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**RunTestNameResponse**](RunTestNameResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsRerunTestExecutionsCreate

> TestExecutionRerunResponse SimulateRunTestsRerunTestExecutionsCreate(ctx, runTestId).TestExecutionRerun(testExecutionRerun).Execute()





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
	testExecutionRerun := *openapiclient.NewTestExecutionRerun("RerunType_example") // TestExecutionRerun | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsRerunTestExecutionsCreate(context.Background(), runTestId).TestExecutionRerun(testExecutionRerun).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsRerunTestExecutionsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsRerunTestExecutionsCreate`: TestExecutionRerunResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsRerunTestExecutionsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsRerunTestExecutionsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **testExecutionRerun** | [**TestExecutionRerun**](TestExecutionRerun.md) |  | 

### Return type

[**TestExecutionRerunResponse**](TestExecutionRerunResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsScenariosList

> []RunTestScenarioItemResponse SimulateRunTestsScenariosList(ctx, runTestId).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsScenariosList(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsScenariosList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsScenariosList`: []RunTestScenarioItemResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsScenariosList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsScenariosListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**[]RunTestScenarioItemResponse**](RunTestScenarioItemResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateRunTestsSdkCodeList

> ChatSDKCodeResponse SimulateRunTestsSdkCodeList(ctx, runTestId).Execute()





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

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateRunTestsSdkCodeList(context.Background(), runTestId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateRunTestsSdkCodeList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateRunTestsSdkCodeList`: ChatSDKCodeResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateRunTestsSdkCodeList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**runTestId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateRunTestsSdkCodeListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**ChatSDKCodeResponse**](ChatSDKCodeResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateSimulatorAgentsCreateCreate

> SimulatorAgent SimulateSimulatorAgentsCreateCreate(ctx).SimulatorAgent(simulatorAgent).Execute()





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
	simulatorAgent := *openapiclient.NewSimulatorAgent("Name_example", "Prompt_example", "VoiceProvider_example", "VoiceName_example", "Model_example") // SimulatorAgent | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateSimulatorAgentsCreateCreate(context.Background()).SimulatorAgent(simulatorAgent).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateSimulatorAgentsCreateCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateSimulatorAgentsCreateCreate`: SimulatorAgent
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateSimulatorAgentsCreateCreate`: %v\n", resp)
}
```

### Path Parameters



### Other Parameters

Other parameters are passed through a pointer to a apiSimulateSimulatorAgentsCreateCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **simulatorAgent** | [**SimulatorAgent**](SimulatorAgent.md) |  | 

### Return type

[**SimulatorAgent**](SimulatorAgent.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateSimulatorAgentsDeleteDelete

> SimulatorAgentDeleteResponse SimulateSimulatorAgentsDeleteDelete(ctx, agentId).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateSimulatorAgentsDeleteDelete(context.Background(), agentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateSimulatorAgentsDeleteDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateSimulatorAgentsDeleteDelete`: SimulatorAgentDeleteResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateSimulatorAgentsDeleteDelete`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateSimulatorAgentsDeleteDeleteRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**SimulatorAgentDeleteResponse**](SimulatorAgentDeleteResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateSimulatorAgentsEditUpdate

> SimulatorAgent SimulateSimulatorAgentsEditUpdate(ctx, agentId).SimulatorAgent(simulatorAgent).Execute()





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
	simulatorAgent := *openapiclient.NewSimulatorAgent("Name_example", "Prompt_example", "VoiceProvider_example", "VoiceName_example", "Model_example") // SimulatorAgent | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateSimulatorAgentsEditUpdate(context.Background(), agentId).SimulatorAgent(simulatorAgent).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateSimulatorAgentsEditUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateSimulatorAgentsEditUpdate`: SimulatorAgent
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateSimulatorAgentsEditUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateSimulatorAgentsEditUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **simulatorAgent** | [**SimulatorAgent**](SimulatorAgent.md) |  | 

### Return type

[**SimulatorAgent**](SimulatorAgent.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateSimulatorAgentsList

> SimulatorAgentListResponse SimulateSimulatorAgentsList(ctx).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateSimulatorAgentsList(context.Background()).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateSimulatorAgentsList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateSimulatorAgentsList`: SimulatorAgentListResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateSimulatorAgentsList`: %v\n", resp)
}
```

### Path Parameters

This endpoint does not need any parameter.

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateSimulatorAgentsListRequest struct via the builder pattern


### Return type

[**SimulatorAgentListResponse**](SimulatorAgentListResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateSimulatorAgentsRead

> SimulatorAgent SimulateSimulatorAgentsRead(ctx, agentId).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateSimulatorAgentsRead(context.Background(), agentId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateSimulatorAgentsRead``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateSimulatorAgentsRead`: SimulatorAgent
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateSimulatorAgentsRead`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**agentId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateSimulatorAgentsReadRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**SimulatorAgent**](SimulatorAgent.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateTestExecutionsChatCallExecutionsBatchCreate

> TestExecutionChatBatchResponse SimulateTestExecutionsChatCallExecutionsBatchCreate(ctx, testExecutionId).Body(body).Execute()

Create a batch of CallExecution records for chat execution (exactly 10 per API call).



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
	resp, r, err := apiClient.SimulateAPI.SimulateTestExecutionsChatCallExecutionsBatchCreate(context.Background(), testExecutionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateTestExecutionsChatCallExecutionsBatchCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateTestExecutionsChatCallExecutionsBatchCreate`: TestExecutionChatBatchResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateTestExecutionsChatCallExecutionsBatchCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateTestExecutionsChatCallExecutionsBatchCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**TestExecutionChatBatchResponse**](TestExecutionChatBatchResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateTestExecutionsColumnOrderUpdate

> TestExecutionColumnOrderResponse SimulateTestExecutionsColumnOrderUpdate(ctx, testExecutionId).TestExecutionColumnOrder(testExecutionColumnOrder).Execute()





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
	testExecutionColumnOrder := *openapiclient.NewTestExecutionColumnOrder([]openapiclient.ColumnOrder{*openapiclient.NewColumnOrder("ColumnName_example", "Id_example", false)}) // TestExecutionColumnOrder | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateTestExecutionsColumnOrderUpdate(context.Background(), testExecutionId).TestExecutionColumnOrder(testExecutionColumnOrder).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateTestExecutionsColumnOrderUpdate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateTestExecutionsColumnOrderUpdate`: TestExecutionColumnOrderResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateTestExecutionsColumnOrderUpdate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateTestExecutionsColumnOrderUpdateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **testExecutionColumnOrder** | [**TestExecutionColumnOrder**](TestExecutionColumnOrder.md) |  | 

### Return type

[**TestExecutionColumnOrderResponse**](TestExecutionColumnOrderResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateTestExecutionsDeleteDelete

> SimulateTestExecutionsDeleteDelete(ctx, testExecutionId).Execute()





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
	r, err := apiClient.SimulateAPI.SimulateTestExecutionsDeleteDelete(context.Background(), testExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateTestExecutionsDeleteDelete``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateTestExecutionsDeleteDeleteRequest struct via the builder pattern


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


## SimulateTestExecutionsEvalExplanationSummaryList

> EvalExplanationSummaryResponse SimulateTestExecutionsEvalExplanationSummaryList(ctx, testExecutionId).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateTestExecutionsEvalExplanationSummaryList(context.Background(), testExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateTestExecutionsEvalExplanationSummaryList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateTestExecutionsEvalExplanationSummaryList`: EvalExplanationSummaryResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateTestExecutionsEvalExplanationSummaryList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateTestExecutionsEvalExplanationSummaryListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**EvalExplanationSummaryResponse**](EvalExplanationSummaryResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateTestExecutionsEvalExplanationSummaryRefreshCreate

> EvalExplanationSummaryRefreshResponse SimulateTestExecutionsEvalExplanationSummaryRefreshCreate(ctx, testExecutionId).Body(body).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateTestExecutionsEvalExplanationSummaryRefreshCreate(context.Background(), testExecutionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateTestExecutionsEvalExplanationSummaryRefreshCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateTestExecutionsEvalExplanationSummaryRefreshCreate`: EvalExplanationSummaryRefreshResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateTestExecutionsEvalExplanationSummaryRefreshCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateTestExecutionsEvalExplanationSummaryRefreshCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**EvalExplanationSummaryRefreshResponse**](EvalExplanationSummaryRefreshResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateTestExecutionsOptimiserAnalysisList

> OptimiserAnalysisResponse SimulateTestExecutionsOptimiserAnalysisList(ctx, testExecutionId).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateTestExecutionsOptimiserAnalysisList(context.Background(), testExecutionId).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateTestExecutionsOptimiserAnalysisList``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateTestExecutionsOptimiserAnalysisList`: OptimiserAnalysisResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateTestExecutionsOptimiserAnalysisList`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateTestExecutionsOptimiserAnalysisListRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------


### Return type

[**OptimiserAnalysisResponse**](OptimiserAnalysisResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateTestExecutionsOptimiserAnalysisRefreshCreate

> OptimiserAnalysisRefreshResponse SimulateTestExecutionsOptimiserAnalysisRefreshCreate(ctx, testExecutionId).Body(body).Execute()





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
	resp, r, err := apiClient.SimulateAPI.SimulateTestExecutionsOptimiserAnalysisRefreshCreate(context.Background(), testExecutionId).Body(body).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateTestExecutionsOptimiserAnalysisRefreshCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateTestExecutionsOptimiserAnalysisRefreshCreate`: OptimiserAnalysisRefreshResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateTestExecutionsOptimiserAnalysisRefreshCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateTestExecutionsOptimiserAnalysisRefreshCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **body** | **map[string]interface{}** |  | 

### Return type

[**OptimiserAnalysisRefreshResponse**](OptimiserAnalysisRefreshResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## SimulateTestExecutionsRerunCallsCreate

> RerunCallsResponse SimulateTestExecutionsRerunCallsCreate(ctx, testExecutionId).CallExecutionRerun(callExecutionRerun).Execute()





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
	callExecutionRerun := *openapiclient.NewCallExecutionRerun("RerunType_example") // CallExecutionRerun | 

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.SimulateAPI.SimulateTestExecutionsRerunCallsCreate(context.Background(), testExecutionId).CallExecutionRerun(callExecutionRerun).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `SimulateAPI.SimulateTestExecutionsRerunCallsCreate``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `SimulateTestExecutionsRerunCallsCreate`: RerunCallsResponse
	fmt.Fprintf(os.Stdout, "Response from `SimulateAPI.SimulateTestExecutionsRerunCallsCreate`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**testExecutionId** | **string** |  | 

### Other Parameters

Other parameters are passed through a pointer to a apiSimulateTestExecutionsRerunCallsCreateRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **callExecutionRerun** | [**CallExecutionRerun**](CallExecutionRerun.md) |  | 

### Return type

[**RerunCallsResponse**](RerunCallsResponse.md)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

