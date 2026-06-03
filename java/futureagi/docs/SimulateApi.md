# SimulateApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**simulateAgentDefinitionsDelete**](SimulateApi.md#simulateAgentDefinitionsDelete) | **DELETE** /simulate/agent-definitions/ |  |
| [**simulateAgentDefinitionsDeleteWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsDeleteWithHttpInfo) | **DELETE** /simulate/agent-definitions/ |  |
| [**simulateAgentDefinitionsVersionsActivateCreate**](SimulateApi.md#simulateAgentDefinitionsVersionsActivateCreate) | **POST** /simulate/agent-definitions/{agent_id}/versions/{version_id}/activate/ |  |
| [**simulateAgentDefinitionsVersionsActivateCreateWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsVersionsActivateCreateWithHttpInfo) | **POST** /simulate/agent-definitions/{agent_id}/versions/{version_id}/activate/ |  |
| [**simulateAgentDefinitionsVersionsCallExecutionsList**](SimulateApi.md#simulateAgentDefinitionsVersionsCallExecutionsList) | **GET** /simulate/agent-definitions/{agent_id}/versions/{version_id}/call-executions/ |  |
| [**simulateAgentDefinitionsVersionsCallExecutionsListWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsVersionsCallExecutionsListWithHttpInfo) | **GET** /simulate/agent-definitions/{agent_id}/versions/{version_id}/call-executions/ |  |
| [**simulateAgentDefinitionsVersionsCreateCreate**](SimulateApi.md#simulateAgentDefinitionsVersionsCreateCreate) | **POST** /simulate/agent-definitions/{agent_id}/versions/create/ |  |
| [**simulateAgentDefinitionsVersionsCreateCreateWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsVersionsCreateCreateWithHttpInfo) | **POST** /simulate/agent-definitions/{agent_id}/versions/create/ |  |
| [**simulateAgentDefinitionsVersionsDeleteDelete**](SimulateApi.md#simulateAgentDefinitionsVersionsDeleteDelete) | **DELETE** /simulate/agent-definitions/{agent_id}/versions/{version_id}/delete/ |  |
| [**simulateAgentDefinitionsVersionsDeleteDeleteWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsVersionsDeleteDeleteWithHttpInfo) | **DELETE** /simulate/agent-definitions/{agent_id}/versions/{version_id}/delete/ |  |
| [**simulateAgentDefinitionsVersionsEvalSummaryList**](SimulateApi.md#simulateAgentDefinitionsVersionsEvalSummaryList) | **GET** /simulate/agent-definitions/{agent_id}/versions/{version_id}/eval-summary/ |  |
| [**simulateAgentDefinitionsVersionsEvalSummaryListWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsVersionsEvalSummaryListWithHttpInfo) | **GET** /simulate/agent-definitions/{agent_id}/versions/{version_id}/eval-summary/ |  |
| [**simulateAgentDefinitionsVersionsList**](SimulateApi.md#simulateAgentDefinitionsVersionsList) | **GET** /simulate/agent-definitions/{agent_id}/versions/ |  |
| [**simulateAgentDefinitionsVersionsListWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsVersionsListWithHttpInfo) | **GET** /simulate/agent-definitions/{agent_id}/versions/ |  |
| [**simulateAgentDefinitionsVersionsRead**](SimulateApi.md#simulateAgentDefinitionsVersionsRead) | **GET** /simulate/agent-definitions/{agent_id}/versions/{version_id}/ |  |
| [**simulateAgentDefinitionsVersionsReadWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsVersionsReadWithHttpInfo) | **GET** /simulate/agent-definitions/{agent_id}/versions/{version_id}/ |  |
| [**simulateAgentDefinitionsVersionsRestoreCreate**](SimulateApi.md#simulateAgentDefinitionsVersionsRestoreCreate) | **POST** /simulate/agent-definitions/{agent_id}/versions/{version_id}/restore/ |  |
| [**simulateAgentDefinitionsVersionsRestoreCreateWithHttpInfo**](SimulateApi.md#simulateAgentDefinitionsVersionsRestoreCreateWithHttpInfo) | **POST** /simulate/agent-definitions/{agent_id}/versions/{version_id}/restore/ |  |
| [**simulateApiCallExecutionsList**](SimulateApi.md#simulateApiCallExecutionsList) | **GET** /simulate/api/call-executions/ |  |
| [**simulateApiCallExecutionsListWithHttpInfo**](SimulateApi.md#simulateApiCallExecutionsListWithHttpInfo) | **GET** /simulate/api/call-executions/ |  |
| [**simulateApiPersonasDuplicate**](SimulateApi.md#simulateApiPersonasDuplicate) | **POST** /simulate/api/personas/{id}/duplicate/ |  |
| [**simulateApiPersonasDuplicateWithHttpInfo**](SimulateApi.md#simulateApiPersonasDuplicateWithHttpInfo) | **POST** /simulate/api/personas/{id}/duplicate/ |  |
| [**simulateApiPersonasDuplicateCreate**](SimulateApi.md#simulateApiPersonasDuplicateCreate) | **POST** /simulate/api/personas/duplicate/{persona_id}/ |  |
| [**simulateApiPersonasDuplicateCreateWithHttpInfo**](SimulateApi.md#simulateApiPersonasDuplicateCreateWithHttpInfo) | **POST** /simulate/api/personas/duplicate/{persona_id}/ |  |
| [**simulateApiPersonasFieldOptions**](SimulateApi.md#simulateApiPersonasFieldOptions) | **GET** /simulate/api/personas/field-options/ |  |
| [**simulateApiPersonasFieldOptionsWithHttpInfo**](SimulateApi.md#simulateApiPersonasFieldOptionsWithHttpInfo) | **GET** /simulate/api/personas/field-options/ |  |
| [**simulateApiPersonasSystemPersonas**](SimulateApi.md#simulateApiPersonasSystemPersonas) | **GET** /simulate/api/personas/system/ |  |
| [**simulateApiPersonasSystemPersonasWithHttpInfo**](SimulateApi.md#simulateApiPersonasSystemPersonasWithHttpInfo) | **GET** /simulate/api/personas/system/ |  |
| [**simulateApiPersonasUpdate**](SimulateApi.md#simulateApiPersonasUpdate) | **PUT** /simulate/api/personas/{id}/ |  |
| [**simulateApiPersonasUpdateWithHttpInfo**](SimulateApi.md#simulateApiPersonasUpdateWithHttpInfo) | **PUT** /simulate/api/personas/{id}/ |  |
| [**simulateApiPersonasWorkspacePersonas**](SimulateApi.md#simulateApiPersonasWorkspacePersonas) | **GET** /simulate/api/personas/workspace/ |  |
| [**simulateApiPersonasWorkspacePersonasWithHttpInfo**](SimulateApi.md#simulateApiPersonasWorkspacePersonasWithHttpInfo) | **GET** /simulate/api/personas/workspace/ |  |
| [**simulateApiRunTestsList**](SimulateApi.md#simulateApiRunTestsList) | **GET** /simulate/api/run-tests/ |  |
| [**simulateApiRunTestsListWithHttpInfo**](SimulateApi.md#simulateApiRunTestsListWithHttpInfo) | **GET** /simulate/api/run-tests/ |  |
| [**simulateCallExecutionsBranchAnalysisCreate**](SimulateApi.md#simulateCallExecutionsBranchAnalysisCreate) | **POST** /simulate/call-executions/{call_execution_id}/branch-analysis/ |  |
| [**simulateCallExecutionsBranchAnalysisCreateWithHttpInfo**](SimulateApi.md#simulateCallExecutionsBranchAnalysisCreateWithHttpInfo) | **POST** /simulate/call-executions/{call_execution_id}/branch-analysis/ |  |
| [**simulateCallExecutionsBranchAnalysisList**](SimulateApi.md#simulateCallExecutionsBranchAnalysisList) | **GET** /simulate/call-executions/{call_execution_id}/branch-analysis/ |  |
| [**simulateCallExecutionsBranchAnalysisListWithHttpInfo**](SimulateApi.md#simulateCallExecutionsBranchAnalysisListWithHttpInfo) | **GET** /simulate/call-executions/{call_execution_id}/branch-analysis/ |  |
| [**simulateCallExecutionsChatSendMessageCreate**](SimulateApi.md#simulateCallExecutionsChatSendMessageCreate) | **POST** /simulate/call-executions/{call_execution_id}/chat/send-message/ |  |
| [**simulateCallExecutionsChatSendMessageCreateWithHttpInfo**](SimulateApi.md#simulateCallExecutionsChatSendMessageCreateWithHttpInfo) | **POST** /simulate/call-executions/{call_execution_id}/chat/send-message/ |  |
| [**simulateCallExecutionsDeleteDelete**](SimulateApi.md#simulateCallExecutionsDeleteDelete) | **DELETE** /simulate/call-executions/{call_execution_id}/delete/ |  |
| [**simulateCallExecutionsDeleteDeleteWithHttpInfo**](SimulateApi.md#simulateCallExecutionsDeleteDeleteWithHttpInfo) | **DELETE** /simulate/call-executions/{call_execution_id}/delete/ |  |
| [**simulateCallExecutionsErrorLocalizerTasksList**](SimulateApi.md#simulateCallExecutionsErrorLocalizerTasksList) | **GET** /simulate/call-executions/{call_execution_id}/error-localizer-tasks/ |  |
| [**simulateCallExecutionsErrorLocalizerTasksListWithHttpInfo**](SimulateApi.md#simulateCallExecutionsErrorLocalizerTasksListWithHttpInfo) | **GET** /simulate/call-executions/{call_execution_id}/error-localizer-tasks/ |  |
| [**simulateCallExecutionsLogsList**](SimulateApi.md#simulateCallExecutionsLogsList) | **GET** /simulate/call-executions/{call_execution_id}/logs/ |  |
| [**simulateCallExecutionsLogsListWithHttpInfo**](SimulateApi.md#simulateCallExecutionsLogsListWithHttpInfo) | **GET** /simulate/call-executions/{call_execution_id}/logs/ |  |
| [**simulateCallExecutionsPartialUpdate**](SimulateApi.md#simulateCallExecutionsPartialUpdate) | **PATCH** /simulate/call-executions/{call_execution_id}/ |  |
| [**simulateCallExecutionsPartialUpdateWithHttpInfo**](SimulateApi.md#simulateCallExecutionsPartialUpdateWithHttpInfo) | **PATCH** /simulate/call-executions/{call_execution_id}/ |  |
| [**simulateCallExecutionsRead**](SimulateApi.md#simulateCallExecutionsRead) | **GET** /simulate/call-executions/{call_execution_id}/ |  |
| [**simulateCallExecutionsReadWithHttpInfo**](SimulateApi.md#simulateCallExecutionsReadWithHttpInfo) | **GET** /simulate/call-executions/{call_execution_id}/ |  |
| [**simulateCallExecutionsSessionComparisonList**](SimulateApi.md#simulateCallExecutionsSessionComparisonList) | **GET** /simulate/call-executions/{call_execution_id}/session-comparison/ |  |
| [**simulateCallExecutionsSessionComparisonListWithHttpInfo**](SimulateApi.md#simulateCallExecutionsSessionComparisonListWithHttpInfo) | **GET** /simulate/call-executions/{call_execution_id}/session-comparison/ |  |
| [**simulateCallExecutionsTranscriptsList**](SimulateApi.md#simulateCallExecutionsTranscriptsList) | **GET** /simulate/call-executions/{call_execution_id}/transcripts/ |  |
| [**simulateCallExecutionsTranscriptsListWithHttpInfo**](SimulateApi.md#simulateCallExecutionsTranscriptsListWithHttpInfo) | **GET** /simulate/call-executions/{call_execution_id}/transcripts/ |  |
| [**simulateExportRead**](SimulateApi.md#simulateExportRead) | **GET** /simulate/export/{item_id}/ |  |
| [**simulateExportReadWithHttpInfo**](SimulateApi.md#simulateExportReadWithHttpInfo) | **GET** /simulate/export/{item_id}/ |  |
| [**simulatePromptSimulationsScenariosList**](SimulateApi.md#simulatePromptSimulationsScenariosList) | **GET** /simulate/prompt-simulations/scenarios/ | Get list of scenarios available for prompt simulations. |
| [**simulatePromptSimulationsScenariosListWithHttpInfo**](SimulateApi.md#simulatePromptSimulationsScenariosListWithHttpInfo) | **GET** /simulate/prompt-simulations/scenarios/ | Get list of scenarios available for prompt simulations. |
| [**simulatePromptTemplatesSimulationsCreate**](SimulateApi.md#simulatePromptTemplatesSimulationsCreate) | **POST** /simulate/prompt-templates/{prompt_template_id}/simulations/ | Create a new prompt-based simulation run. |
| [**simulatePromptTemplatesSimulationsCreateWithHttpInfo**](SimulateApi.md#simulatePromptTemplatesSimulationsCreateWithHttpInfo) | **POST** /simulate/prompt-templates/{prompt_template_id}/simulations/ | Create a new prompt-based simulation run. |
| [**simulatePromptTemplatesSimulationsDelete**](SimulateApi.md#simulatePromptTemplatesSimulationsDelete) | **DELETE** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ |  |
| [**simulatePromptTemplatesSimulationsDeleteWithHttpInfo**](SimulateApi.md#simulatePromptTemplatesSimulationsDeleteWithHttpInfo) | **DELETE** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ |  |
| [**simulatePromptTemplatesSimulationsExecuteCreate**](SimulateApi.md#simulatePromptTemplatesSimulationsExecuteCreate) | **POST** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/execute/ | Execute a prompt-based simulation run. |
| [**simulatePromptTemplatesSimulationsExecuteCreateWithHttpInfo**](SimulateApi.md#simulatePromptTemplatesSimulationsExecuteCreateWithHttpInfo) | **POST** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/execute/ | Execute a prompt-based simulation run. |
| [**simulatePromptTemplatesSimulationsList**](SimulateApi.md#simulatePromptTemplatesSimulationsList) | **GET** /simulate/prompt-templates/{prompt_template_id}/simulations/ | Get paginated list of simulation runs for a specific prompt template. |
| [**simulatePromptTemplatesSimulationsListWithHttpInfo**](SimulateApi.md#simulatePromptTemplatesSimulationsListWithHttpInfo) | **GET** /simulate/prompt-templates/{prompt_template_id}/simulations/ | Get paginated list of simulation runs for a specific prompt template. |
| [**simulatePromptTemplatesSimulationsPartialUpdate**](SimulateApi.md#simulatePromptTemplatesSimulationsPartialUpdate) | **PATCH** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ |  |
| [**simulatePromptTemplatesSimulationsPartialUpdateWithHttpInfo**](SimulateApi.md#simulatePromptTemplatesSimulationsPartialUpdateWithHttpInfo) | **PATCH** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ |  |
| [**simulatePromptTemplatesSimulationsRead**](SimulateApi.md#simulatePromptTemplatesSimulationsRead) | **GET** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ |  |
| [**simulatePromptTemplatesSimulationsReadWithHttpInfo**](SimulateApi.md#simulatePromptTemplatesSimulationsReadWithHttpInfo) | **GET** /simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/ |  |
| [**simulateRunTestsActiveList**](SimulateApi.md#simulateRunTestsActiveList) | **GET** /simulate/run-tests/active/ |  |
| [**simulateRunTestsActiveListWithHttpInfo**](SimulateApi.md#simulateRunTestsActiveListWithHttpInfo) | **GET** /simulate/run-tests/active/ |  |
| [**simulateRunTestsChatExecuteCreate**](SimulateApi.md#simulateRunTestsChatExecuteCreate) | **POST** /simulate/run-tests/{run_test_id}/chat-execute/ |  |
| [**simulateRunTestsChatExecuteCreateWithHttpInfo**](SimulateApi.md#simulateRunTestsChatExecuteCreateWithHttpInfo) | **POST** /simulate/run-tests/{run_test_id}/chat-execute/ |  |
| [**simulateRunTestsComponentsPartialUpdate**](SimulateApi.md#simulateRunTestsComponentsPartialUpdate) | **PATCH** /simulate/run-tests/{run_test_id}/components/ |  |
| [**simulateRunTestsComponentsPartialUpdateWithHttpInfo**](SimulateApi.md#simulateRunTestsComponentsPartialUpdateWithHttpInfo) | **PATCH** /simulate/run-tests/{run_test_id}/components/ |  |
| [**simulateRunTestsDeleteDelete**](SimulateApi.md#simulateRunTestsDeleteDelete) | **DELETE** /simulate/run-tests/{run_test_id}/delete/ |  |
| [**simulateRunTestsDeleteDeleteWithHttpInfo**](SimulateApi.md#simulateRunTestsDeleteDeleteWithHttpInfo) | **DELETE** /simulate/run-tests/{run_test_id}/delete/ |  |
| [**simulateRunTestsDeleteTestExecutionsCreate**](SimulateApi.md#simulateRunTestsDeleteTestExecutionsCreate) | **POST** /simulate/run-tests/{run_test_id}/delete-test-executions/ |  |
| [**simulateRunTestsDeleteTestExecutionsCreateWithHttpInfo**](SimulateApi.md#simulateRunTestsDeleteTestExecutionsCreateWithHttpInfo) | **POST** /simulate/run-tests/{run_test_id}/delete-test-executions/ |  |
| [**simulateRunTestsEvalConfigsGetStructureList**](SimulateApi.md#simulateRunTestsEvalConfigsGetStructureList) | **GET** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/get-structure/ |  |
| [**simulateRunTestsEvalConfigsGetStructureListWithHttpInfo**](SimulateApi.md#simulateRunTestsEvalConfigsGetStructureListWithHttpInfo) | **GET** /simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/get-structure/ |  |
| [**simulateRunTestsGetIdByNameRead**](SimulateApi.md#simulateRunTestsGetIdByNameRead) | **GET** /simulate/run-tests/get-id-by-name/{run_test_name}/ |  |
| [**simulateRunTestsGetIdByNameReadWithHttpInfo**](SimulateApi.md#simulateRunTestsGetIdByNameReadWithHttpInfo) | **GET** /simulate/run-tests/get-id-by-name/{run_test_name}/ |  |
| [**simulateRunTestsRerunTestExecutionsCreate**](SimulateApi.md#simulateRunTestsRerunTestExecutionsCreate) | **POST** /simulate/run-tests/{run_test_id}/rerun-test-executions/ |  |
| [**simulateRunTestsRerunTestExecutionsCreateWithHttpInfo**](SimulateApi.md#simulateRunTestsRerunTestExecutionsCreateWithHttpInfo) | **POST** /simulate/run-tests/{run_test_id}/rerun-test-executions/ |  |
| [**simulateRunTestsScenariosList**](SimulateApi.md#simulateRunTestsScenariosList) | **GET** /simulate/run-tests/{run_test_id}/scenarios/ |  |
| [**simulateRunTestsScenariosListWithHttpInfo**](SimulateApi.md#simulateRunTestsScenariosListWithHttpInfo) | **GET** /simulate/run-tests/{run_test_id}/scenarios/ |  |
| [**simulateRunTestsSdkCodeList**](SimulateApi.md#simulateRunTestsSdkCodeList) | **GET** /simulate/run-tests/{run_test_id}/sdk-code/ |  |
| [**simulateRunTestsSdkCodeListWithHttpInfo**](SimulateApi.md#simulateRunTestsSdkCodeListWithHttpInfo) | **GET** /simulate/run-tests/{run_test_id}/sdk-code/ |  |
| [**simulateSimulatorAgentsCreateCreate**](SimulateApi.md#simulateSimulatorAgentsCreateCreate) | **POST** /simulate/simulator-agents/create/ |  |
| [**simulateSimulatorAgentsCreateCreateWithHttpInfo**](SimulateApi.md#simulateSimulatorAgentsCreateCreateWithHttpInfo) | **POST** /simulate/simulator-agents/create/ |  |
| [**simulateSimulatorAgentsDeleteDelete**](SimulateApi.md#simulateSimulatorAgentsDeleteDelete) | **DELETE** /simulate/simulator-agents/{agent_id}/delete/ |  |
| [**simulateSimulatorAgentsDeleteDeleteWithHttpInfo**](SimulateApi.md#simulateSimulatorAgentsDeleteDeleteWithHttpInfo) | **DELETE** /simulate/simulator-agents/{agent_id}/delete/ |  |
| [**simulateSimulatorAgentsEditUpdate**](SimulateApi.md#simulateSimulatorAgentsEditUpdate) | **PUT** /simulate/simulator-agents/{agent_id}/edit/ |  |
| [**simulateSimulatorAgentsEditUpdateWithHttpInfo**](SimulateApi.md#simulateSimulatorAgentsEditUpdateWithHttpInfo) | **PUT** /simulate/simulator-agents/{agent_id}/edit/ |  |
| [**simulateSimulatorAgentsList**](SimulateApi.md#simulateSimulatorAgentsList) | **GET** /simulate/simulator-agents/ |  |
| [**simulateSimulatorAgentsListWithHttpInfo**](SimulateApi.md#simulateSimulatorAgentsListWithHttpInfo) | **GET** /simulate/simulator-agents/ |  |
| [**simulateSimulatorAgentsRead**](SimulateApi.md#simulateSimulatorAgentsRead) | **GET** /simulate/simulator-agents/{agent_id}/ |  |
| [**simulateSimulatorAgentsReadWithHttpInfo**](SimulateApi.md#simulateSimulatorAgentsReadWithHttpInfo) | **GET** /simulate/simulator-agents/{agent_id}/ |  |
| [**simulateTestExecutionsChatCallExecutionsBatchCreate**](SimulateApi.md#simulateTestExecutionsChatCallExecutionsBatchCreate) | **POST** /simulate/test-executions/{test_execution_id}/chat/call-executions/batch/ | Create a batch of CallExecution records for chat execution (exactly 10 per API call). |
| [**simulateTestExecutionsChatCallExecutionsBatchCreateWithHttpInfo**](SimulateApi.md#simulateTestExecutionsChatCallExecutionsBatchCreateWithHttpInfo) | **POST** /simulate/test-executions/{test_execution_id}/chat/call-executions/batch/ | Create a batch of CallExecution records for chat execution (exactly 10 per API call). |
| [**simulateTestExecutionsColumnOrderUpdate**](SimulateApi.md#simulateTestExecutionsColumnOrderUpdate) | **PUT** /simulate/test-executions/{test_execution_id}/column-order/ |  |
| [**simulateTestExecutionsColumnOrderUpdateWithHttpInfo**](SimulateApi.md#simulateTestExecutionsColumnOrderUpdateWithHttpInfo) | **PUT** /simulate/test-executions/{test_execution_id}/column-order/ |  |
| [**simulateTestExecutionsDeleteDelete**](SimulateApi.md#simulateTestExecutionsDeleteDelete) | **DELETE** /simulate/test-executions/{test_execution_id}/delete/ |  |
| [**simulateTestExecutionsDeleteDeleteWithHttpInfo**](SimulateApi.md#simulateTestExecutionsDeleteDeleteWithHttpInfo) | **DELETE** /simulate/test-executions/{test_execution_id}/delete/ |  |
| [**simulateTestExecutionsEvalExplanationSummaryList**](SimulateApi.md#simulateTestExecutionsEvalExplanationSummaryList) | **GET** /simulate/test-executions/{test_execution_id}/eval-explanation-summary/ |  |
| [**simulateTestExecutionsEvalExplanationSummaryListWithHttpInfo**](SimulateApi.md#simulateTestExecutionsEvalExplanationSummaryListWithHttpInfo) | **GET** /simulate/test-executions/{test_execution_id}/eval-explanation-summary/ |  |
| [**simulateTestExecutionsEvalExplanationSummaryRefreshCreate**](SimulateApi.md#simulateTestExecutionsEvalExplanationSummaryRefreshCreate) | **POST** /simulate/test-executions/{test_execution_id}/eval-explanation-summary/refresh/ |  |
| [**simulateTestExecutionsEvalExplanationSummaryRefreshCreateWithHttpInfo**](SimulateApi.md#simulateTestExecutionsEvalExplanationSummaryRefreshCreateWithHttpInfo) | **POST** /simulate/test-executions/{test_execution_id}/eval-explanation-summary/refresh/ |  |
| [**simulateTestExecutionsOptimiserAnalysisList**](SimulateApi.md#simulateTestExecutionsOptimiserAnalysisList) | **GET** /simulate/test-executions/{test_execution_id}/optimiser-analysis/ |  |
| [**simulateTestExecutionsOptimiserAnalysisListWithHttpInfo**](SimulateApi.md#simulateTestExecutionsOptimiserAnalysisListWithHttpInfo) | **GET** /simulate/test-executions/{test_execution_id}/optimiser-analysis/ |  |
| [**simulateTestExecutionsOptimiserAnalysisRefreshCreate**](SimulateApi.md#simulateTestExecutionsOptimiserAnalysisRefreshCreate) | **POST** /simulate/test-executions/{test_execution_id}/optimiser-analysis/refresh/ |  |
| [**simulateTestExecutionsOptimiserAnalysisRefreshCreateWithHttpInfo**](SimulateApi.md#simulateTestExecutionsOptimiserAnalysisRefreshCreateWithHttpInfo) | **POST** /simulate/test-executions/{test_execution_id}/optimiser-analysis/refresh/ |  |
| [**simulateTestExecutionsRerunCallsCreate**](SimulateApi.md#simulateTestExecutionsRerunCallsCreate) | **POST** /simulate/test-executions/{test_execution_id}/rerun-calls/ |  |
| [**simulateTestExecutionsRerunCallsCreateWithHttpInfo**](SimulateApi.md#simulateTestExecutionsRerunCallsCreateWithHttpInfo) | **POST** /simulate/test-executions/{test_execution_id}/rerun-calls/ |  |



## simulateAgentDefinitionsDelete

> AgentDefinitionBulkDeleteResponse simulateAgentDefinitionsDelete(agentDefinitionBulkDeleteRequest)



Bulk soft-delete agent definitions.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        AgentDefinitionBulkDeleteRequest agentDefinitionBulkDeleteRequest = new AgentDefinitionBulkDeleteRequest(); // AgentDefinitionBulkDeleteRequest | 
        try {
            AgentDefinitionBulkDeleteResponse result = apiInstance.simulateAgentDefinitionsDelete(agentDefinitionBulkDeleteRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentDefinitionBulkDeleteRequest** | [**AgentDefinitionBulkDeleteRequest**](AgentDefinitionBulkDeleteRequest.md)|  | |

### Return type

[**AgentDefinitionBulkDeleteResponse**](AgentDefinitionBulkDeleteResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsDeleteWithHttpInfo

> ApiResponse<AgentDefinitionBulkDeleteResponse> simulateAgentDefinitionsDelete simulateAgentDefinitionsDeleteWithHttpInfo(agentDefinitionBulkDeleteRequest)



Bulk soft-delete agent definitions.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        AgentDefinitionBulkDeleteRequest agentDefinitionBulkDeleteRequest = new AgentDefinitionBulkDeleteRequest(); // AgentDefinitionBulkDeleteRequest | 
        try {
            ApiResponse<AgentDefinitionBulkDeleteResponse> response = apiInstance.simulateAgentDefinitionsDeleteWithHttpInfo(agentDefinitionBulkDeleteRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentDefinitionBulkDeleteRequest** | [**AgentDefinitionBulkDeleteRequest**](AgentDefinitionBulkDeleteRequest.md)|  | |

### Return type

ApiResponse<[**AgentDefinitionBulkDeleteResponse**](AgentDefinitionBulkDeleteResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateAgentDefinitionsVersionsActivateCreate

> AgentVersionActivateResponse simulateAgentDefinitionsVersionsActivateCreate(agentId, versionId, body)



Activate a specific agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        Object body = null; // Object | 
        try {
            AgentVersionActivateResponse result = apiInstance.simulateAgentDefinitionsVersionsActivateCreate(agentId, versionId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsActivateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**AgentVersionActivateResponse**](AgentVersionActivateResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsVersionsActivateCreateWithHttpInfo

> ApiResponse<AgentVersionActivateResponse> simulateAgentDefinitionsVersionsActivateCreate simulateAgentDefinitionsVersionsActivateCreateWithHttpInfo(agentId, versionId, body)



Activate a specific agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<AgentVersionActivateResponse> response = apiInstance.simulateAgentDefinitionsVersionsActivateCreateWithHttpInfo(agentId, versionId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsActivateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**AgentVersionActivateResponse**](AgentVersionActivateResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateAgentDefinitionsVersionsCallExecutionsList

> List<CallExecution> simulateAgentDefinitionsVersionsCallExecutionsList(agentId, versionId)



Get the call executions of an agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        try {
            List<CallExecution> result = apiInstance.simulateAgentDefinitionsVersionsCallExecutionsList(agentId, versionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsCallExecutionsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |

### Return type

[**List&lt;CallExecution&gt;**](CallExecution.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsVersionsCallExecutionsListWithHttpInfo

> ApiResponse<List<CallExecution>> simulateAgentDefinitionsVersionsCallExecutionsList simulateAgentDefinitionsVersionsCallExecutionsListWithHttpInfo(agentId, versionId)



Get the call executions of an agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        try {
            ApiResponse<List<CallExecution>> response = apiInstance.simulateAgentDefinitionsVersionsCallExecutionsListWithHttpInfo(agentId, versionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsCallExecutionsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |

### Return type

ApiResponse<[**List&lt;CallExecution&gt;**](CallExecution.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateAgentDefinitionsVersionsCreateCreate

> AgentVersionCreateResponse simulateAgentDefinitionsVersionsCreateCreate(agentId, agentVersionCreateRequest)



Create a new version of an agent definition.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        AgentVersionCreateRequest agentVersionCreateRequest = new AgentVersionCreateRequest(); // AgentVersionCreateRequest | 
        try {
            AgentVersionCreateResponse result = apiInstance.simulateAgentDefinitionsVersionsCreateCreate(agentId, agentVersionCreateRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsCreateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **agentVersionCreateRequest** | [**AgentVersionCreateRequest**](AgentVersionCreateRequest.md)|  | |

### Return type

[**AgentVersionCreateResponse**](AgentVersionCreateResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsVersionsCreateCreateWithHttpInfo

> ApiResponse<AgentVersionCreateResponse> simulateAgentDefinitionsVersionsCreateCreate simulateAgentDefinitionsVersionsCreateCreateWithHttpInfo(agentId, agentVersionCreateRequest)



Create a new version of an agent definition.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        AgentVersionCreateRequest agentVersionCreateRequest = new AgentVersionCreateRequest(); // AgentVersionCreateRequest | 
        try {
            ApiResponse<AgentVersionCreateResponse> response = apiInstance.simulateAgentDefinitionsVersionsCreateCreateWithHttpInfo(agentId, agentVersionCreateRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsCreateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **agentVersionCreateRequest** | [**AgentVersionCreateRequest**](AgentVersionCreateRequest.md)|  | |

### Return type

ApiResponse<[**AgentVersionCreateResponse**](AgentVersionCreateResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateAgentDefinitionsVersionsDeleteDelete

> AgentVersionDeleteResponse simulateAgentDefinitionsVersionsDeleteDelete(agentId, versionId)



Soft delete an agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        try {
            AgentVersionDeleteResponse result = apiInstance.simulateAgentDefinitionsVersionsDeleteDelete(agentId, versionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |

### Return type

[**AgentVersionDeleteResponse**](AgentVersionDeleteResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsVersionsDeleteDeleteWithHttpInfo

> ApiResponse<AgentVersionDeleteResponse> simulateAgentDefinitionsVersionsDeleteDelete simulateAgentDefinitionsVersionsDeleteDeleteWithHttpInfo(agentId, versionId)



Soft delete an agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        try {
            ApiResponse<AgentVersionDeleteResponse> response = apiInstance.simulateAgentDefinitionsVersionsDeleteDeleteWithHttpInfo(agentId, versionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |

### Return type

ApiResponse<[**AgentVersionDeleteResponse**](AgentVersionDeleteResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateAgentDefinitionsVersionsEvalSummaryList

> EvalSummaryResponse simulateAgentDefinitionsVersionsEvalSummaryList(agentId, versionId)



Get the eval summary of an agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        try {
            EvalSummaryResponse result = apiInstance.simulateAgentDefinitionsVersionsEvalSummaryList(agentId, versionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsEvalSummaryList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |

### Return type

[**EvalSummaryResponse**](EvalSummaryResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsVersionsEvalSummaryListWithHttpInfo

> ApiResponse<EvalSummaryResponse> simulateAgentDefinitionsVersionsEvalSummaryList simulateAgentDefinitionsVersionsEvalSummaryListWithHttpInfo(agentId, versionId)



Get the eval summary of an agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        try {
            ApiResponse<EvalSummaryResponse> response = apiInstance.simulateAgentDefinitionsVersionsEvalSummaryListWithHttpInfo(agentId, versionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsEvalSummaryList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |

### Return type

ApiResponse<[**EvalSummaryResponse**](EvalSummaryResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateAgentDefinitionsVersionsList

> List<AgentVersionListResponse> simulateAgentDefinitionsVersionsList(agentId)



Get all versions of a specific agent definition.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            List<AgentVersionListResponse> result = apiInstance.simulateAgentDefinitionsVersionsList(agentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |

### Return type

[**List&lt;AgentVersionListResponse&gt;**](AgentVersionListResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsVersionsListWithHttpInfo

> ApiResponse<List<AgentVersionListResponse>> simulateAgentDefinitionsVersionsList simulateAgentDefinitionsVersionsListWithHttpInfo(agentId)



Get all versions of a specific agent definition.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            ApiResponse<List<AgentVersionListResponse>> response = apiInstance.simulateAgentDefinitionsVersionsListWithHttpInfo(agentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |

### Return type

ApiResponse<[**List&lt;AgentVersionListResponse&gt;**](AgentVersionListResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateAgentDefinitionsVersionsRead

> AgentVersionResponse simulateAgentDefinitionsVersionsRead(agentId, versionId)



Get details of a specific agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        try {
            AgentVersionResponse result = apiInstance.simulateAgentDefinitionsVersionsRead(agentId, versionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |

### Return type

[**AgentVersionResponse**](AgentVersionResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsVersionsReadWithHttpInfo

> ApiResponse<AgentVersionResponse> simulateAgentDefinitionsVersionsRead simulateAgentDefinitionsVersionsReadWithHttpInfo(agentId, versionId)



Get details of a specific agent version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        try {
            ApiResponse<AgentVersionResponse> response = apiInstance.simulateAgentDefinitionsVersionsReadWithHttpInfo(agentId, versionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |

### Return type

ApiResponse<[**AgentVersionResponse**](AgentVersionResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateAgentDefinitionsVersionsRestoreCreate

> AgentVersionRestoreResponse simulateAgentDefinitionsVersionsRestoreCreate(agentId, versionId, body)



Restore agent definition from a specific version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        Object body = null; // Object | 
        try {
            AgentVersionRestoreResponse result = apiInstance.simulateAgentDefinitionsVersionsRestoreCreate(agentId, versionId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsRestoreCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**AgentVersionRestoreResponse**](AgentVersionRestoreResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateAgentDefinitionsVersionsRestoreCreateWithHttpInfo

> ApiResponse<AgentVersionRestoreResponse> simulateAgentDefinitionsVersionsRestoreCreate simulateAgentDefinitionsVersionsRestoreCreateWithHttpInfo(agentId, versionId, body)



Restore agent definition from a specific version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        String versionId = "versionId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<AgentVersionRestoreResponse> response = apiInstance.simulateAgentDefinitionsVersionsRestoreCreateWithHttpInfo(agentId, versionId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateAgentDefinitionsVersionsRestoreCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **versionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**AgentVersionRestoreResponse**](AgentVersionRestoreResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateApiCallExecutionsList

> List<CallExecution> simulateApiCallExecutionsList(search, status, testExecutionId, page, limit)



Get paginated list of call executions for the user&#39;s organization Query Parameters: - search: search string to filter call executions by phone number or scenario name - status: filter by call status - test_execution_id: filter by specific test execution - limit: number of items per page (default: 10) - page: page number (default: 1)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String search = ""; // String | 
        String status = ""; // String | 
        UUID testExecutionId = UUID.randomUUID(); // UUID | 
        Integer page = 1; // Integer | 
        Integer limit = 56; // Integer | 
        try {
            List<CallExecution> result = apiInstance.simulateApiCallExecutionsList(search, status, testExecutionId, page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiCallExecutionsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **search** | **String**|  | [optional] [default to ] |
| **status** | **String**|  | [optional] [default to ] |
| **testExecutionId** | **UUID**|  | [optional] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] |

### Return type

[**List&lt;CallExecution&gt;**](CallExecution.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateApiCallExecutionsListWithHttpInfo

> ApiResponse<List<CallExecution>> simulateApiCallExecutionsList simulateApiCallExecutionsListWithHttpInfo(search, status, testExecutionId, page, limit)



Get paginated list of call executions for the user&#39;s organization Query Parameters: - search: search string to filter call executions by phone number or scenario name - status: filter by call status - test_execution_id: filter by specific test execution - limit: number of items per page (default: 10) - page: page number (default: 1)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String search = ""; // String | 
        String status = ""; // String | 
        UUID testExecutionId = UUID.randomUUID(); // UUID | 
        Integer page = 1; // Integer | 
        Integer limit = 56; // Integer | 
        try {
            ApiResponse<List<CallExecution>> response = apiInstance.simulateApiCallExecutionsListWithHttpInfo(search, status, testExecutionId, page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiCallExecutionsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **search** | **String**|  | [optional] [default to ] |
| **status** | **String**|  | [optional] [default to ] |
| **testExecutionId** | **UUID**|  | [optional] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] |

### Return type

ApiResponse<[**List&lt;CallExecution&gt;**](CallExecution.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateApiPersonasDuplicate

> PersonaDuplicateResponse simulateApiPersonasDuplicate(id, personaDuplicateRequest)



Duplicate a persona (creates a workspace-level copy)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String id = "id_example"; // String | 
        PersonaDuplicateRequest personaDuplicateRequest = new PersonaDuplicateRequest(); // PersonaDuplicateRequest | 
        try {
            PersonaDuplicateResponse result = apiInstance.simulateApiPersonasDuplicate(id, personaDuplicateRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasDuplicate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **id** | **String**|  | |
| **personaDuplicateRequest** | [**PersonaDuplicateRequest**](PersonaDuplicateRequest.md)|  | |

### Return type

[**PersonaDuplicateResponse**](PersonaDuplicateResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateApiPersonasDuplicateWithHttpInfo

> ApiResponse<PersonaDuplicateResponse> simulateApiPersonasDuplicate simulateApiPersonasDuplicateWithHttpInfo(id, personaDuplicateRequest)



Duplicate a persona (creates a workspace-level copy)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String id = "id_example"; // String | 
        PersonaDuplicateRequest personaDuplicateRequest = new PersonaDuplicateRequest(); // PersonaDuplicateRequest | 
        try {
            ApiResponse<PersonaDuplicateResponse> response = apiInstance.simulateApiPersonasDuplicateWithHttpInfo(id, personaDuplicateRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasDuplicate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **id** | **String**|  | |
| **personaDuplicateRequest** | [**PersonaDuplicateRequest**](PersonaDuplicateRequest.md)|  | |

### Return type

ApiResponse<[**PersonaDuplicateResponse**](PersonaDuplicateResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateApiPersonasDuplicateCreate

> PersonaDuplicateResponse simulateApiPersonasDuplicateCreate(personaId, personaDuplicateRequest)



Duplicate a persona by ID

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String personaId = "personaId_example"; // String | 
        PersonaDuplicateRequest personaDuplicateRequest = new PersonaDuplicateRequest(); // PersonaDuplicateRequest | 
        try {
            PersonaDuplicateResponse result = apiInstance.simulateApiPersonasDuplicateCreate(personaId, personaDuplicateRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasDuplicateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **personaId** | **String**|  | |
| **personaDuplicateRequest** | [**PersonaDuplicateRequest**](PersonaDuplicateRequest.md)|  | |

### Return type

[**PersonaDuplicateResponse**](PersonaDuplicateResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **0** | Default error response |  -  |

## simulateApiPersonasDuplicateCreateWithHttpInfo

> ApiResponse<PersonaDuplicateResponse> simulateApiPersonasDuplicateCreate simulateApiPersonasDuplicateCreateWithHttpInfo(personaId, personaDuplicateRequest)



Duplicate a persona by ID

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String personaId = "personaId_example"; // String | 
        PersonaDuplicateRequest personaDuplicateRequest = new PersonaDuplicateRequest(); // PersonaDuplicateRequest | 
        try {
            ApiResponse<PersonaDuplicateResponse> response = apiInstance.simulateApiPersonasDuplicateCreateWithHttpInfo(personaId, personaDuplicateRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasDuplicateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **personaId** | **String**|  | |
| **personaDuplicateRequest** | [**PersonaDuplicateRequest**](PersonaDuplicateRequest.md)|  | |

### Return type

ApiResponse<[**PersonaDuplicateResponse**](PersonaDuplicateResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **0** | Default error response |  -  |


## simulateApiPersonasFieldOptions

> SimulateApiPersonasFieldOptions200Response simulateApiPersonasFieldOptions(page, limit)



Get field options/choices for persona creation

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            SimulateApiPersonasFieldOptions200Response result = apiInstance.simulateApiPersonasFieldOptions(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasFieldOptions");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

[**SimulateApiPersonasFieldOptions200Response**](SimulateApiPersonasFieldOptions200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateApiPersonasFieldOptionsWithHttpInfo

> ApiResponse<SimulateApiPersonasFieldOptions200Response> simulateApiPersonasFieldOptions simulateApiPersonasFieldOptionsWithHttpInfo(page, limit)



Get field options/choices for persona creation

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<SimulateApiPersonasFieldOptions200Response> response = apiInstance.simulateApiPersonasFieldOptionsWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasFieldOptions");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

ApiResponse<[**SimulateApiPersonasFieldOptions200Response**](SimulateApiPersonasFieldOptions200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateApiPersonasSystemPersonas

> SimulateApiPersonasSystemPersonas200Response simulateApiPersonasSystemPersonas(page, limit)



Get only system-level personas

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            SimulateApiPersonasSystemPersonas200Response result = apiInstance.simulateApiPersonasSystemPersonas(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasSystemPersonas");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

[**SimulateApiPersonasSystemPersonas200Response**](SimulateApiPersonasSystemPersonas200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateApiPersonasSystemPersonasWithHttpInfo

> ApiResponse<SimulateApiPersonasSystemPersonas200Response> simulateApiPersonasSystemPersonas simulateApiPersonasSystemPersonasWithHttpInfo(page, limit)



Get only system-level personas

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<SimulateApiPersonasSystemPersonas200Response> response = apiInstance.simulateApiPersonasSystemPersonasWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasSystemPersonas");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

ApiResponse<[**SimulateApiPersonasSystemPersonas200Response**](SimulateApiPersonasSystemPersonas200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateApiPersonasUpdate

> Persona simulateApiPersonasUpdate(id, persona)



Update a persona (workspace-level only)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String id = "id_example"; // String | 
        Persona persona = new Persona(); // Persona | 
        try {
            Persona result = apiInstance.simulateApiPersonasUpdate(id, persona);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **id** | **String**|  | |
| **persona** | [**Persona**](Persona.md)|  | |

### Return type

[**Persona**](Persona.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateApiPersonasUpdateWithHttpInfo

> ApiResponse<Persona> simulateApiPersonasUpdate simulateApiPersonasUpdateWithHttpInfo(id, persona)



Update a persona (workspace-level only)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String id = "id_example"; // String | 
        Persona persona = new Persona(); // Persona | 
        try {
            ApiResponse<Persona> response = apiInstance.simulateApiPersonasUpdateWithHttpInfo(id, persona);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **id** | **String**|  | |
| **persona** | [**Persona**](Persona.md)|  | |

### Return type

ApiResponse<[**Persona**](Persona.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateApiPersonasWorkspacePersonas

> SimulateApiPersonasSystemPersonas200Response simulateApiPersonasWorkspacePersonas(page, limit)



Get only workspace-level personas

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            SimulateApiPersonasSystemPersonas200Response result = apiInstance.simulateApiPersonasWorkspacePersonas(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasWorkspacePersonas");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

[**SimulateApiPersonasSystemPersonas200Response**](SimulateApiPersonasSystemPersonas200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateApiPersonasWorkspacePersonasWithHttpInfo

> ApiResponse<SimulateApiPersonasSystemPersonas200Response> simulateApiPersonasWorkspacePersonas simulateApiPersonasWorkspacePersonasWithHttpInfo(page, limit)



Get only workspace-level personas

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<SimulateApiPersonasSystemPersonas200Response> response = apiInstance.simulateApiPersonasWorkspacePersonasWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiPersonasWorkspacePersonas");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |

### Return type

ApiResponse<[**SimulateApiPersonasSystemPersonas200Response**](SimulateApiPersonasSystemPersonas200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateApiRunTestsList

> List<RunTestResponse> simulateApiRunTestsList(search, simulationType, promptTemplateId, page, limit)



Get paginated list of run tests for the user&#39;s organization Query Parameters: - search: search string to filter run tests by name - limit: number of items per page (default: 10) - page: page number (default: 1)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String search = ""; // String | 
        String simulationType = "agent_definition"; // String | 
        UUID promptTemplateId = UUID.randomUUID(); // UUID | 
        Integer page = 1; // Integer | 
        Integer limit = 56; // Integer | 
        try {
            List<RunTestResponse> result = apiInstance.simulateApiRunTestsList(search, simulationType, promptTemplateId, page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiRunTestsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **search** | **String**|  | [optional] [default to ] |
| **simulationType** | **String**|  | [optional] [enum: agent_definition, prompt] |
| **promptTemplateId** | **UUID**|  | [optional] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] |

### Return type

[**List&lt;RunTestResponse&gt;**](RunTestResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateApiRunTestsListWithHttpInfo

> ApiResponse<List<RunTestResponse>> simulateApiRunTestsList simulateApiRunTestsListWithHttpInfo(search, simulationType, promptTemplateId, page, limit)



Get paginated list of run tests for the user&#39;s organization Query Parameters: - search: search string to filter run tests by name - limit: number of items per page (default: 10) - page: page number (default: 1)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String search = ""; // String | 
        String simulationType = "agent_definition"; // String | 
        UUID promptTemplateId = UUID.randomUUID(); // UUID | 
        Integer page = 1; // Integer | 
        Integer limit = 56; // Integer | 
        try {
            ApiResponse<List<RunTestResponse>> response = apiInstance.simulateApiRunTestsListWithHttpInfo(search, simulationType, promptTemplateId, page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateApiRunTestsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **search** | **String**|  | [optional] [default to ] |
| **simulationType** | **String**|  | [optional] [enum: agent_definition, prompt] |
| **promptTemplateId** | **UUID**|  | [optional] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] |

### Return type

ApiResponse<[**List&lt;RunTestResponse&gt;**](RunTestResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsBranchAnalysisCreate

> CallBranchDeviationCreateResponse simulateCallExecutionsBranchAnalysisCreate(callExecutionId, body)



Create deviation nodes and edges for a call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            CallBranchDeviationCreateResponse result = apiInstance.simulateCallExecutionsBranchAnalysisCreate(callExecutionId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsBranchAnalysisCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**CallBranchDeviationCreateResponse**](CallBranchDeviationCreateResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsBranchAnalysisCreateWithHttpInfo

> ApiResponse<CallBranchDeviationCreateResponse> simulateCallExecutionsBranchAnalysisCreate simulateCallExecutionsBranchAnalysisCreateWithHttpInfo(callExecutionId, body)



Create deviation nodes and edges for a call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<CallBranchDeviationCreateResponse> response = apiInstance.simulateCallExecutionsBranchAnalysisCreateWithHttpInfo(callExecutionId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsBranchAnalysisCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**CallBranchDeviationCreateResponse**](CallBranchDeviationCreateResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsBranchAnalysisList

> CallBranchAnalysisResponse simulateCallExecutionsBranchAnalysisList(callExecutionId)



Analyze a call execution against graph branches and identify deviations

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            CallBranchAnalysisResponse result = apiInstance.simulateCallExecutionsBranchAnalysisList(callExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsBranchAnalysisList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

[**CallBranchAnalysisResponse**](CallBranchAnalysisResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsBranchAnalysisListWithHttpInfo

> ApiResponse<CallBranchAnalysisResponse> simulateCallExecutionsBranchAnalysisList simulateCallExecutionsBranchAnalysisListWithHttpInfo(callExecutionId)



Analyze a call execution against graph branches and identify deviations

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            ApiResponse<CallBranchAnalysisResponse> response = apiInstance.simulateCallExecutionsBranchAnalysisListWithHttpInfo(callExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsBranchAnalysisList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

ApiResponse<[**CallBranchAnalysisResponse**](CallBranchAnalysisResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsChatSendMessageCreate

> ChatSendMessageResponse simulateCallExecutionsChatSendMessageCreate(callExecutionId, sendChatRequest)



Send a message to a chat execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        SendChatRequest sendChatRequest = new SendChatRequest(); // SendChatRequest | 
        try {
            ChatSendMessageResponse result = apiInstance.simulateCallExecutionsChatSendMessageCreate(callExecutionId, sendChatRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsChatSendMessageCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |
| **sendChatRequest** | [**SendChatRequest**](SendChatRequest.md)|  | |

### Return type

[**ChatSendMessageResponse**](ChatSendMessageResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsChatSendMessageCreateWithHttpInfo

> ApiResponse<ChatSendMessageResponse> simulateCallExecutionsChatSendMessageCreate simulateCallExecutionsChatSendMessageCreateWithHttpInfo(callExecutionId, sendChatRequest)



Send a message to a chat execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        SendChatRequest sendChatRequest = new SendChatRequest(); // SendChatRequest | 
        try {
            ApiResponse<ChatSendMessageResponse> response = apiInstance.simulateCallExecutionsChatSendMessageCreateWithHttpInfo(callExecutionId, sendChatRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsChatSendMessageCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |
| **sendChatRequest** | [**SendChatRequest**](SendChatRequest.md)|  | |

### Return type

ApiResponse<[**ChatSendMessageResponse**](ChatSendMessageResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsDeleteDelete

> CallExecutionDeleteResponse simulateCallExecutionsDeleteDelete(callExecutionId)



Delete a specific call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            CallExecutionDeleteResponse result = apiInstance.simulateCallExecutionsDeleteDelete(callExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

[**CallExecutionDeleteResponse**](CallExecutionDeleteResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsDeleteDeleteWithHttpInfo

> ApiResponse<CallExecutionDeleteResponse> simulateCallExecutionsDeleteDelete simulateCallExecutionsDeleteDeleteWithHttpInfo(callExecutionId)



Delete a specific call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            ApiResponse<CallExecutionDeleteResponse> response = apiInstance.simulateCallExecutionsDeleteDeleteWithHttpInfo(callExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

ApiResponse<[**CallExecutionDeleteResponse**](CallExecutionDeleteResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsErrorLocalizerTasksList

> CallExecutionErrorLocalizerTasksResponse simulateCallExecutionsErrorLocalizerTasksList(callExecutionId)



Get error localizer tasks for a specific call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            CallExecutionErrorLocalizerTasksResponse result = apiInstance.simulateCallExecutionsErrorLocalizerTasksList(callExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsErrorLocalizerTasksList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

[**CallExecutionErrorLocalizerTasksResponse**](CallExecutionErrorLocalizerTasksResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsErrorLocalizerTasksListWithHttpInfo

> ApiResponse<CallExecutionErrorLocalizerTasksResponse> simulateCallExecutionsErrorLocalizerTasksList simulateCallExecutionsErrorLocalizerTasksListWithHttpInfo(callExecutionId)



Get error localizer tasks for a specific call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            ApiResponse<CallExecutionErrorLocalizerTasksResponse> response = apiInstance.simulateCallExecutionsErrorLocalizerTasksListWithHttpInfo(callExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsErrorLocalizerTasksList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

ApiResponse<[**CallExecutionErrorLocalizerTasksResponse**](CallExecutionErrorLocalizerTasksResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsLogsList

> CallExecutionLogsResponse simulateCallExecutionsLogsList(callExecutionId)



Paginated API to retrieve stored log entries for a call execution.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            CallExecutionLogsResponse result = apiInstance.simulateCallExecutionsLogsList(callExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsLogsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

[**CallExecutionLogsResponse**](CallExecutionLogsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsLogsListWithHttpInfo

> ApiResponse<CallExecutionLogsResponse> simulateCallExecutionsLogsList simulateCallExecutionsLogsListWithHttpInfo(callExecutionId)



Paginated API to retrieve stored log entries for a call execution.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            ApiResponse<CallExecutionLogsResponse> response = apiInstance.simulateCallExecutionsLogsListWithHttpInfo(callExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsLogsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

ApiResponse<[**CallExecutionLogsResponse**](CallExecutionLogsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsPartialUpdate

> CallExecution simulateCallExecutionsPartialUpdate(callExecutionId, callExecutionStatusUpdate)



Update the status of a specific call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        CallExecutionStatusUpdate callExecutionStatusUpdate = new CallExecutionStatusUpdate(); // CallExecutionStatusUpdate | 
        try {
            CallExecution result = apiInstance.simulateCallExecutionsPartialUpdate(callExecutionId, callExecutionStatusUpdate);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsPartialUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |
| **callExecutionStatusUpdate** | [**CallExecutionStatusUpdate**](CallExecutionStatusUpdate.md)|  | |

### Return type

[**CallExecution**](CallExecution.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsPartialUpdateWithHttpInfo

> ApiResponse<CallExecution> simulateCallExecutionsPartialUpdate simulateCallExecutionsPartialUpdateWithHttpInfo(callExecutionId, callExecutionStatusUpdate)



Update the status of a specific call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        CallExecutionStatusUpdate callExecutionStatusUpdate = new CallExecutionStatusUpdate(); // CallExecutionStatusUpdate | 
        try {
            ApiResponse<CallExecution> response = apiInstance.simulateCallExecutionsPartialUpdateWithHttpInfo(callExecutionId, callExecutionStatusUpdate);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsPartialUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |
| **callExecutionStatusUpdate** | [**CallExecutionStatusUpdate**](CallExecutionStatusUpdate.md)|  | |

### Return type

ApiResponse<[**CallExecution**](CallExecution.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsRead

> CallExecutionDetail simulateCallExecutionsRead(callExecutionId)



Get a specific call execution with all its details

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            CallExecutionDetail result = apiInstance.simulateCallExecutionsRead(callExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

[**CallExecutionDetail**](CallExecutionDetail.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsReadWithHttpInfo

> ApiResponse<CallExecutionDetail> simulateCallExecutionsRead simulateCallExecutionsReadWithHttpInfo(callExecutionId)



Get a specific call execution with all its details

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            ApiResponse<CallExecutionDetail> response = apiInstance.simulateCallExecutionsReadWithHttpInfo(callExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

ApiResponse<[**CallExecutionDetail**](CallExecutionDetail.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsSessionComparisonList

> SessionComparisonResponse simulateCallExecutionsSessionComparisonList(callExecutionId)



API View to compare session chat simulations

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            SessionComparisonResponse result = apiInstance.simulateCallExecutionsSessionComparisonList(callExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsSessionComparisonList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

[**SessionComparisonResponse**](SessionComparisonResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsSessionComparisonListWithHttpInfo

> ApiResponse<SessionComparisonResponse> simulateCallExecutionsSessionComparisonList simulateCallExecutionsSessionComparisonListWithHttpInfo(callExecutionId)



API View to compare session chat simulations

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            ApiResponse<SessionComparisonResponse> response = apiInstance.simulateCallExecutionsSessionComparisonListWithHttpInfo(callExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsSessionComparisonList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

ApiResponse<[**SessionComparisonResponse**](SessionComparisonResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateCallExecutionsTranscriptsList

> CallTranscriptResponse simulateCallExecutionsTranscriptsList(callExecutionId)



Get transcripts for a specific call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            CallTranscriptResponse result = apiInstance.simulateCallExecutionsTranscriptsList(callExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsTranscriptsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

[**CallTranscriptResponse**](CallTranscriptResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateCallExecutionsTranscriptsListWithHttpInfo

> ApiResponse<CallTranscriptResponse> simulateCallExecutionsTranscriptsList simulateCallExecutionsTranscriptsListWithHttpInfo(callExecutionId)



Get transcripts for a specific call execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String callExecutionId = "callExecutionId_example"; // String | 
        try {
            ApiResponse<CallTranscriptResponse> response = apiInstance.simulateCallExecutionsTranscriptsListWithHttpInfo(callExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateCallExecutionsTranscriptsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **callExecutionId** | **String**|  | |

### Return type

ApiResponse<[**CallTranscriptResponse**](CallTranscriptResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateExportRead

> File simulateExportRead(itemId, type, search, status)



Export data as CSV based on type parameter Query Parameters: - type: &#39;runtest&#39; or &#39;testexecution&#39; (required) - search: search string to filter call executions by phone number or scenario name - status: filter by call execution status

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String itemId = "itemId_example"; // String | 
        String type = "runtest"; // String | Export source type.
        String search = "search_example"; // String | Optional call-execution search term.
        String status = "status_example"; // String | Optional call-execution status filter.
        try {
            File result = apiInstance.simulateExportRead(itemId, type, search, status);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateExportRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **itemId** | **String**|  | |
| **type** | **String**| Export source type. | [enum: runtest, testexecution] |
| **search** | **String**| Optional call-execution search term. | [optional] |
| **status** | **String**| Optional call-execution status filter. | [optional] |

### Return type

[**File**](File.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | CSV export |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateExportReadWithHttpInfo

> ApiResponse<File> simulateExportRead simulateExportReadWithHttpInfo(itemId, type, search, status)



Export data as CSV based on type parameter Query Parameters: - type: &#39;runtest&#39; or &#39;testexecution&#39; (required) - search: search string to filter call executions by phone number or scenario name - status: filter by call execution status

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String itemId = "itemId_example"; // String | 
        String type = "runtest"; // String | Export source type.
        String search = "search_example"; // String | Optional call-execution search term.
        String status = "status_example"; // String | Optional call-execution status filter.
        try {
            ApiResponse<File> response = apiInstance.simulateExportReadWithHttpInfo(itemId, type, search, status);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateExportRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **itemId** | **String**|  | |
| **type** | **String**| Export source type. | [enum: runtest, testexecution] |
| **search** | **String**| Optional call-execution search term. | [optional] |
| **status** | **String**| Optional call-execution status filter. | [optional] |

### Return type

ApiResponse<[**File**](File.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | CSV export |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulatePromptSimulationsScenariosList

> PromptSimulationScenariosResponse simulatePromptSimulationsScenariosList()

Get list of scenarios available for prompt simulations.

Query Parameters: - limit: number of items per page (default: 20) - page: page number (default: 1) - search: search string to filter scenarios by name

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        try {
            PromptSimulationScenariosResponse result = apiInstance.simulatePromptSimulationsScenariosList();
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptSimulationsScenariosList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**PromptSimulationScenariosResponse**](PromptSimulationScenariosResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulatePromptSimulationsScenariosListWithHttpInfo

> ApiResponse<PromptSimulationScenariosResponse> simulatePromptSimulationsScenariosList simulatePromptSimulationsScenariosListWithHttpInfo()

Get list of scenarios available for prompt simulations.

Query Parameters: - limit: number of items per page (default: 20) - page: page number (default: 1) - search: search string to filter scenarios by name

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        try {
            ApiResponse<PromptSimulationScenariosResponse> response = apiInstance.simulatePromptSimulationsScenariosListWithHttpInfo();
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptSimulationsScenariosList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type

ApiResponse<[**PromptSimulationScenariosResponse**](PromptSimulationScenariosResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulatePromptTemplatesSimulationsCreate

> PromptSimulationRunResponse simulatePromptTemplatesSimulationsCreate(promptTemplateId, createPromptSimulationRequest)

Create a new prompt-based simulation run.

Request Body: - name: Name of the simulation run - description: Optional description - prompt_version_id: The prompt version to use - scenario_ids: List of scenario IDs to run - dataset_row_ids: Optional list of specific row IDs - evaluations_config: Optional evaluation configurations - enable_tool_evaluation: Optional boolean to enable tool evaluation

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        CreatePromptSimulationRequest createPromptSimulationRequest = new CreatePromptSimulationRequest(); // CreatePromptSimulationRequest | 
        try {
            PromptSimulationRunResponse result = apiInstance.simulatePromptTemplatesSimulationsCreate(promptTemplateId, createPromptSimulationRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **createPromptSimulationRequest** | [**CreatePromptSimulationRequest**](CreatePromptSimulationRequest.md)|  | |

### Return type

[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulatePromptTemplatesSimulationsCreateWithHttpInfo

> ApiResponse<PromptSimulationRunResponse> simulatePromptTemplatesSimulationsCreate simulatePromptTemplatesSimulationsCreateWithHttpInfo(promptTemplateId, createPromptSimulationRequest)

Create a new prompt-based simulation run.

Request Body: - name: Name of the simulation run - description: Optional description - prompt_version_id: The prompt version to use - scenario_ids: List of scenario IDs to run - dataset_row_ids: Optional list of specific row IDs - evaluations_config: Optional evaluation configurations - enable_tool_evaluation: Optional boolean to enable tool evaluation

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        CreatePromptSimulationRequest createPromptSimulationRequest = new CreatePromptSimulationRequest(); // CreatePromptSimulationRequest | 
        try {
            ApiResponse<PromptSimulationRunResponse> response = apiInstance.simulatePromptTemplatesSimulationsCreateWithHttpInfo(promptTemplateId, createPromptSimulationRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **createPromptSimulationRequest** | [**CreatePromptSimulationRequest**](CreatePromptSimulationRequest.md)|  | |

### Return type

ApiResponse<[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulatePromptTemplatesSimulationsDelete

> void simulatePromptTemplatesSimulationsDelete(promptTemplateId, runTestId)



Soft delete a prompt simulation run.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        String runTestId = "runTestId_example"; // String | 
        try {
            apiInstance.simulatePromptTemplatesSimulationsDelete(promptTemplateId, runTestId);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **runTestId** | **String**|  | |

### Return type


null (empty response body)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulatePromptTemplatesSimulationsDeleteWithHttpInfo

> ApiResponse<Void> simulatePromptTemplatesSimulationsDelete simulatePromptTemplatesSimulationsDeleteWithHttpInfo(promptTemplateId, runTestId)



Soft delete a prompt simulation run.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        String runTestId = "runTestId_example"; // String | 
        try {
            ApiResponse<Void> response = apiInstance.simulatePromptTemplatesSimulationsDeleteWithHttpInfo(promptTemplateId, runTestId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **runTestId** | **String**|  | |

### Return type


ApiResponse<Void>

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulatePromptTemplatesSimulationsExecuteCreate

> ExecutePromptSimulationResponse simulatePromptTemplatesSimulationsExecuteCreate(promptTemplateId, runTestId, executePromptSimulationRequest)

Execute a prompt-based simulation run.

Request Body (optional): - scenario_ids: List of specific scenario IDs to run (default: all scenarios) - select_all: If true, run all scenarios except ones in scenario_ids

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        String runTestId = "runTestId_example"; // String | 
        ExecutePromptSimulationRequest executePromptSimulationRequest = new ExecutePromptSimulationRequest(); // ExecutePromptSimulationRequest | 
        try {
            ExecutePromptSimulationResponse result = apiInstance.simulatePromptTemplatesSimulationsExecuteCreate(promptTemplateId, runTestId, executePromptSimulationRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsExecuteCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **runTestId** | **String**|  | |
| **executePromptSimulationRequest** | [**ExecutePromptSimulationRequest**](ExecutePromptSimulationRequest.md)|  | |

### Return type

[**ExecutePromptSimulationResponse**](ExecutePromptSimulationResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulatePromptTemplatesSimulationsExecuteCreateWithHttpInfo

> ApiResponse<ExecutePromptSimulationResponse> simulatePromptTemplatesSimulationsExecuteCreate simulatePromptTemplatesSimulationsExecuteCreateWithHttpInfo(promptTemplateId, runTestId, executePromptSimulationRequest)

Execute a prompt-based simulation run.

Request Body (optional): - scenario_ids: List of specific scenario IDs to run (default: all scenarios) - select_all: If true, run all scenarios except ones in scenario_ids

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        String runTestId = "runTestId_example"; // String | 
        ExecutePromptSimulationRequest executePromptSimulationRequest = new ExecutePromptSimulationRequest(); // ExecutePromptSimulationRequest | 
        try {
            ApiResponse<ExecutePromptSimulationResponse> response = apiInstance.simulatePromptTemplatesSimulationsExecuteCreateWithHttpInfo(promptTemplateId, runTestId, executePromptSimulationRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsExecuteCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **runTestId** | **String**|  | |
| **executePromptSimulationRequest** | [**ExecutePromptSimulationRequest**](ExecutePromptSimulationRequest.md)|  | |

### Return type

ApiResponse<[**ExecutePromptSimulationResponse**](ExecutePromptSimulationResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulatePromptTemplatesSimulationsList

> PromptSimulationListResponse simulatePromptTemplatesSimulationsList(promptTemplateId)

Get paginated list of simulation runs for a specific prompt template.

Query Parameters: - limit: number of items per page (default: 10) - page: page number (default: 1) - version_id: filter by specific prompt version

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        try {
            PromptSimulationListResponse result = apiInstance.simulatePromptTemplatesSimulationsList(promptTemplateId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |

### Return type

[**PromptSimulationListResponse**](PromptSimulationListResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulatePromptTemplatesSimulationsListWithHttpInfo

> ApiResponse<PromptSimulationListResponse> simulatePromptTemplatesSimulationsList simulatePromptTemplatesSimulationsListWithHttpInfo(promptTemplateId)

Get paginated list of simulation runs for a specific prompt template.

Query Parameters: - limit: number of items per page (default: 10) - page: page number (default: 1) - version_id: filter by specific prompt version

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        try {
            ApiResponse<PromptSimulationListResponse> response = apiInstance.simulatePromptTemplatesSimulationsListWithHttpInfo(promptTemplateId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |

### Return type

ApiResponse<[**PromptSimulationListResponse**](PromptSimulationListResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulatePromptTemplatesSimulationsPartialUpdate

> PromptSimulationRunResponse simulatePromptTemplatesSimulationsPartialUpdate(promptTemplateId, runTestId, promptSimulationUpdateRequest)



Update a prompt simulation run (version, scenarios, etc.).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        String runTestId = "runTestId_example"; // String | 
        PromptSimulationUpdateRequest promptSimulationUpdateRequest = new PromptSimulationUpdateRequest(); // PromptSimulationUpdateRequest | 
        try {
            PromptSimulationRunResponse result = apiInstance.simulatePromptTemplatesSimulationsPartialUpdate(promptTemplateId, runTestId, promptSimulationUpdateRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsPartialUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **runTestId** | **String**|  | |
| **promptSimulationUpdateRequest** | [**PromptSimulationUpdateRequest**](PromptSimulationUpdateRequest.md)|  | |

### Return type

[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulatePromptTemplatesSimulationsPartialUpdateWithHttpInfo

> ApiResponse<PromptSimulationRunResponse> simulatePromptTemplatesSimulationsPartialUpdate simulatePromptTemplatesSimulationsPartialUpdateWithHttpInfo(promptTemplateId, runTestId, promptSimulationUpdateRequest)



Update a prompt simulation run (version, scenarios, etc.).

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        String runTestId = "runTestId_example"; // String | 
        PromptSimulationUpdateRequest promptSimulationUpdateRequest = new PromptSimulationUpdateRequest(); // PromptSimulationUpdateRequest | 
        try {
            ApiResponse<PromptSimulationRunResponse> response = apiInstance.simulatePromptTemplatesSimulationsPartialUpdateWithHttpInfo(promptTemplateId, runTestId, promptSimulationUpdateRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsPartialUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **runTestId** | **String**|  | |
| **promptSimulationUpdateRequest** | [**PromptSimulationUpdateRequest**](PromptSimulationUpdateRequest.md)|  | |

### Return type

ApiResponse<[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulatePromptTemplatesSimulationsRead

> PromptSimulationRunResponse simulatePromptTemplatesSimulationsRead(promptTemplateId, runTestId)



Retrieve a specific prompt simulation run.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        String runTestId = "runTestId_example"; // String | 
        try {
            PromptSimulationRunResponse result = apiInstance.simulatePromptTemplatesSimulationsRead(promptTemplateId, runTestId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **runTestId** | **String**|  | |

### Return type

[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulatePromptTemplatesSimulationsReadWithHttpInfo

> ApiResponse<PromptSimulationRunResponse> simulatePromptTemplatesSimulationsRead simulatePromptTemplatesSimulationsReadWithHttpInfo(promptTemplateId, runTestId)



Retrieve a specific prompt simulation run.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String promptTemplateId = "promptTemplateId_example"; // String | 
        String runTestId = "runTestId_example"; // String | 
        try {
            ApiResponse<PromptSimulationRunResponse> response = apiInstance.simulatePromptTemplatesSimulationsReadWithHttpInfo(promptTemplateId, runTestId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulatePromptTemplatesSimulationsRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **promptTemplateId** | **String**|  | |
| **runTestId** | **String**|  | |

### Return type

ApiResponse<[**PromptSimulationRunResponse**](PromptSimulationRunResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsActiveList

> AllActiveTests simulateRunTestsActiveList()



Get all active tests

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        try {
            AllActiveTests result = apiInstance.simulateRunTestsActiveList();
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsActiveList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**AllActiveTests**](AllActiveTests.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsActiveListWithHttpInfo

> ApiResponse<AllActiveTests> simulateRunTestsActiveList simulateRunTestsActiveListWithHttpInfo()



Get all active tests

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        try {
            ApiResponse<AllActiveTests> response = apiInstance.simulateRunTestsActiveListWithHttpInfo();
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsActiveList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type

ApiResponse<[**AllActiveTests**](AllActiveTests.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsChatExecuteCreate

> RunTestChatExecutionResponse simulateRunTestsChatExecuteCreate(runTestId, body)



Execute a test run

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        Object body = null; // Object | 
        try {
            RunTestChatExecutionResponse result = apiInstance.simulateRunTestsChatExecuteCreate(runTestId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsChatExecuteCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**RunTestChatExecutionResponse**](RunTestChatExecutionResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsChatExecuteCreateWithHttpInfo

> ApiResponse<RunTestChatExecutionResponse> simulateRunTestsChatExecuteCreate simulateRunTestsChatExecuteCreateWithHttpInfo(runTestId, body)



Execute a test run

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<RunTestChatExecutionResponse> response = apiInstance.simulateRunTestsChatExecuteCreateWithHttpInfo(runTestId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsChatExecuteCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**RunTestChatExecutionResponse**](RunTestChatExecutionResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsComponentsPartialUpdate

> RunTestResponse simulateRunTestsComponentsPartialUpdate(runTestId, runTestComponentsUpdate)



Update components of a specific RunTest

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        RunTestComponentsUpdate runTestComponentsUpdate = new RunTestComponentsUpdate(); // RunTestComponentsUpdate | 
        try {
            RunTestResponse result = apiInstance.simulateRunTestsComponentsPartialUpdate(runTestId, runTestComponentsUpdate);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsComponentsPartialUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **runTestComponentsUpdate** | [**RunTestComponentsUpdate**](RunTestComponentsUpdate.md)|  | |

### Return type

[**RunTestResponse**](RunTestResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsComponentsPartialUpdateWithHttpInfo

> ApiResponse<RunTestResponse> simulateRunTestsComponentsPartialUpdate simulateRunTestsComponentsPartialUpdateWithHttpInfo(runTestId, runTestComponentsUpdate)



Update components of a specific RunTest

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        RunTestComponentsUpdate runTestComponentsUpdate = new RunTestComponentsUpdate(); // RunTestComponentsUpdate | 
        try {
            ApiResponse<RunTestResponse> response = apiInstance.simulateRunTestsComponentsPartialUpdateWithHttpInfo(runTestId, runTestComponentsUpdate);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsComponentsPartialUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **runTestComponentsUpdate** | [**RunTestComponentsUpdate**](RunTestComponentsUpdate.md)|  | |

### Return type

ApiResponse<[**RunTestResponse**](RunTestResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsDeleteDelete

> void simulateRunTestsDeleteDelete(runTestId)



Delete a specific run test

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        try {
            apiInstance.simulateRunTestsDeleteDelete(runTestId);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |

### Return type


null (empty response body)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsDeleteDeleteWithHttpInfo

> ApiResponse<Void> simulateRunTestsDeleteDelete simulateRunTestsDeleteDeleteWithHttpInfo(runTestId)



Delete a specific run test

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        try {
            ApiResponse<Void> response = apiInstance.simulateRunTestsDeleteDeleteWithHttpInfo(runTestId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |

### Return type


ApiResponse<Void>

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsDeleteTestExecutionsCreate

> TestExecutionBulkDeleteResponse simulateRunTestsDeleteTestExecutionsCreate(runTestId, testExecutionBulkDelete)



Delete multiple test executions within a run test.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        TestExecutionBulkDelete testExecutionBulkDelete = new TestExecutionBulkDelete(); // TestExecutionBulkDelete | 
        try {
            TestExecutionBulkDeleteResponse result = apiInstance.simulateRunTestsDeleteTestExecutionsCreate(runTestId, testExecutionBulkDelete);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsDeleteTestExecutionsCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **testExecutionBulkDelete** | [**TestExecutionBulkDelete**](TestExecutionBulkDelete.md)|  | |

### Return type

[**TestExecutionBulkDeleteResponse**](TestExecutionBulkDeleteResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsDeleteTestExecutionsCreateWithHttpInfo

> ApiResponse<TestExecutionBulkDeleteResponse> simulateRunTestsDeleteTestExecutionsCreate simulateRunTestsDeleteTestExecutionsCreateWithHttpInfo(runTestId, testExecutionBulkDelete)



Delete multiple test executions within a run test.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        TestExecutionBulkDelete testExecutionBulkDelete = new TestExecutionBulkDelete(); // TestExecutionBulkDelete | 
        try {
            ApiResponse<TestExecutionBulkDeleteResponse> response = apiInstance.simulateRunTestsDeleteTestExecutionsCreateWithHttpInfo(runTestId, testExecutionBulkDelete);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsDeleteTestExecutionsCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **testExecutionBulkDelete** | [**TestExecutionBulkDelete**](TestExecutionBulkDelete.md)|  | |

### Return type

ApiResponse<[**TestExecutionBulkDeleteResponse**](TestExecutionBulkDeleteResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsEvalConfigsGetStructureList

> EvalConfigStructureResponse simulateRunTestsEvalConfigsGetStructureList(runTestId, evalConfigId)



Get the structure of an evaluation config

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        String evalConfigId = "evalConfigId_example"; // String | 
        try {
            EvalConfigStructureResponse result = apiInstance.simulateRunTestsEvalConfigsGetStructureList(runTestId, evalConfigId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsEvalConfigsGetStructureList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **evalConfigId** | **String**|  | |

### Return type

[**EvalConfigStructureResponse**](EvalConfigStructureResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsEvalConfigsGetStructureListWithHttpInfo

> ApiResponse<EvalConfigStructureResponse> simulateRunTestsEvalConfigsGetStructureList simulateRunTestsEvalConfigsGetStructureListWithHttpInfo(runTestId, evalConfigId)



Get the structure of an evaluation config

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        String evalConfigId = "evalConfigId_example"; // String | 
        try {
            ApiResponse<EvalConfigStructureResponse> response = apiInstance.simulateRunTestsEvalConfigsGetStructureListWithHttpInfo(runTestId, evalConfigId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsEvalConfigsGetStructureList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **evalConfigId** | **String**|  | |

### Return type

ApiResponse<[**EvalConfigStructureResponse**](EvalConfigStructureResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsGetIdByNameRead

> RunTestNameResponse simulateRunTestsGetIdByNameRead(runTestName)



API View to get the id of a run test by name

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestName = "runTestName_example"; // String | 
        try {
            RunTestNameResponse result = apiInstance.simulateRunTestsGetIdByNameRead(runTestName);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsGetIdByNameRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestName** | **String**|  | |

### Return type

[**RunTestNameResponse**](RunTestNameResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsGetIdByNameReadWithHttpInfo

> ApiResponse<RunTestNameResponse> simulateRunTestsGetIdByNameRead simulateRunTestsGetIdByNameReadWithHttpInfo(runTestName)



API View to get the id of a run test by name

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestName = "runTestName_example"; // String | 
        try {
            ApiResponse<RunTestNameResponse> response = apiInstance.simulateRunTestsGetIdByNameReadWithHttpInfo(runTestName);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsGetIdByNameRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestName** | **String**|  | |

### Return type

ApiResponse<[**RunTestNameResponse**](RunTestNameResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsRerunTestExecutionsCreate

> TestExecutionRerunResponse simulateRunTestsRerunTestExecutionsCreate(runTestId, testExecutionRerun)



Rerun multiple test executions (either evaluation only or call + evaluation). All call executions within each test execution are rerun.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        TestExecutionRerun testExecutionRerun = new TestExecutionRerun(); // TestExecutionRerun | 
        try {
            TestExecutionRerunResponse result = apiInstance.simulateRunTestsRerunTestExecutionsCreate(runTestId, testExecutionRerun);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsRerunTestExecutionsCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **testExecutionRerun** | [**TestExecutionRerun**](TestExecutionRerun.md)|  | |

### Return type

[**TestExecutionRerunResponse**](TestExecutionRerunResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsRerunTestExecutionsCreateWithHttpInfo

> ApiResponse<TestExecutionRerunResponse> simulateRunTestsRerunTestExecutionsCreate simulateRunTestsRerunTestExecutionsCreateWithHttpInfo(runTestId, testExecutionRerun)



Rerun multiple test executions (either evaluation only or call + evaluation). All call executions within each test execution are rerun.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        TestExecutionRerun testExecutionRerun = new TestExecutionRerun(); // TestExecutionRerun | 
        try {
            ApiResponse<TestExecutionRerunResponse> response = apiInstance.simulateRunTestsRerunTestExecutionsCreateWithHttpInfo(runTestId, testExecutionRerun);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsRerunTestExecutionsCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |
| **testExecutionRerun** | [**TestExecutionRerun**](TestExecutionRerun.md)|  | |

### Return type

ApiResponse<[**TestExecutionRerunResponse**](TestExecutionRerunResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsScenariosList

> List<RunTestScenarioItemResponse> simulateRunTestsScenariosList(runTestId)



Get paginated list of scenarios for a specific run test Query Parameters: - search: search string to filter scenarios by name - limit: number of items per page (default: 10) - page: page number (default: 1)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        try {
            List<RunTestScenarioItemResponse> result = apiInstance.simulateRunTestsScenariosList(runTestId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsScenariosList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |

### Return type

[**List&lt;RunTestScenarioItemResponse&gt;**](RunTestScenarioItemResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsScenariosListWithHttpInfo

> ApiResponse<List<RunTestScenarioItemResponse>> simulateRunTestsScenariosList simulateRunTestsScenariosListWithHttpInfo(runTestId)



Get paginated list of scenarios for a specific run test Query Parameters: - search: search string to filter scenarios by name - limit: number of items per page (default: 10) - page: page number (default: 1)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        try {
            ApiResponse<List<RunTestScenarioItemResponse>> response = apiInstance.simulateRunTestsScenariosListWithHttpInfo(runTestId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsScenariosList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |

### Return type

ApiResponse<[**List&lt;RunTestScenarioItemResponse&gt;**](RunTestScenarioItemResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateRunTestsSdkCodeList

> ChatSDKCodeResponse simulateRunTestsSdkCodeList(runTestId)



Get the SDK code with placeholders filled

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        try {
            ChatSDKCodeResponse result = apiInstance.simulateRunTestsSdkCodeList(runTestId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsSdkCodeList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |

### Return type

[**ChatSDKCodeResponse**](ChatSDKCodeResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateRunTestsSdkCodeListWithHttpInfo

> ApiResponse<ChatSDKCodeResponse> simulateRunTestsSdkCodeList simulateRunTestsSdkCodeListWithHttpInfo(runTestId)



Get the SDK code with placeholders filled

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String runTestId = "runTestId_example"; // String | 
        try {
            ApiResponse<ChatSDKCodeResponse> response = apiInstance.simulateRunTestsSdkCodeListWithHttpInfo(runTestId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateRunTestsSdkCodeList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **runTestId** | **String**|  | |

### Return type

ApiResponse<[**ChatSDKCodeResponse**](ChatSDKCodeResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateSimulatorAgentsCreateCreate

> SimulatorAgent simulateSimulatorAgentsCreateCreate(simulatorAgent)



Create a new simulator agent

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        SimulatorAgent simulatorAgent = new SimulatorAgent(); // SimulatorAgent | 
        try {
            SimulatorAgent result = apiInstance.simulateSimulatorAgentsCreateCreate(simulatorAgent);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsCreateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **simulatorAgent** | [**SimulatorAgent**](SimulatorAgent.md)|  | |

### Return type

[**SimulatorAgent**](SimulatorAgent.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **0** | Default error response |  -  |

## simulateSimulatorAgentsCreateCreateWithHttpInfo

> ApiResponse<SimulatorAgent> simulateSimulatorAgentsCreateCreate simulateSimulatorAgentsCreateCreateWithHttpInfo(simulatorAgent)



Create a new simulator agent

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        SimulatorAgent simulatorAgent = new SimulatorAgent(); // SimulatorAgent | 
        try {
            ApiResponse<SimulatorAgent> response = apiInstance.simulateSimulatorAgentsCreateCreateWithHttpInfo(simulatorAgent);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsCreateCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **simulatorAgent** | [**SimulatorAgent**](SimulatorAgent.md)|  | |

### Return type

ApiResponse<[**SimulatorAgent**](SimulatorAgent.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **400** | Response |  -  |
| **0** | Default error response |  -  |


## simulateSimulatorAgentsDeleteDelete

> SimulatorAgentDeleteResponse simulateSimulatorAgentsDeleteDelete(agentId)



Soft delete a simulator agent

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            SimulatorAgentDeleteResponse result = apiInstance.simulateSimulatorAgentsDeleteDelete(agentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |

### Return type

[**SimulatorAgentDeleteResponse**](SimulatorAgentDeleteResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateSimulatorAgentsDeleteDeleteWithHttpInfo

> ApiResponse<SimulatorAgentDeleteResponse> simulateSimulatorAgentsDeleteDelete simulateSimulatorAgentsDeleteDeleteWithHttpInfo(agentId)



Soft delete a simulator agent

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            ApiResponse<SimulatorAgentDeleteResponse> response = apiInstance.simulateSimulatorAgentsDeleteDeleteWithHttpInfo(agentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |

### Return type

ApiResponse<[**SimulatorAgentDeleteResponse**](SimulatorAgentDeleteResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateSimulatorAgentsEditUpdate

> SimulatorAgent simulateSimulatorAgentsEditUpdate(agentId, simulatorAgent)



Edit an existing simulator agent

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        SimulatorAgent simulatorAgent = new SimulatorAgent(); // SimulatorAgent | 
        try {
            SimulatorAgent result = apiInstance.simulateSimulatorAgentsEditUpdate(agentId, simulatorAgent);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsEditUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **simulatorAgent** | [**SimulatorAgent**](SimulatorAgent.md)|  | |

### Return type

[**SimulatorAgent**](SimulatorAgent.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **0** | Default error response |  -  |

## simulateSimulatorAgentsEditUpdateWithHttpInfo

> ApiResponse<SimulatorAgent> simulateSimulatorAgentsEditUpdate simulateSimulatorAgentsEditUpdateWithHttpInfo(agentId, simulatorAgent)



Edit an existing simulator agent

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        SimulatorAgent simulatorAgent = new SimulatorAgent(); // SimulatorAgent | 
        try {
            ApiResponse<SimulatorAgent> response = apiInstance.simulateSimulatorAgentsEditUpdateWithHttpInfo(agentId, simulatorAgent);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsEditUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |
| **simulatorAgent** | [**SimulatorAgent**](SimulatorAgent.md)|  | |

### Return type

ApiResponse<[**SimulatorAgent**](SimulatorAgent.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **0** | Default error response |  -  |


## simulateSimulatorAgentsList

> SimulatorAgentListResponse simulateSimulatorAgentsList()



List simulator agents with pagination and search

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        try {
            SimulatorAgentListResponse result = apiInstance.simulateSimulatorAgentsList();
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**SimulatorAgentListResponse**](SimulatorAgentListResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateSimulatorAgentsListWithHttpInfo

> ApiResponse<SimulatorAgentListResponse> simulateSimulatorAgentsList simulateSimulatorAgentsListWithHttpInfo()



List simulator agents with pagination and search

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        try {
            ApiResponse<SimulatorAgentListResponse> response = apiInstance.simulateSimulatorAgentsListWithHttpInfo();
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters

This endpoint does not need any parameter.

### Return type

ApiResponse<[**SimulatorAgentListResponse**](SimulatorAgentListResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateSimulatorAgentsRead

> SimulatorAgent simulateSimulatorAgentsRead(agentId)



Get details of a specific simulator agent

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            SimulatorAgent result = apiInstance.simulateSimulatorAgentsRead(agentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |

### Return type

[**SimulatorAgent**](SimulatorAgent.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateSimulatorAgentsReadWithHttpInfo

> ApiResponse<SimulatorAgent> simulateSimulatorAgentsRead simulateSimulatorAgentsReadWithHttpInfo(agentId)



Get details of a specific simulator agent

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            ApiResponse<SimulatorAgent> response = apiInstance.simulateSimulatorAgentsReadWithHttpInfo(agentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateSimulatorAgentsRead");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **agentId** | **String**|  | |

### Return type

ApiResponse<[**SimulatorAgent**](SimulatorAgent.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateTestExecutionsChatCallExecutionsBatchCreate

> TestExecutionChatBatchResponse simulateTestExecutionsChatCallExecutionsBatchCreate(testExecutionId, body)

Create a batch of CallExecution records for chat execution (exactly 10 per API call).

This follows the same flow as inbound/outbound calls: 1. Resolve SimulatorAgent (scenario &gt; run_test &gt; fallback) 2. Extract base_prompt from SimulatorAgent 3. Handle dataset scenarios (create one CallExecution per row) 4. Enhance prompt with row data if applicable 5. Store proper metadata in CallExecution  Returns exactly 10 CallExecution objects per API call. hasMore is true until ALL row_ids of ALL scenarios have CallExecution objects created.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            TestExecutionChatBatchResponse result = apiInstance.simulateTestExecutionsChatCallExecutionsBatchCreate(testExecutionId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsChatCallExecutionsBatchCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**TestExecutionChatBatchResponse**](TestExecutionChatBatchResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateTestExecutionsChatCallExecutionsBatchCreateWithHttpInfo

> ApiResponse<TestExecutionChatBatchResponse> simulateTestExecutionsChatCallExecutionsBatchCreate simulateTestExecutionsChatCallExecutionsBatchCreateWithHttpInfo(testExecutionId, body)

Create a batch of CallExecution records for chat execution (exactly 10 per API call).

This follows the same flow as inbound/outbound calls: 1. Resolve SimulatorAgent (scenario &gt; run_test &gt; fallback) 2. Extract base_prompt from SimulatorAgent 3. Handle dataset scenarios (create one CallExecution per row) 4. Enhance prompt with row data if applicable 5. Store proper metadata in CallExecution  Returns exactly 10 CallExecution objects per API call. hasMore is true until ALL row_ids of ALL scenarios have CallExecution objects created.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<TestExecutionChatBatchResponse> response = apiInstance.simulateTestExecutionsChatCallExecutionsBatchCreateWithHttpInfo(testExecutionId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsChatCallExecutionsBatchCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**TestExecutionChatBatchResponse**](TestExecutionChatBatchResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateTestExecutionsColumnOrderUpdate

> TestExecutionColumnOrderResponse simulateTestExecutionsColumnOrderUpdate(testExecutionId, testExecutionColumnOrder)



Update column order for a test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        TestExecutionColumnOrder testExecutionColumnOrder = new TestExecutionColumnOrder(); // TestExecutionColumnOrder | 
        try {
            TestExecutionColumnOrderResponse result = apiInstance.simulateTestExecutionsColumnOrderUpdate(testExecutionId, testExecutionColumnOrder);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsColumnOrderUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **testExecutionColumnOrder** | [**TestExecutionColumnOrder**](TestExecutionColumnOrder.md)|  | |

### Return type

[**TestExecutionColumnOrderResponse**](TestExecutionColumnOrderResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateTestExecutionsColumnOrderUpdateWithHttpInfo

> ApiResponse<TestExecutionColumnOrderResponse> simulateTestExecutionsColumnOrderUpdate simulateTestExecutionsColumnOrderUpdateWithHttpInfo(testExecutionId, testExecutionColumnOrder)



Update column order for a test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        TestExecutionColumnOrder testExecutionColumnOrder = new TestExecutionColumnOrder(); // TestExecutionColumnOrder | 
        try {
            ApiResponse<TestExecutionColumnOrderResponse> response = apiInstance.simulateTestExecutionsColumnOrderUpdateWithHttpInfo(testExecutionId, testExecutionColumnOrder);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsColumnOrderUpdate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **testExecutionColumnOrder** | [**TestExecutionColumnOrder**](TestExecutionColumnOrder.md)|  | |

### Return type

ApiResponse<[**TestExecutionColumnOrderResponse**](TestExecutionColumnOrderResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateTestExecutionsDeleteDelete

> void simulateTestExecutionsDeleteDelete(testExecutionId)



Delete a specific test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            apiInstance.simulateTestExecutionsDeleteDelete(testExecutionId);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |

### Return type


null (empty response body)

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateTestExecutionsDeleteDeleteWithHttpInfo

> ApiResponse<Void> simulateTestExecutionsDeleteDelete simulateTestExecutionsDeleteDeleteWithHttpInfo(testExecutionId)



Delete a specific test execution

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            ApiResponse<Void> response = apiInstance.simulateTestExecutionsDeleteDeleteWithHttpInfo(testExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsDeleteDelete");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |

### Return type


ApiResponse<Void>

### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateTestExecutionsEvalExplanationSummaryList

> EvalExplanationSummaryResponse simulateTestExecutionsEvalExplanationSummaryList(testExecutionId)



Fetch the evaluation explanation summary from the database. If not present, trigger async calculation and return empty response.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            EvalExplanationSummaryResponse result = apiInstance.simulateTestExecutionsEvalExplanationSummaryList(testExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsEvalExplanationSummaryList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |

### Return type

[**EvalExplanationSummaryResponse**](EvalExplanationSummaryResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateTestExecutionsEvalExplanationSummaryListWithHttpInfo

> ApiResponse<EvalExplanationSummaryResponse> simulateTestExecutionsEvalExplanationSummaryList simulateTestExecutionsEvalExplanationSummaryListWithHttpInfo(testExecutionId)



Fetch the evaluation explanation summary from the database. If not present, trigger async calculation and return empty response.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            ApiResponse<EvalExplanationSummaryResponse> response = apiInstance.simulateTestExecutionsEvalExplanationSummaryListWithHttpInfo(testExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsEvalExplanationSummaryList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |

### Return type

ApiResponse<[**EvalExplanationSummaryResponse**](EvalExplanationSummaryResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateTestExecutionsEvalExplanationSummaryRefreshCreate

> EvalExplanationSummaryRefreshResponse simulateTestExecutionsEvalExplanationSummaryRefreshCreate(testExecutionId, body)



Refresh the evaluation explanation summary by recalculating it. This endpoint triggers the summary calculation task again.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            EvalExplanationSummaryRefreshResponse result = apiInstance.simulateTestExecutionsEvalExplanationSummaryRefreshCreate(testExecutionId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsEvalExplanationSummaryRefreshCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**EvalExplanationSummaryRefreshResponse**](EvalExplanationSummaryRefreshResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateTestExecutionsEvalExplanationSummaryRefreshCreateWithHttpInfo

> ApiResponse<EvalExplanationSummaryRefreshResponse> simulateTestExecutionsEvalExplanationSummaryRefreshCreate simulateTestExecutionsEvalExplanationSummaryRefreshCreateWithHttpInfo(testExecutionId, body)



Refresh the evaluation explanation summary by recalculating it. This endpoint triggers the summary calculation task again.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<EvalExplanationSummaryRefreshResponse> response = apiInstance.simulateTestExecutionsEvalExplanationSummaryRefreshCreateWithHttpInfo(testExecutionId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsEvalExplanationSummaryRefreshCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**EvalExplanationSummaryRefreshResponse**](EvalExplanationSummaryRefreshResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateTestExecutionsOptimiserAnalysisList

> OptimiserAnalysisResponse simulateTestExecutionsOptimiserAnalysisList(testExecutionId)



Fetch the agent optimiser analysis for a test execution. If not present or pending, returns status information.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            OptimiserAnalysisResponse result = apiInstance.simulateTestExecutionsOptimiserAnalysisList(testExecutionId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsOptimiserAnalysisList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |

### Return type

[**OptimiserAnalysisResponse**](OptimiserAnalysisResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateTestExecutionsOptimiserAnalysisListWithHttpInfo

> ApiResponse<OptimiserAnalysisResponse> simulateTestExecutionsOptimiserAnalysisList simulateTestExecutionsOptimiserAnalysisListWithHttpInfo(testExecutionId)



Fetch the agent optimiser analysis for a test execution. If not present or pending, returns status information.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        try {
            ApiResponse<OptimiserAnalysisResponse> response = apiInstance.simulateTestExecutionsOptimiserAnalysisListWithHttpInfo(testExecutionId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsOptimiserAnalysisList");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |

### Return type

ApiResponse<[**OptimiserAnalysisResponse**](OptimiserAnalysisResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateTestExecutionsOptimiserAnalysisRefreshCreate

> OptimiserAnalysisRefreshResponse simulateTestExecutionsOptimiserAnalysisRefreshCreate(testExecutionId, body)



Trigger a new agent optimiser analysis run.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            OptimiserAnalysisRefreshResponse result = apiInstance.simulateTestExecutionsOptimiserAnalysisRefreshCreate(testExecutionId, body);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsOptimiserAnalysisRefreshCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

[**OptimiserAnalysisRefreshResponse**](OptimiserAnalysisRefreshResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateTestExecutionsOptimiserAnalysisRefreshCreateWithHttpInfo

> ApiResponse<OptimiserAnalysisRefreshResponse> simulateTestExecutionsOptimiserAnalysisRefreshCreate simulateTestExecutionsOptimiserAnalysisRefreshCreateWithHttpInfo(testExecutionId, body)



Trigger a new agent optimiser analysis run.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        Object body = null; // Object | 
        try {
            ApiResponse<OptimiserAnalysisRefreshResponse> response = apiInstance.simulateTestExecutionsOptimiserAnalysisRefreshCreateWithHttpInfo(testExecutionId, body);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsOptimiserAnalysisRefreshCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **body** | **Object**|  | |

### Return type

ApiResponse<[**OptimiserAnalysisRefreshResponse**](OptimiserAnalysisRefreshResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateTestExecutionsRerunCallsCreate

> RerunCallsResponse simulateTestExecutionsRerunCallsCreate(testExecutionId, callExecutionRerun)



Rerun multiple call executions (either evaluation only or call + evaluation)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        CallExecutionRerun callExecutionRerun = new CallExecutionRerun(); // CallExecutionRerun | 
        try {
            RerunCallsResponse result = apiInstance.simulateTestExecutionsRerunCallsCreate(testExecutionId, callExecutionRerun);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsRerunCallsCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Reason: " + e.getResponseBody());
            System.err.println("Response headers: " + e.getResponseHeaders());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **callExecutionRerun** | [**CallExecutionRerun**](CallExecutionRerun.md)|  | |

### Return type

[**RerunCallsResponse**](RerunCallsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateTestExecutionsRerunCallsCreateWithHttpInfo

> ApiResponse<RerunCallsResponse> simulateTestExecutionsRerunCallsCreate simulateTestExecutionsRerunCallsCreateWithHttpInfo(testExecutionId, callExecutionRerun)



Rerun multiple call executions (either evaluation only or call + evaluation)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulateApi;

public class Example {
    public static void main(String[] args) {
        ApiClient defaultClient = Configuration.getDefaultApiClient();
        defaultClient.setBasePath("https://api.futureagi.com");
        
        // Configure API key authorization: X-Secret-Key
        ApiKeyAuth X-Secret-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Secret-Key");
        X-Secret-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Secret-Key.setApiKeyPrefix("Token");

        // Configure API key authorization: X-Api-Key
        ApiKeyAuth X-Api-Key = (ApiKeyAuth) defaultClient.getAuthentication("X-Api-Key");
        X-Api-Key.setApiKey("YOUR API KEY");
        // Uncomment the following line to set a prefix for the API key, e.g. "Token" (defaults to null)
        //X-Api-Key.setApiKeyPrefix("Token");

        SimulateApi apiInstance = new SimulateApi(defaultClient);
        String testExecutionId = "testExecutionId_example"; // String | 
        CallExecutionRerun callExecutionRerun = new CallExecutionRerun(); // CallExecutionRerun | 
        try {
            ApiResponse<RerunCallsResponse> response = apiInstance.simulateTestExecutionsRerunCallsCreateWithHttpInfo(testExecutionId, callExecutionRerun);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulateApi#simulateTestExecutionsRerunCallsCreate");
            System.err.println("Status code: " + e.getCode());
            System.err.println("Response headers: " + e.getResponseHeaders());
            System.err.println("Reason: " + e.getResponseBody());
            e.printStackTrace();
        }
    }
}
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **testExecutionId** | **String**|  | |
| **callExecutionRerun** | [**CallExecutionRerun**](CallExecutionRerun.md)|  | |

### Return type

ApiResponse<[**RerunCallsResponse**](RerunCallsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

