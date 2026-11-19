# TracerApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**tracerFeedIssuesCreateLinearIssueCreate**](TracerApi.md#tracerFeedIssuesCreateLinearIssueCreate) | **POST** /tracer/feed/issues/{cluster_id}/create-linear-issue/ |  |
| [**tracerFeedIssuesCreateLinearIssueCreateWithHttpInfo**](TracerApi.md#tracerFeedIssuesCreateLinearIssueCreateWithHttpInfo) | **POST** /tracer/feed/issues/{cluster_id}/create-linear-issue/ |  |
| [**tracerFeedIssuesDeepAnalysisCreate**](TracerApi.md#tracerFeedIssuesDeepAnalysisCreate) | **POST** /tracer/feed/issues/{cluster_id}/deep-analysis/ |  |
| [**tracerFeedIssuesDeepAnalysisCreateWithHttpInfo**](TracerApi.md#tracerFeedIssuesDeepAnalysisCreateWithHttpInfo) | **POST** /tracer/feed/issues/{cluster_id}/deep-analysis/ |  |
| [**tracerFeedIssuesOverviewList**](TracerApi.md#tracerFeedIssuesOverviewList) | **GET** /tracer/feed/issues/{cluster_id}/overview/ |  |
| [**tracerFeedIssuesOverviewListWithHttpInfo**](TracerApi.md#tracerFeedIssuesOverviewListWithHttpInfo) | **GET** /tracer/feed/issues/{cluster_id}/overview/ |  |
| [**tracerFeedIssuesPartialUpdate**](TracerApi.md#tracerFeedIssuesPartialUpdate) | **PATCH** /tracer/feed/issues/{cluster_id}/ |  |
| [**tracerFeedIssuesPartialUpdateWithHttpInfo**](TracerApi.md#tracerFeedIssuesPartialUpdateWithHttpInfo) | **PATCH** /tracer/feed/issues/{cluster_id}/ |  |
| [**tracerFeedIssuesRootCauseList**](TracerApi.md#tracerFeedIssuesRootCauseList) | **GET** /tracer/feed/issues/{cluster_id}/root-cause/ | GET /tracer/feed/issues/{cluster_id}/root-cause/?trace_id&#x3D;X |
| [**tracerFeedIssuesRootCauseListWithHttpInfo**](TracerApi.md#tracerFeedIssuesRootCauseListWithHttpInfo) | **GET** /tracer/feed/issues/{cluster_id}/root-cause/ | GET /tracer/feed/issues/{cluster_id}/root-cause/?trace_id&#x3D;X |
| [**tracerFeedIssuesSidebarList**](TracerApi.md#tracerFeedIssuesSidebarList) | **GET** /tracer/feed/issues/{cluster_id}/sidebar/ | GET /tracer/feed/issues/{cluster_id}/sidebar/ |
| [**tracerFeedIssuesSidebarListWithHttpInfo**](TracerApi.md#tracerFeedIssuesSidebarListWithHttpInfo) | **GET** /tracer/feed/issues/{cluster_id}/sidebar/ | GET /tracer/feed/issues/{cluster_id}/sidebar/ |
| [**tracerFeedIssuesTracesList**](TracerApi.md#tracerFeedIssuesTracesList) | **GET** /tracer/feed/issues/{cluster_id}/traces/ |  |
| [**tracerFeedIssuesTracesListWithHttpInfo**](TracerApi.md#tracerFeedIssuesTracesListWithHttpInfo) | **GET** /tracer/feed/issues/{cluster_id}/traces/ |  |
| [**tracerFeedIssuesTrendsList**](TracerApi.md#tracerFeedIssuesTrendsList) | **GET** /tracer/feed/issues/{cluster_id}/trends/ |  |
| [**tracerFeedIssuesTrendsListWithHttpInfo**](TracerApi.md#tracerFeedIssuesTrendsListWithHttpInfo) | **GET** /tracer/feed/issues/{cluster_id}/trends/ |  |
| [**tracerTraceAgentGraph**](TracerApi.md#tracerTraceAgentGraph) | **GET** /tracer/trace/agent_graph/ | Return the aggregate agent graph for a project. |
| [**tracerTraceAgentGraphWithHttpInfo**](TracerApi.md#tracerTraceAgentGraphWithHttpInfo) | **GET** /tracer/trace/agent_graph/ | Return the aggregate agent graph for a project. |
| [**tracerTraceAnnotationCreate**](TracerApi.md#tracerTraceAnnotationCreate) | **POST** /tracer/trace-annotation/ |  |
| [**tracerTraceAnnotationCreateWithHttpInfo**](TracerApi.md#tracerTraceAnnotationCreateWithHttpInfo) | **POST** /tracer/trace-annotation/ |  |
| [**tracerTraceAnnotationDelete**](TracerApi.md#tracerTraceAnnotationDelete) | **DELETE** /tracer/trace-annotation/{id}/ |  |
| [**tracerTraceAnnotationDeleteWithHttpInfo**](TracerApi.md#tracerTraceAnnotationDeleteWithHttpInfo) | **DELETE** /tracer/trace-annotation/{id}/ |  |
| [**tracerTraceAnnotationGetAnnotationValues**](TracerApi.md#tracerTraceAnnotationGetAnnotationValues) | **GET** /tracer/trace-annotation/get_annotation_values/ |  |
| [**tracerTraceAnnotationGetAnnotationValuesWithHttpInfo**](TracerApi.md#tracerTraceAnnotationGetAnnotationValuesWithHttpInfo) | **GET** /tracer/trace-annotation/get_annotation_values/ |  |
| [**tracerTraceAnnotationList**](TracerApi.md#tracerTraceAnnotationList) | **GET** /tracer/trace-annotation/ |  |
| [**tracerTraceAnnotationListWithHttpInfo**](TracerApi.md#tracerTraceAnnotationListWithHttpInfo) | **GET** /tracer/trace-annotation/ |  |
| [**tracerTraceAnnotationPartialUpdate**](TracerApi.md#tracerTraceAnnotationPartialUpdate) | **PATCH** /tracer/trace-annotation/{id}/ |  |
| [**tracerTraceAnnotationPartialUpdateWithHttpInfo**](TracerApi.md#tracerTraceAnnotationPartialUpdateWithHttpInfo) | **PATCH** /tracer/trace-annotation/{id}/ |  |
| [**tracerTraceAnnotationRead**](TracerApi.md#tracerTraceAnnotationRead) | **GET** /tracer/trace-annotation/{id}/ |  |
| [**tracerTraceAnnotationReadWithHttpInfo**](TracerApi.md#tracerTraceAnnotationReadWithHttpInfo) | **GET** /tracer/trace-annotation/{id}/ |  |
| [**tracerTraceAnnotationUpdate**](TracerApi.md#tracerTraceAnnotationUpdate) | **PUT** /tracer/trace-annotation/{id}/ |  |
| [**tracerTraceAnnotationUpdateWithHttpInfo**](TracerApi.md#tracerTraceAnnotationUpdateWithHttpInfo) | **PUT** /tracer/trace-annotation/{id}/ |  |
| [**tracerTraceBulkCreate**](TracerApi.md#tracerTraceBulkCreate) | **POST** /tracer/trace/bulk_create/ |  |
| [**tracerTraceBulkCreateWithHttpInfo**](TracerApi.md#tracerTraceBulkCreateWithHttpInfo) | **POST** /tracer/trace/bulk_create/ |  |
| [**tracerTraceCompareTraces**](TracerApi.md#tracerTraceCompareTraces) | **POST** /tracer/trace/compare_traces/ |  |
| [**tracerTraceCompareTracesWithHttpInfo**](TracerApi.md#tracerTraceCompareTracesWithHttpInfo) | **POST** /tracer/trace/compare_traces/ |  |
| [**tracerTraceCreate**](TracerApi.md#tracerTraceCreate) | **POST** /tracer/trace/ |  |
| [**tracerTraceCreateWithHttpInfo**](TracerApi.md#tracerTraceCreateWithHttpInfo) | **POST** /tracer/trace/ |  |
| [**tracerTraceDelete**](TracerApi.md#tracerTraceDelete) | **DELETE** /tracer/trace/{id}/ |  |
| [**tracerTraceDeleteWithHttpInfo**](TracerApi.md#tracerTraceDeleteWithHttpInfo) | **DELETE** /tracer/trace/{id}/ |  |
| [**tracerTraceGetEvalNames**](TracerApi.md#tracerTraceGetEvalNames) | **GET** /tracer/trace/get_eval_names/ |  |
| [**tracerTraceGetEvalNamesWithHttpInfo**](TracerApi.md#tracerTraceGetEvalNamesWithHttpInfo) | **GET** /tracer/trace/get_eval_names/ |  |
| [**tracerTraceGetTraceExportData**](TracerApi.md#tracerTraceGetTraceExportData) | **GET** /tracer/trace/get_trace_export_data/ |  |
| [**tracerTraceGetTraceExportDataWithHttpInfo**](TracerApi.md#tracerTraceGetTraceExportDataWithHttpInfo) | **GET** /tracer/trace/get_trace_export_data/ |  |
| [**tracerTraceGetTraceIdByIndex**](TracerApi.md#tracerTraceGetTraceIdByIndex) | **GET** /tracer/trace/get_trace_id_by_index/ |  |
| [**tracerTraceGetTraceIdByIndexWithHttpInfo**](TracerApi.md#tracerTraceGetTraceIdByIndexWithHttpInfo) | **GET** /tracer/trace/get_trace_id_by_index/ |  |
| [**tracerTraceGetTraceIdByIndexObserve**](TracerApi.md#tracerTraceGetTraceIdByIndexObserve) | **GET** /tracer/trace/get_trace_id_by_index_observe/ |  |
| [**tracerTraceGetTraceIdByIndexObserveWithHttpInfo**](TracerApi.md#tracerTraceGetTraceIdByIndexObserveWithHttpInfo) | **GET** /tracer/trace/get_trace_id_by_index_observe/ |  |
| [**tracerTraceList**](TracerApi.md#tracerTraceList) | **GET** /tracer/trace/ |  |
| [**tracerTraceListWithHttpInfo**](TracerApi.md#tracerTraceListWithHttpInfo) | **GET** /tracer/trace/ |  |
| [**tracerTraceListTracesOfSession**](TracerApi.md#tracerTraceListTracesOfSession) | **GET** /tracer/trace/list_traces_of_session/ |  |
| [**tracerTraceListTracesOfSessionWithHttpInfo**](TracerApi.md#tracerTraceListTracesOfSessionWithHttpInfo) | **GET** /tracer/trace/list_traces_of_session/ |  |
| [**tracerTracePartialUpdate**](TracerApi.md#tracerTracePartialUpdate) | **PATCH** /tracer/trace/{id}/ |  |
| [**tracerTracePartialUpdateWithHttpInfo**](TracerApi.md#tracerTracePartialUpdateWithHttpInfo) | **PATCH** /tracer/trace/{id}/ |  |
| [**tracerTraceSessionCreate**](TracerApi.md#tracerTraceSessionCreate) | **POST** /tracer/trace-session/ |  |
| [**tracerTraceSessionCreateWithHttpInfo**](TracerApi.md#tracerTraceSessionCreateWithHttpInfo) | **POST** /tracer/trace-session/ |  |
| [**tracerTraceSessionDelete**](TracerApi.md#tracerTraceSessionDelete) | **DELETE** /tracer/trace-session/{id}/ |  |
| [**tracerTraceSessionDeleteWithHttpInfo**](TracerApi.md#tracerTraceSessionDeleteWithHttpInfo) | **DELETE** /tracer/trace-session/{id}/ |  |
| [**tracerTraceSessionEvalLogs**](TracerApi.md#tracerTraceSessionEvalLogs) | **GET** /tracer/trace-session/{id}/eval_logs/ | Session-scoped eval log feed for TracesDrawer&#39;s \&quot;Evals\&quot; tab. |
| [**tracerTraceSessionEvalLogsWithHttpInfo**](TracerApi.md#tracerTraceSessionEvalLogsWithHttpInfo) | **GET** /tracer/trace-session/{id}/eval_logs/ | Session-scoped eval log feed for TracesDrawer&#39;s \&quot;Evals\&quot; tab. |
| [**tracerTraceSessionGetSessionFilterValues**](TracerApi.md#tracerTraceSessionGetSessionFilterValues) | **GET** /tracer/trace-session/get_session_filter_values/ |  |
| [**tracerTraceSessionGetSessionFilterValuesWithHttpInfo**](TracerApi.md#tracerTraceSessionGetSessionFilterValuesWithHttpInfo) | **GET** /tracer/trace-session/get_session_filter_values/ |  |
| [**tracerTraceSessionGetTraceSessionExportData**](TracerApi.md#tracerTraceSessionGetTraceSessionExportData) | **GET** /tracer/trace-session/get_trace_session_export_data/ |  |
| [**tracerTraceSessionGetTraceSessionExportDataWithHttpInfo**](TracerApi.md#tracerTraceSessionGetTraceSessionExportDataWithHttpInfo) | **GET** /tracer/trace-session/get_trace_session_export_data/ |  |
| [**tracerTraceSessionList**](TracerApi.md#tracerTraceSessionList) | **GET** /tracer/trace-session/ |  |
| [**tracerTraceSessionListWithHttpInfo**](TracerApi.md#tracerTraceSessionListWithHttpInfo) | **GET** /tracer/trace-session/ |  |
| [**tracerTraceSessionPartialUpdate**](TracerApi.md#tracerTraceSessionPartialUpdate) | **PATCH** /tracer/trace-session/{id}/ |  |
| [**tracerTraceSessionPartialUpdateWithHttpInfo**](TracerApi.md#tracerTraceSessionPartialUpdateWithHttpInfo) | **PATCH** /tracer/trace-session/{id}/ |  |
| [**tracerTraceSessionUpdate**](TracerApi.md#tracerTraceSessionUpdate) | **PUT** /tracer/trace-session/{id}/ |  |
| [**tracerTraceSessionUpdateWithHttpInfo**](TracerApi.md#tracerTraceSessionUpdateWithHttpInfo) | **PUT** /tracer/trace-session/{id}/ |  |
| [**tracerTraceUpdate**](TracerApi.md#tracerTraceUpdate) | **PUT** /tracer/trace/{id}/ |  |
| [**tracerTraceUpdateWithHttpInfo**](TracerApi.md#tracerTraceUpdateWithHttpInfo) | **PUT** /tracer/trace/{id}/ |  |
| [**tracerUserAlertLogsCreate**](TracerApi.md#tracerUserAlertLogsCreate) | **POST** /tracer/user-alert-logs/ |  |
| [**tracerUserAlertLogsCreateWithHttpInfo**](TracerApi.md#tracerUserAlertLogsCreateWithHttpInfo) | **POST** /tracer/user-alert-logs/ |  |
| [**tracerUserAlertLogsDelete**](TracerApi.md#tracerUserAlertLogsDelete) | **DELETE** /tracer/user-alert-logs/{id}/ |  |
| [**tracerUserAlertLogsDeleteWithHttpInfo**](TracerApi.md#tracerUserAlertLogsDeleteWithHttpInfo) | **DELETE** /tracer/user-alert-logs/{id}/ |  |
| [**tracerUserAlertLogsPartialUpdate**](TracerApi.md#tracerUserAlertLogsPartialUpdate) | **PATCH** /tracer/user-alert-logs/{id}/ |  |
| [**tracerUserAlertLogsPartialUpdateWithHttpInfo**](TracerApi.md#tracerUserAlertLogsPartialUpdateWithHttpInfo) | **PATCH** /tracer/user-alert-logs/{id}/ |  |
| [**tracerUserAlertLogsUpdate**](TracerApi.md#tracerUserAlertLogsUpdate) | **PUT** /tracer/user-alert-logs/{id}/ |  |
| [**tracerUserAlertLogsUpdateWithHttpInfo**](TracerApi.md#tracerUserAlertLogsUpdateWithHttpInfo) | **PUT** /tracer/user-alert-logs/{id}/ |  |
| [**tracerUserAlertsDuplicate**](TracerApi.md#tracerUserAlertsDuplicate) | **POST** /tracer/user-alerts/duplicate/ |  |
| [**tracerUserAlertsDuplicateWithHttpInfo**](TracerApi.md#tracerUserAlertsDuplicateWithHttpInfo) | **POST** /tracer/user-alerts/duplicate/ |  |
| [**tracerUserAlertsListMonitors**](TracerApi.md#tracerUserAlertsListMonitors) | **GET** /tracer/user-alerts/list_monitors/ |  |
| [**tracerUserAlertsListMonitorsWithHttpInfo**](TracerApi.md#tracerUserAlertsListMonitorsWithHttpInfo) | **GET** /tracer/user-alerts/list_monitors/ |  |
| [**tracerUserAlertsUpdate**](TracerApi.md#tracerUserAlertsUpdate) | **PUT** /tracer/user-alerts/{id}/ |  |
| [**tracerUserAlertsUpdateWithHttpInfo**](TracerApi.md#tracerUserAlertsUpdateWithHttpInfo) | **PUT** /tracer/user-alerts/{id}/ |  |
| [**tracerUsersGetCodeExampleList**](TracerApi.md#tracerUsersGetCodeExampleList) | **GET** /tracer/users/get_code_example/ |  |
| [**tracerUsersGetCodeExampleListWithHttpInfo**](TracerApi.md#tracerUsersGetCodeExampleListWithHttpInfo) | **GET** /tracer/users/get_code_example/ |  |



## tracerFeedIssuesCreateLinearIssueCreate

> CreateLinearIssueResponse tracerFeedIssuesCreateLinearIssueCreate(clusterId, createLinearIssue)



POST /tracer/feed/issues/{cluster_id}/create-linear-issue/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        CreateLinearIssue createLinearIssue = new CreateLinearIssue(); // CreateLinearIssue | 
        try {
            CreateLinearIssueResponse result = apiInstance.tracerFeedIssuesCreateLinearIssueCreate(clusterId, createLinearIssue);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesCreateLinearIssueCreate");
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
| **clusterId** | **String**|  | |
| **createLinearIssue** | [**CreateLinearIssue**](CreateLinearIssue.md)|  | |

### Return type

[**CreateLinearIssueResponse**](CreateLinearIssueResponse.md)


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

## tracerFeedIssuesCreateLinearIssueCreateWithHttpInfo

> ApiResponse<CreateLinearIssueResponse> tracerFeedIssuesCreateLinearIssueCreate tracerFeedIssuesCreateLinearIssueCreateWithHttpInfo(clusterId, createLinearIssue)



POST /tracer/feed/issues/{cluster_id}/create-linear-issue/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        CreateLinearIssue createLinearIssue = new CreateLinearIssue(); // CreateLinearIssue | 
        try {
            ApiResponse<CreateLinearIssueResponse> response = apiInstance.tracerFeedIssuesCreateLinearIssueCreateWithHttpInfo(clusterId, createLinearIssue);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesCreateLinearIssueCreate");
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
| **clusterId** | **String**|  | |
| **createLinearIssue** | [**CreateLinearIssue**](CreateLinearIssue.md)|  | |

### Return type

ApiResponse<[**CreateLinearIssueResponse**](CreateLinearIssueResponse.md)>


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


## tracerFeedIssuesDeepAnalysisCreate

> DeepAnalysisDispatchApiResponse tracerFeedIssuesDeepAnalysisCreate(clusterId, deepAnalysisBody)



POST /tracer/feed/issues/{cluster_id}/deep-analysis/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        DeepAnalysisBody deepAnalysisBody = new DeepAnalysisBody(); // DeepAnalysisBody | 
        try {
            DeepAnalysisDispatchApiResponse result = apiInstance.tracerFeedIssuesDeepAnalysisCreate(clusterId, deepAnalysisBody);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesDeepAnalysisCreate");
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
| **clusterId** | **String**|  | |
| **deepAnalysisBody** | [**DeepAnalysisBody**](DeepAnalysisBody.md)|  | |

### Return type

[**DeepAnalysisDispatchApiResponse**](DeepAnalysisDispatchApiResponse.md)


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

## tracerFeedIssuesDeepAnalysisCreateWithHttpInfo

> ApiResponse<DeepAnalysisDispatchApiResponse> tracerFeedIssuesDeepAnalysisCreate tracerFeedIssuesDeepAnalysisCreateWithHttpInfo(clusterId, deepAnalysisBody)



POST /tracer/feed/issues/{cluster_id}/deep-analysis/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        DeepAnalysisBody deepAnalysisBody = new DeepAnalysisBody(); // DeepAnalysisBody | 
        try {
            ApiResponse<DeepAnalysisDispatchApiResponse> response = apiInstance.tracerFeedIssuesDeepAnalysisCreateWithHttpInfo(clusterId, deepAnalysisBody);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesDeepAnalysisCreate");
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
| **clusterId** | **String**|  | |
| **deepAnalysisBody** | [**DeepAnalysisBody**](DeepAnalysisBody.md)|  | |

### Return type

ApiResponse<[**DeepAnalysisDispatchApiResponse**](DeepAnalysisDispatchApiResponse.md)>


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


## tracerFeedIssuesOverviewList

> OverviewApiResponse tracerFeedIssuesOverviewList(clusterId)



GET /tracer/feed/issues/{cluster_id}/overview/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        try {
            OverviewApiResponse result = apiInstance.tracerFeedIssuesOverviewList(clusterId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesOverviewList");
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
| **clusterId** | **String**|  | |

### Return type

[**OverviewApiResponse**](OverviewApiResponse.md)


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## tracerFeedIssuesOverviewListWithHttpInfo

> ApiResponse<OverviewApiResponse> tracerFeedIssuesOverviewList tracerFeedIssuesOverviewListWithHttpInfo(clusterId)



GET /tracer/feed/issues/{cluster_id}/overview/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        try {
            ApiResponse<OverviewApiResponse> response = apiInstance.tracerFeedIssuesOverviewListWithHttpInfo(clusterId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesOverviewList");
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
| **clusterId** | **String**|  | |

### Return type

ApiResponse<[**OverviewApiResponse**](OverviewApiResponse.md)>


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## tracerFeedIssuesPartialUpdate

> FeedDetailApiResponse tracerFeedIssuesPartialUpdate(clusterId, feedUpdateBody)



GET + PATCH /tracer/feed/issues/{cluster_id}/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        FeedUpdateBody feedUpdateBody = new FeedUpdateBody(); // FeedUpdateBody | 
        try {
            FeedDetailApiResponse result = apiInstance.tracerFeedIssuesPartialUpdate(clusterId, feedUpdateBody);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesPartialUpdate");
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
| **clusterId** | **String**|  | |
| **feedUpdateBody** | [**FeedUpdateBody**](FeedUpdateBody.md)|  | |

### Return type

[**FeedDetailApiResponse**](FeedDetailApiResponse.md)


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

## tracerFeedIssuesPartialUpdateWithHttpInfo

> ApiResponse<FeedDetailApiResponse> tracerFeedIssuesPartialUpdate tracerFeedIssuesPartialUpdateWithHttpInfo(clusterId, feedUpdateBody)



GET + PATCH /tracer/feed/issues/{cluster_id}/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        FeedUpdateBody feedUpdateBody = new FeedUpdateBody(); // FeedUpdateBody | 
        try {
            ApiResponse<FeedDetailApiResponse> response = apiInstance.tracerFeedIssuesPartialUpdateWithHttpInfo(clusterId, feedUpdateBody);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesPartialUpdate");
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
| **clusterId** | **String**|  | |
| **feedUpdateBody** | [**FeedUpdateBody**](FeedUpdateBody.md)|  | |

### Return type

ApiResponse<[**FeedDetailApiResponse**](FeedDetailApiResponse.md)>


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


## tracerFeedIssuesRootCauseList

> DeepAnalysisApiResponse tracerFeedIssuesRootCauseList(clusterId, traceId)

GET /tracer/feed/issues/{cluster_id}/root-cause/?trace_id&#x3D;X

Read cached deep-analysis results for a single trace within the cluster. The frontend hits this on mount (to show existing results) and polls it after a POST to /deep-analysis/ until &#x60;&#x60;status&#x60;&#x60; flips from &#x60;&#x60;running&#x60;&#x60; to &#x60;&#x60;done&#x60;&#x60; or &#x60;&#x60;failed&#x60;&#x60;.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        String traceId = "traceId_example"; // String | 
        try {
            DeepAnalysisApiResponse result = apiInstance.tracerFeedIssuesRootCauseList(clusterId, traceId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesRootCauseList");
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
| **clusterId** | **String**|  | |
| **traceId** | **String**|  | |

### Return type

[**DeepAnalysisApiResponse**](DeepAnalysisApiResponse.md)


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## tracerFeedIssuesRootCauseListWithHttpInfo

> ApiResponse<DeepAnalysisApiResponse> tracerFeedIssuesRootCauseList tracerFeedIssuesRootCauseListWithHttpInfo(clusterId, traceId)

GET /tracer/feed/issues/{cluster_id}/root-cause/?trace_id&#x3D;X

Read cached deep-analysis results for a single trace within the cluster. The frontend hits this on mount (to show existing results) and polls it after a POST to /deep-analysis/ until &#x60;&#x60;status&#x60;&#x60; flips from &#x60;&#x60;running&#x60;&#x60; to &#x60;&#x60;done&#x60;&#x60; or &#x60;&#x60;failed&#x60;&#x60;.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        String traceId = "traceId_example"; // String | 
        try {
            ApiResponse<DeepAnalysisApiResponse> response = apiInstance.tracerFeedIssuesRootCauseListWithHttpInfo(clusterId, traceId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesRootCauseList");
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
| **clusterId** | **String**|  | |
| **traceId** | **String**|  | |

### Return type

ApiResponse<[**DeepAnalysisApiResponse**](DeepAnalysisApiResponse.md)>


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## tracerFeedIssuesSidebarList

> FeedSidebarApiResponse tracerFeedIssuesSidebarList(clusterId, traceId)

GET /tracer/feed/issues/{cluster_id}/sidebar/

Accepts an optional &#x60;&#x60;?trace_id&#x3D;&#x60;&#x60; query param. When present, the trace-level sections (AI Metadata + Evaluations) are computed for that trace instead of the cluster&#39;s latest, keeping the sidebar in sync with the Overview tab&#39;s trace selection.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        String traceId = "traceId_example"; // String | 
        try {
            FeedSidebarApiResponse result = apiInstance.tracerFeedIssuesSidebarList(clusterId, traceId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesSidebarList");
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
| **clusterId** | **String**|  | |
| **traceId** | **String**|  | [optional] |

### Return type

[**FeedSidebarApiResponse**](FeedSidebarApiResponse.md)


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## tracerFeedIssuesSidebarListWithHttpInfo

> ApiResponse<FeedSidebarApiResponse> tracerFeedIssuesSidebarList tracerFeedIssuesSidebarListWithHttpInfo(clusterId, traceId)

GET /tracer/feed/issues/{cluster_id}/sidebar/

Accepts an optional &#x60;&#x60;?trace_id&#x3D;&#x60;&#x60; query param. When present, the trace-level sections (AI Metadata + Evaluations) are computed for that trace instead of the cluster&#39;s latest, keeping the sidebar in sync with the Overview tab&#39;s trace selection.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        String traceId = "traceId_example"; // String | 
        try {
            ApiResponse<FeedSidebarApiResponse> response = apiInstance.tracerFeedIssuesSidebarListWithHttpInfo(clusterId, traceId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesSidebarList");
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
| **clusterId** | **String**|  | |
| **traceId** | **String**|  | [optional] |

### Return type

ApiResponse<[**FeedSidebarApiResponse**](FeedSidebarApiResponse.md)>


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## tracerFeedIssuesTracesList

> TracesTabApiResponse tracerFeedIssuesTracesList(clusterId, limit, offset)



GET /tracer/feed/issues/{cluster_id}/traces/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        Integer limit = 50; // Integer | 
        Integer offset = 0; // Integer | 
        try {
            TracesTabApiResponse result = apiInstance.tracerFeedIssuesTracesList(clusterId, limit, offset);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesTracesList");
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
| **clusterId** | **String**|  | |
| **limit** | **Integer**|  | [optional] [default to 50] |
| **offset** | **Integer**|  | [optional] [default to 0] |

### Return type

[**TracesTabApiResponse**](TracesTabApiResponse.md)


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## tracerFeedIssuesTracesListWithHttpInfo

> ApiResponse<TracesTabApiResponse> tracerFeedIssuesTracesList tracerFeedIssuesTracesListWithHttpInfo(clusterId, limit, offset)



GET /tracer/feed/issues/{cluster_id}/traces/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        Integer limit = 50; // Integer | 
        Integer offset = 0; // Integer | 
        try {
            ApiResponse<TracesTabApiResponse> response = apiInstance.tracerFeedIssuesTracesListWithHttpInfo(clusterId, limit, offset);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesTracesList");
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
| **clusterId** | **String**|  | |
| **limit** | **Integer**|  | [optional] [default to 50] |
| **offset** | **Integer**|  | [optional] [default to 0] |

### Return type

ApiResponse<[**TracesTabApiResponse**](TracesTabApiResponse.md)>


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## tracerFeedIssuesTrendsList

> TrendsTabApiResponse tracerFeedIssuesTrendsList(clusterId, days)



GET /tracer/feed/issues/{cluster_id}/trends/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        Integer days = 14; // Integer | 
        try {
            TrendsTabApiResponse result = apiInstance.tracerFeedIssuesTrendsList(clusterId, days);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesTrendsList");
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
| **clusterId** | **String**|  | |
| **days** | **Integer**|  | [optional] [default to 14] |

### Return type

[**TrendsTabApiResponse**](TrendsTabApiResponse.md)


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## tracerFeedIssuesTrendsListWithHttpInfo

> ApiResponse<TrendsTabApiResponse> tracerFeedIssuesTrendsList tracerFeedIssuesTrendsListWithHttpInfo(clusterId, days)



GET /tracer/feed/issues/{cluster_id}/trends/

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String clusterId = "clusterId_example"; // String | 
        Integer days = 14; // Integer | 
        try {
            ApiResponse<TrendsTabApiResponse> response = apiInstance.tracerFeedIssuesTrendsListWithHttpInfo(clusterId, days);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerFeedIssuesTrendsList");
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
| **clusterId** | **String**|  | |
| **days** | **Integer**|  | [optional] [default to 14] |

### Return type

ApiResponse<[**TrendsTabApiResponse**](TrendsTabApiResponse.md)>


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
| **403** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceAgentGraph

> TracerTraceList200Response tracerTraceAgentGraph(projectId, page, limit, filters)

Return the aggregate agent graph for a project.

Computes nodes (distinct span types/names) and edges (parent→child transitions) across all traces in the given time window.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String filters = "[]"; // String | 
        try {
            TracerTraceList200Response result = apiInstance.tracerTraceAgentGraph(projectId, page, limit, filters);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAgentGraph");
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
| **projectId** | **UUID**|  | |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **filters** | **String**|  | [optional] [default to []] |

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceAgentGraphWithHttpInfo

> ApiResponse<TracerTraceList200Response> tracerTraceAgentGraph tracerTraceAgentGraphWithHttpInfo(projectId, page, limit, filters)

Return the aggregate agent graph for a project.

Computes nodes (distinct span types/names) and edges (parent→child transitions) across all traces in the given time window.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UUID projectId = UUID.randomUUID(); // UUID | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String filters = "[]"; // String | 
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.tracerTraceAgentGraphWithHttpInfo(projectId, page, limit, filters);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAgentGraph");
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
| **projectId** | **UUID**|  | |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **filters** | **String**|  | [optional] [default to []] |

### Return type

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceAnnotationCreate

> GetTraceAnnotation tracerTraceAnnotationCreate(getTraceAnnotation)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        GetTraceAnnotation getTraceAnnotation = new GetTraceAnnotation(); // GetTraceAnnotation | 
        try {
            GetTraceAnnotation result = apiInstance.tracerTraceAnnotationCreate(getTraceAnnotation);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationCreate");
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
| **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md)|  | |

### Return type

[**GetTraceAnnotation**](GetTraceAnnotation.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceAnnotationCreateWithHttpInfo

> ApiResponse<GetTraceAnnotation> tracerTraceAnnotationCreate tracerTraceAnnotationCreateWithHttpInfo(getTraceAnnotation)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        GetTraceAnnotation getTraceAnnotation = new GetTraceAnnotation(); // GetTraceAnnotation | 
        try {
            ApiResponse<GetTraceAnnotation> response = apiInstance.tracerTraceAnnotationCreateWithHttpInfo(getTraceAnnotation);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationCreate");
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
| **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md)|  | |

### Return type

ApiResponse<[**GetTraceAnnotation**](GetTraceAnnotation.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceAnnotationDelete

> void tracerTraceAnnotationDelete(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            apiInstance.tracerTraceAnnotationDelete(id);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationDelete");
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
| **0** | Default error response |  -  |

## tracerTraceAnnotationDeleteWithHttpInfo

> ApiResponse<Void> tracerTraceAnnotationDelete tracerTraceAnnotationDeleteWithHttpInfo(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            ApiResponse<Void> response = apiInstance.tracerTraceAnnotationDeleteWithHttpInfo(id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationDelete");
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
| **0** | Default error response |  -  |


## tracerTraceAnnotationGetAnnotationValues

> GetTraceAnnotationValuesResponse tracerTraceAnnotationGetAnnotationValues(page, limit, observationSpanId, traceId, annotators, excludeAnnotators)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String observationSpanId = "observationSpanId_example"; // String | 
        UUID traceId = UUID.randomUUID(); // UUID | 
        String annotators = "annotators_example"; // String | 
        String excludeAnnotators = "excludeAnnotators_example"; // String | 
        try {
            GetTraceAnnotationValuesResponse result = apiInstance.tracerTraceAnnotationGetAnnotationValues(page, limit, observationSpanId, traceId, annotators, excludeAnnotators);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationGetAnnotationValues");
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
| **observationSpanId** | **String**|  | [optional] |
| **traceId** | **UUID**|  | [optional] |
| **annotators** | **String**|  | [optional] |
| **excludeAnnotators** | **String**|  | [optional] |

### Return type

[**GetTraceAnnotationValuesResponse**](GetTraceAnnotationValuesResponse.md)


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

## tracerTraceAnnotationGetAnnotationValuesWithHttpInfo

> ApiResponse<GetTraceAnnotationValuesResponse> tracerTraceAnnotationGetAnnotationValues tracerTraceAnnotationGetAnnotationValuesWithHttpInfo(page, limit, observationSpanId, traceId, annotators, excludeAnnotators)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String observationSpanId = "observationSpanId_example"; // String | 
        UUID traceId = UUID.randomUUID(); // UUID | 
        String annotators = "annotators_example"; // String | 
        String excludeAnnotators = "excludeAnnotators_example"; // String | 
        try {
            ApiResponse<GetTraceAnnotationValuesResponse> response = apiInstance.tracerTraceAnnotationGetAnnotationValuesWithHttpInfo(page, limit, observationSpanId, traceId, annotators, excludeAnnotators);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationGetAnnotationValues");
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
| **observationSpanId** | **String**|  | [optional] |
| **traceId** | **UUID**|  | [optional] |
| **annotators** | **String**|  | [optional] |
| **excludeAnnotators** | **String**|  | [optional] |

### Return type

ApiResponse<[**GetTraceAnnotationValuesResponse**](GetTraceAnnotationValuesResponse.md)>


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


## tracerTraceAnnotationList

> TracerTraceAnnotationList200Response tracerTraceAnnotationList(page, limit)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceAnnotationList200Response result = apiInstance.tracerTraceAnnotationList(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationList");
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

[**TracerTraceAnnotationList200Response**](TracerTraceAnnotationList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceAnnotationListWithHttpInfo

> ApiResponse<TracerTraceAnnotationList200Response> tracerTraceAnnotationList tracerTraceAnnotationListWithHttpInfo(page, limit)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceAnnotationList200Response> response = apiInstance.tracerTraceAnnotationListWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationList");
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

ApiResponse<[**TracerTraceAnnotationList200Response**](TracerTraceAnnotationList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceAnnotationPartialUpdate

> GetTraceAnnotation tracerTraceAnnotationPartialUpdate(id, getTraceAnnotation)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        GetTraceAnnotation getTraceAnnotation = new GetTraceAnnotation(); // GetTraceAnnotation | 
        try {
            GetTraceAnnotation result = apiInstance.tracerTraceAnnotationPartialUpdate(id, getTraceAnnotation);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationPartialUpdate");
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
| **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md)|  | |

### Return type

[**GetTraceAnnotation**](GetTraceAnnotation.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceAnnotationPartialUpdateWithHttpInfo

> ApiResponse<GetTraceAnnotation> tracerTraceAnnotationPartialUpdate tracerTraceAnnotationPartialUpdateWithHttpInfo(id, getTraceAnnotation)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        GetTraceAnnotation getTraceAnnotation = new GetTraceAnnotation(); // GetTraceAnnotation | 
        try {
            ApiResponse<GetTraceAnnotation> response = apiInstance.tracerTraceAnnotationPartialUpdateWithHttpInfo(id, getTraceAnnotation);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationPartialUpdate");
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
| **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md)|  | |

### Return type

ApiResponse<[**GetTraceAnnotation**](GetTraceAnnotation.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceAnnotationRead

> GetTraceAnnotation tracerTraceAnnotationRead(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            GetTraceAnnotation result = apiInstance.tracerTraceAnnotationRead(id);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationRead");
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

### Return type

[**GetTraceAnnotation**](GetTraceAnnotation.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceAnnotationReadWithHttpInfo

> ApiResponse<GetTraceAnnotation> tracerTraceAnnotationRead tracerTraceAnnotationReadWithHttpInfo(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            ApiResponse<GetTraceAnnotation> response = apiInstance.tracerTraceAnnotationReadWithHttpInfo(id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationRead");
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

### Return type

ApiResponse<[**GetTraceAnnotation**](GetTraceAnnotation.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceAnnotationUpdate

> GetTraceAnnotation tracerTraceAnnotationUpdate(id, getTraceAnnotation)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        GetTraceAnnotation getTraceAnnotation = new GetTraceAnnotation(); // GetTraceAnnotation | 
        try {
            GetTraceAnnotation result = apiInstance.tracerTraceAnnotationUpdate(id, getTraceAnnotation);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationUpdate");
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
| **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md)|  | |

### Return type

[**GetTraceAnnotation**](GetTraceAnnotation.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceAnnotationUpdateWithHttpInfo

> ApiResponse<GetTraceAnnotation> tracerTraceAnnotationUpdate tracerTraceAnnotationUpdateWithHttpInfo(id, getTraceAnnotation)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        GetTraceAnnotation getTraceAnnotation = new GetTraceAnnotation(); // GetTraceAnnotation | 
        try {
            ApiResponse<GetTraceAnnotation> response = apiInstance.tracerTraceAnnotationUpdateWithHttpInfo(id, getTraceAnnotation);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceAnnotationUpdate");
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
| **getTraceAnnotation** | [**GetTraceAnnotation**](GetTraceAnnotation.md)|  | |

### Return type

ApiResponse<[**GetTraceAnnotation**](GetTraceAnnotation.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceBulkCreate

> Trace tracerTraceBulkCreate(trace)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Trace trace = new Trace(); // Trace | 
        try {
            Trace result = apiInstance.tracerTraceBulkCreate(trace);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceBulkCreate");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

[**Trace**](Trace.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceBulkCreateWithHttpInfo

> ApiResponse<Trace> tracerTraceBulkCreate tracerTraceBulkCreateWithHttpInfo(trace)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Trace trace = new Trace(); // Trace | 
        try {
            ApiResponse<Trace> response = apiInstance.tracerTraceBulkCreateWithHttpInfo(trace);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceBulkCreate");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

ApiResponse<[**Trace**](Trace.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceCompareTraces

> Trace tracerTraceCompareTraces(trace)



Compare traces across project versions with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Trace trace = new Trace(); // Trace | 
        try {
            Trace result = apiInstance.tracerTraceCompareTraces(trace);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceCompareTraces");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

[**Trace**](Trace.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceCompareTracesWithHttpInfo

> ApiResponse<Trace> tracerTraceCompareTraces tracerTraceCompareTracesWithHttpInfo(trace)



Compare traces across project versions with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Trace trace = new Trace(); // Trace | 
        try {
            ApiResponse<Trace> response = apiInstance.tracerTraceCompareTracesWithHttpInfo(trace);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceCompareTraces");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

ApiResponse<[**Trace**](Trace.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceCreate

> Trace tracerTraceCreate(trace)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Trace trace = new Trace(); // Trace | 
        try {
            Trace result = apiInstance.tracerTraceCreate(trace);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceCreate");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

[**Trace**](Trace.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceCreateWithHttpInfo

> ApiResponse<Trace> tracerTraceCreate tracerTraceCreateWithHttpInfo(trace)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Trace trace = new Trace(); // Trace | 
        try {
            ApiResponse<Trace> response = apiInstance.tracerTraceCreateWithHttpInfo(trace);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceCreate");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

ApiResponse<[**Trace**](Trace.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceDelete

> void tracerTraceDelete(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            apiInstance.tracerTraceDelete(id);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceDelete");
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
| **0** | Default error response |  -  |

## tracerTraceDeleteWithHttpInfo

> ApiResponse<Void> tracerTraceDelete tracerTraceDeleteWithHttpInfo(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            ApiResponse<Void> response = apiInstance.tracerTraceDeleteWithHttpInfo(id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceDelete");
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
| **0** | Default error response |  -  |


## tracerTraceGetEvalNames

> TracerTraceList200Response tracerTraceGetEvalNames(page, limit)



Fetch all evaluation template names.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceList200Response result = apiInstance.tracerTraceGetEvalNames(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceGetEvalNames");
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

[**TracerTraceList200Response**](TracerTraceList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceGetEvalNamesWithHttpInfo

> ApiResponse<TracerTraceList200Response> tracerTraceGetEvalNames tracerTraceGetEvalNamesWithHttpInfo(page, limit)



Fetch all evaluation template names.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.tracerTraceGetEvalNamesWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceGetEvalNames");
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

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceGetTraceExportData

> TracerTraceList200Response tracerTraceGetTraceExportData(page, limit)



Export traces filtered by project ID with optimized queries. Auto-detects voice/conversation projects and exports voice-specific fields.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceList200Response result = apiInstance.tracerTraceGetTraceExportData(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceGetTraceExportData");
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

[**TracerTraceList200Response**](TracerTraceList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceGetTraceExportDataWithHttpInfo

> ApiResponse<TracerTraceList200Response> tracerTraceGetTraceExportData tracerTraceGetTraceExportDataWithHttpInfo(page, limit)



Export traces filtered by project ID with optimized queries. Auto-detects voice/conversation projects and exports voice-specific fields.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.tracerTraceGetTraceExportDataWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceGetTraceExportData");
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

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceGetTraceIdByIndex

> TracerTraceList200Response tracerTraceGetTraceIdByIndex(traceId, projectVersionId, page, limit, filters)



Get the previous and next trace id by index using efficient database queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UUID traceId = UUID.randomUUID(); // UUID | 
        UUID projectVersionId = UUID.randomUUID(); // UUID | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String filters = "[]"; // String | 
        try {
            TracerTraceList200Response result = apiInstance.tracerTraceGetTraceIdByIndex(traceId, projectVersionId, page, limit, filters);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceGetTraceIdByIndex");
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
| **traceId** | **UUID**|  | |
| **projectVersionId** | **UUID**|  | |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **filters** | **String**|  | [optional] [default to []] |

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceGetTraceIdByIndexWithHttpInfo

> ApiResponse<TracerTraceList200Response> tracerTraceGetTraceIdByIndex tracerTraceGetTraceIdByIndexWithHttpInfo(traceId, projectVersionId, page, limit, filters)



Get the previous and next trace id by index using efficient database queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UUID traceId = UUID.randomUUID(); // UUID | 
        UUID projectVersionId = UUID.randomUUID(); // UUID | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String filters = "[]"; // String | 
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.tracerTraceGetTraceIdByIndexWithHttpInfo(traceId, projectVersionId, page, limit, filters);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceGetTraceIdByIndex");
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
| **traceId** | **UUID**|  | |
| **projectVersionId** | **UUID**|  | |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **filters** | **String**|  | [optional] [default to []] |

### Return type

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceGetTraceIdByIndexObserve

> TracerTraceList200Response tracerTraceGetTraceIdByIndexObserve(traceId, projectId, page, limit, filters)



Get the previous and next trace id by index.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UUID traceId = UUID.randomUUID(); // UUID | 
        UUID projectId = UUID.randomUUID(); // UUID | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String filters = "[]"; // String | 
        try {
            TracerTraceList200Response result = apiInstance.tracerTraceGetTraceIdByIndexObserve(traceId, projectId, page, limit, filters);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceGetTraceIdByIndexObserve");
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
| **traceId** | **UUID**|  | |
| **projectId** | **UUID**|  | |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **filters** | **String**|  | [optional] [default to []] |

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceGetTraceIdByIndexObserveWithHttpInfo

> ApiResponse<TracerTraceList200Response> tracerTraceGetTraceIdByIndexObserve tracerTraceGetTraceIdByIndexObserveWithHttpInfo(traceId, projectId, page, limit, filters)



Get the previous and next trace id by index.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UUID traceId = UUID.randomUUID(); // UUID | 
        UUID projectId = UUID.randomUUID(); // UUID | 
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        String filters = "[]"; // String | 
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.tracerTraceGetTraceIdByIndexObserveWithHttpInfo(traceId, projectId, page, limit, filters);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceGetTraceIdByIndexObserve");
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
| **traceId** | **UUID**|  | |
| **projectId** | **UUID**|  | |
| **page** | **Integer**| A page number within the paginated result set. | [optional] |
| **limit** | **Integer**| Number of results to return per page. | [optional] |
| **filters** | **String**|  | [optional] [default to []] |

### Return type

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceList

> TracerTraceList200Response tracerTraceList(page, limit)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceList200Response result = apiInstance.tracerTraceList(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceList");
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

[**TracerTraceList200Response**](TracerTraceList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceListWithHttpInfo

> ApiResponse<TracerTraceList200Response> tracerTraceList tracerTraceListWithHttpInfo(page, limit)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.tracerTraceListWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceList");
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

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceListTracesOfSession

> TracerTraceList200Response tracerTraceListTracesOfSession(page, limit, projectId, projectVersionId, sessionId, filters, pageNumber, pageSize, interval)



List traces filtered by project ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        UUID projectId = UUID.randomUUID(); // UUID | 
        UUID projectVersionId = UUID.randomUUID(); // UUID | 
        UUID sessionId = UUID.randomUUID(); // UUID | 
        String filters = "[]"; // String | 
        Integer pageNumber = 0; // Integer | 
        Integer pageSize = 30; // Integer | 
        String interval = "interval_example"; // String | 
        try {
            TracerTraceList200Response result = apiInstance.tracerTraceListTracesOfSession(page, limit, projectId, projectVersionId, sessionId, filters, pageNumber, pageSize, interval);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceListTracesOfSession");
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
| **projectId** | **UUID**|  | [optional] |
| **projectVersionId** | **UUID**|  | [optional] |
| **sessionId** | **UUID**|  | [optional] |
| **filters** | **String**|  | [optional] [default to []] |
| **pageNumber** | **Integer**|  | [optional] [default to 0] |
| **pageSize** | **Integer**|  | [optional] [default to 30] |
| **interval** | **String**|  | [optional] |

### Return type

[**TracerTraceList200Response**](TracerTraceList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceListTracesOfSessionWithHttpInfo

> ApiResponse<TracerTraceList200Response> tracerTraceListTracesOfSession tracerTraceListTracesOfSessionWithHttpInfo(page, limit, projectId, projectVersionId, sessionId, filters, pageNumber, pageSize, interval)



List traces filtered by project ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        UUID projectId = UUID.randomUUID(); // UUID | 
        UUID projectVersionId = UUID.randomUUID(); // UUID | 
        UUID sessionId = UUID.randomUUID(); // UUID | 
        String filters = "[]"; // String | 
        Integer pageNumber = 0; // Integer | 
        Integer pageSize = 30; // Integer | 
        String interval = "interval_example"; // String | 
        try {
            ApiResponse<TracerTraceList200Response> response = apiInstance.tracerTraceListTracesOfSessionWithHttpInfo(page, limit, projectId, projectVersionId, sessionId, filters, pageNumber, pageSize, interval);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceListTracesOfSession");
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
| **projectId** | **UUID**|  | [optional] |
| **projectVersionId** | **UUID**|  | [optional] |
| **sessionId** | **UUID**|  | [optional] |
| **filters** | **String**|  | [optional] [default to []] |
| **pageNumber** | **Integer**|  | [optional] [default to 0] |
| **pageSize** | **Integer**|  | [optional] [default to 30] |
| **interval** | **String**|  | [optional] |

### Return type

ApiResponse<[**TracerTraceList200Response**](TracerTraceList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTracePartialUpdate

> Trace tracerTracePartialUpdate(id, trace)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        Trace trace = new Trace(); // Trace | 
        try {
            Trace result = apiInstance.tracerTracePartialUpdate(id, trace);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTracePartialUpdate");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

[**Trace**](Trace.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTracePartialUpdateWithHttpInfo

> ApiResponse<Trace> tracerTracePartialUpdate tracerTracePartialUpdateWithHttpInfo(id, trace)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        Trace trace = new Trace(); // Trace | 
        try {
            ApiResponse<Trace> response = apiInstance.tracerTracePartialUpdateWithHttpInfo(id, trace);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTracePartialUpdate");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

ApiResponse<[**Trace**](Trace.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceSessionCreate

> TraceSession tracerTraceSessionCreate(traceSession)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        TraceSession traceSession = new TraceSession(); // TraceSession | 
        try {
            TraceSession result = apiInstance.tracerTraceSessionCreate(traceSession);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionCreate");
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
| **traceSession** | [**TraceSession**](TraceSession.md)|  | |

### Return type

[**TraceSession**](TraceSession.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceSessionCreateWithHttpInfo

> ApiResponse<TraceSession> tracerTraceSessionCreate tracerTraceSessionCreateWithHttpInfo(traceSession)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        TraceSession traceSession = new TraceSession(); // TraceSession | 
        try {
            ApiResponse<TraceSession> response = apiInstance.tracerTraceSessionCreateWithHttpInfo(traceSession);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionCreate");
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
| **traceSession** | [**TraceSession**](TraceSession.md)|  | |

### Return type

ApiResponse<[**TraceSession**](TraceSession.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceSessionDelete

> void tracerTraceSessionDelete(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            apiInstance.tracerTraceSessionDelete(id);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionDelete");
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
| **0** | Default error response |  -  |

## tracerTraceSessionDeleteWithHttpInfo

> ApiResponse<Void> tracerTraceSessionDelete tracerTraceSessionDeleteWithHttpInfo(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            ApiResponse<Void> response = apiInstance.tracerTraceSessionDeleteWithHttpInfo(id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionDelete");
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
| **0** | Default error response |  -  |


## tracerTraceSessionEvalLogs

> TraceSession tracerTraceSessionEvalLogs(id)

Session-scoped eval log feed for TracesDrawer&#39;s \&quot;Evals\&quot; tab.

Session-level eval results are walled off from span/trace surfaces by &#x60;&#x60;target_type&#x3D;&#39;session&#39;&#x60;&#x60; — this endpoint is the only place they appear.  Query params:     page (int, 0-indexed, default 0)     page_size (int, default 25, max 100)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            TraceSession result = apiInstance.tracerTraceSessionEvalLogs(id);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionEvalLogs");
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

### Return type

[**TraceSession**](TraceSession.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceSessionEvalLogsWithHttpInfo

> ApiResponse<TraceSession> tracerTraceSessionEvalLogs tracerTraceSessionEvalLogsWithHttpInfo(id)

Session-scoped eval log feed for TracesDrawer&#39;s \&quot;Evals\&quot; tab.

Session-level eval results are walled off from span/trace surfaces by &#x60;&#x60;target_type&#x3D;&#39;session&#39;&#x60;&#x60; — this endpoint is the only place they appear.  Query params:     page (int, 0-indexed, default 0)     page_size (int, default 25, max 100)

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            ApiResponse<TraceSession> response = apiInstance.tracerTraceSessionEvalLogsWithHttpInfo(id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionEvalLogs");
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

### Return type

ApiResponse<[**TraceSession**](TraceSession.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceSessionGetSessionFilterValues

> TracerTraceSessionList200Response tracerTraceSessionGetSessionFilterValues(page, limit)



Return distinct values for a session-level column. Used by the filter panel&#39;s value picker for session-specific fields (session_id, user_id, first_message, etc.).  Query params:     project_id: required     column: canonical session column name, e.g. \&quot;session_id\&quot;     search: optional search substring     page: page number (0-based), default 0     page_size: default 50

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceSessionList200Response result = apiInstance.tracerTraceSessionGetSessionFilterValues(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionGetSessionFilterValues");
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

[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceSessionGetSessionFilterValuesWithHttpInfo

> ApiResponse<TracerTraceSessionList200Response> tracerTraceSessionGetSessionFilterValues tracerTraceSessionGetSessionFilterValuesWithHttpInfo(page, limit)



Return distinct values for a session-level column. Used by the filter panel&#39;s value picker for session-specific fields (session_id, user_id, first_message, etc.).  Query params:     project_id: required     column: canonical session column name, e.g. \&quot;session_id\&quot;     search: optional search substring     page: page number (0-based), default 0     page_size: default 50

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceSessionList200Response> response = apiInstance.tracerTraceSessionGetSessionFilterValuesWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionGetSessionFilterValues");
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

ApiResponse<[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceSessionGetTraceSessionExportData

> TracerTraceSessionList200Response tracerTraceSessionGetTraceSessionExportData(page, limit)



Export traces filtered by project ID and project version ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceSessionList200Response result = apiInstance.tracerTraceSessionGetTraceSessionExportData(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionGetTraceSessionExportData");
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

[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceSessionGetTraceSessionExportDataWithHttpInfo

> ApiResponse<TracerTraceSessionList200Response> tracerTraceSessionGetTraceSessionExportData tracerTraceSessionGetTraceSessionExportDataWithHttpInfo(page, limit)



Export traces filtered by project ID and project version ID with optimized queries.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceSessionList200Response> response = apiInstance.tracerTraceSessionGetTraceSessionExportDataWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionGetTraceSessionExportData");
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

ApiResponse<[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceSessionList

> TracerTraceSessionList200Response tracerTraceSessionList(page, limit)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            TracerTraceSessionList200Response result = apiInstance.tracerTraceSessionList(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionList");
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

[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceSessionListWithHttpInfo

> ApiResponse<TracerTraceSessionList200Response> tracerTraceSessionList tracerTraceSessionListWithHttpInfo(page, limit)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<TracerTraceSessionList200Response> response = apiInstance.tracerTraceSessionListWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionList");
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

ApiResponse<[**TracerTraceSessionList200Response**](TracerTraceSessionList200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceSessionPartialUpdate

> TraceSession tracerTraceSessionPartialUpdate(id, traceSession)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        TraceSession traceSession = new TraceSession(); // TraceSession | 
        try {
            TraceSession result = apiInstance.tracerTraceSessionPartialUpdate(id, traceSession);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionPartialUpdate");
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
| **traceSession** | [**TraceSession**](TraceSession.md)|  | |

### Return type

[**TraceSession**](TraceSession.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceSessionPartialUpdateWithHttpInfo

> ApiResponse<TraceSession> tracerTraceSessionPartialUpdate tracerTraceSessionPartialUpdateWithHttpInfo(id, traceSession)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        TraceSession traceSession = new TraceSession(); // TraceSession | 
        try {
            ApiResponse<TraceSession> response = apiInstance.tracerTraceSessionPartialUpdateWithHttpInfo(id, traceSession);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionPartialUpdate");
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
| **traceSession** | [**TraceSession**](TraceSession.md)|  | |

### Return type

ApiResponse<[**TraceSession**](TraceSession.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceSessionUpdate

> TraceSession tracerTraceSessionUpdate(id, traceSession)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        TraceSession traceSession = new TraceSession(); // TraceSession | 
        try {
            TraceSession result = apiInstance.tracerTraceSessionUpdate(id, traceSession);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionUpdate");
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
| **traceSession** | [**TraceSession**](TraceSession.md)|  | |

### Return type

[**TraceSession**](TraceSession.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceSessionUpdateWithHttpInfo

> ApiResponse<TraceSession> tracerTraceSessionUpdate tracerTraceSessionUpdateWithHttpInfo(id, traceSession)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        TraceSession traceSession = new TraceSession(); // TraceSession | 
        try {
            ApiResponse<TraceSession> response = apiInstance.tracerTraceSessionUpdateWithHttpInfo(id, traceSession);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceSessionUpdate");
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
| **traceSession** | [**TraceSession**](TraceSession.md)|  | |

### Return type

ApiResponse<[**TraceSession**](TraceSession.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerTraceUpdate

> Trace tracerTraceUpdate(id, trace)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        Trace trace = new Trace(); // Trace | 
        try {
            Trace result = apiInstance.tracerTraceUpdate(id, trace);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceUpdate");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

[**Trace**](Trace.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerTraceUpdateWithHttpInfo

> ApiResponse<Trace> tracerTraceUpdate tracerTraceUpdateWithHttpInfo(id, trace)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        Trace trace = new Trace(); // Trace | 
        try {
            ApiResponse<Trace> response = apiInstance.tracerTraceUpdateWithHttpInfo(id, trace);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerTraceUpdate");
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
| **trace** | [**Trace**](Trace.md)|  | |

### Return type

ApiResponse<[**Trace**](Trace.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerUserAlertLogsCreate

> UserAlertMonitorLog tracerUserAlertLogsCreate(userAlertMonitorLog)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UserAlertMonitorLog userAlertMonitorLog = new UserAlertMonitorLog(); // UserAlertMonitorLog | 
        try {
            UserAlertMonitorLog result = apiInstance.tracerUserAlertLogsCreate(userAlertMonitorLog);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertLogsCreate");
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
| **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md)|  | |

### Return type

[**UserAlertMonitorLog**](UserAlertMonitorLog.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |

## tracerUserAlertLogsCreateWithHttpInfo

> ApiResponse<UserAlertMonitorLog> tracerUserAlertLogsCreate tracerUserAlertLogsCreateWithHttpInfo(userAlertMonitorLog)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UserAlertMonitorLog userAlertMonitorLog = new UserAlertMonitorLog(); // UserAlertMonitorLog | 
        try {
            ApiResponse<UserAlertMonitorLog> response = apiInstance.tracerUserAlertLogsCreateWithHttpInfo(userAlertMonitorLog);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertLogsCreate");
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
| **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md)|  | |

### Return type

ApiResponse<[**UserAlertMonitorLog**](UserAlertMonitorLog.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Response |  -  |
| **0** | Default error response |  -  |


## tracerUserAlertLogsDelete

> void tracerUserAlertLogsDelete(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            apiInstance.tracerUserAlertLogsDelete(id);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertLogsDelete");
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
| **0** | Default error response |  -  |

## tracerUserAlertLogsDeleteWithHttpInfo

> ApiResponse<Void> tracerUserAlertLogsDelete tracerUserAlertLogsDeleteWithHttpInfo(id)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        try {
            ApiResponse<Void> response = apiInstance.tracerUserAlertLogsDeleteWithHttpInfo(id);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertLogsDelete");
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
| **0** | Default error response |  -  |


## tracerUserAlertLogsPartialUpdate

> UserAlertMonitorLog tracerUserAlertLogsPartialUpdate(id, userAlertMonitorLog)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        UserAlertMonitorLog userAlertMonitorLog = new UserAlertMonitorLog(); // UserAlertMonitorLog | 
        try {
            UserAlertMonitorLog result = apiInstance.tracerUserAlertLogsPartialUpdate(id, userAlertMonitorLog);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertLogsPartialUpdate");
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
| **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md)|  | |

### Return type

[**UserAlertMonitorLog**](UserAlertMonitorLog.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerUserAlertLogsPartialUpdateWithHttpInfo

> ApiResponse<UserAlertMonitorLog> tracerUserAlertLogsPartialUpdate tracerUserAlertLogsPartialUpdateWithHttpInfo(id, userAlertMonitorLog)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        UserAlertMonitorLog userAlertMonitorLog = new UserAlertMonitorLog(); // UserAlertMonitorLog | 
        try {
            ApiResponse<UserAlertMonitorLog> response = apiInstance.tracerUserAlertLogsPartialUpdateWithHttpInfo(id, userAlertMonitorLog);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertLogsPartialUpdate");
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
| **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md)|  | |

### Return type

ApiResponse<[**UserAlertMonitorLog**](UserAlertMonitorLog.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerUserAlertLogsUpdate

> UserAlertMonitorLog tracerUserAlertLogsUpdate(id, userAlertMonitorLog)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        UserAlertMonitorLog userAlertMonitorLog = new UserAlertMonitorLog(); // UserAlertMonitorLog | 
        try {
            UserAlertMonitorLog result = apiInstance.tracerUserAlertLogsUpdate(id, userAlertMonitorLog);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertLogsUpdate");
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
| **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md)|  | |

### Return type

[**UserAlertMonitorLog**](UserAlertMonitorLog.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerUserAlertLogsUpdateWithHttpInfo

> ApiResponse<UserAlertMonitorLog> tracerUserAlertLogsUpdate tracerUserAlertLogsUpdateWithHttpInfo(id, userAlertMonitorLog)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        UserAlertMonitorLog userAlertMonitorLog = new UserAlertMonitorLog(); // UserAlertMonitorLog | 
        try {
            ApiResponse<UserAlertMonitorLog> response = apiInstance.tracerUserAlertLogsUpdateWithHttpInfo(id, userAlertMonitorLog);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertLogsUpdate");
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
| **userAlertMonitorLog** | [**UserAlertMonitorLog**](UserAlertMonitorLog.md)|  | |

### Return type

ApiResponse<[**UserAlertMonitorLog**](UserAlertMonitorLog.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerUserAlertsDuplicate

> UserAlertMonitorDuplicateResponse tracerUserAlertsDuplicate(userAlertMonitorDuplicate)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UserAlertMonitorDuplicate userAlertMonitorDuplicate = new UserAlertMonitorDuplicate(); // UserAlertMonitorDuplicate | 
        try {
            UserAlertMonitorDuplicateResponse result = apiInstance.tracerUserAlertsDuplicate(userAlertMonitorDuplicate);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertsDuplicate");
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
| **userAlertMonitorDuplicate** | [**UserAlertMonitorDuplicate**](UserAlertMonitorDuplicate.md)|  | |

### Return type

[**UserAlertMonitorDuplicateResponse**](UserAlertMonitorDuplicateResponse.md)


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

## tracerUserAlertsDuplicateWithHttpInfo

> ApiResponse<UserAlertMonitorDuplicateResponse> tracerUserAlertsDuplicate tracerUserAlertsDuplicateWithHttpInfo(userAlertMonitorDuplicate)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        UserAlertMonitorDuplicate userAlertMonitorDuplicate = new UserAlertMonitorDuplicate(); // UserAlertMonitorDuplicate | 
        try {
            ApiResponse<UserAlertMonitorDuplicateResponse> response = apiInstance.tracerUserAlertsDuplicateWithHttpInfo(userAlertMonitorDuplicate);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertsDuplicate");
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
| **userAlertMonitorDuplicate** | [**UserAlertMonitorDuplicate**](UserAlertMonitorDuplicate.md)|  | |

### Return type

ApiResponse<[**UserAlertMonitorDuplicateResponse**](UserAlertMonitorDuplicateResponse.md)>


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


## tracerUserAlertsListMonitors

> ListAlerts200Response tracerUserAlertsListMonitors(page, limit)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ListAlerts200Response result = apiInstance.tracerUserAlertsListMonitors(page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertsListMonitors");
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

[**ListAlerts200Response**](ListAlerts200Response.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerUserAlertsListMonitorsWithHttpInfo

> ApiResponse<ListAlerts200Response> tracerUserAlertsListMonitors tracerUserAlertsListMonitorsWithHttpInfo(page, limit)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        Integer page = 56; // Integer | A page number within the paginated result set.
        Integer limit = 56; // Integer | Number of results to return per page.
        try {
            ApiResponse<ListAlerts200Response> response = apiInstance.tracerUserAlertsListMonitorsWithHttpInfo(page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertsListMonitors");
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

ApiResponse<[**ListAlerts200Response**](ListAlerts200Response.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerUserAlertsUpdate

> UserAlertMonitor tracerUserAlertsUpdate(id, userAlertMonitor)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        UserAlertMonitor userAlertMonitor = new UserAlertMonitor(); // UserAlertMonitor | 
        try {
            UserAlertMonitor result = apiInstance.tracerUserAlertsUpdate(id, userAlertMonitor);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertsUpdate");
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
| **userAlertMonitor** | [**UserAlertMonitor**](UserAlertMonitor.md)|  | |

### Return type

[**UserAlertMonitor**](UserAlertMonitor.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |

## tracerUserAlertsUpdateWithHttpInfo

> ApiResponse<UserAlertMonitor> tracerUserAlertsUpdate tracerUserAlertsUpdateWithHttpInfo(id, userAlertMonitor)





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        String id = "id_example"; // String | 
        UserAlertMonitor userAlertMonitor = new UserAlertMonitor(); // UserAlertMonitor | 
        try {
            ApiResponse<UserAlertMonitor> response = apiInstance.tracerUserAlertsUpdateWithHttpInfo(id, userAlertMonitor);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUserAlertsUpdate");
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
| **userAlertMonitor** | [**UserAlertMonitor**](UserAlertMonitor.md)|  | |

### Return type

ApiResponse<[**UserAlertMonitor**](UserAlertMonitor.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Response |  -  |
| **0** | Default error response |  -  |


## tracerUsersGetCodeExampleList

> UserCodeExampleResponse tracerUsersGetCodeExampleList()





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        try {
            UserCodeExampleResponse result = apiInstance.tracerUsersGetCodeExampleList();
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUsersGetCodeExampleList");
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

[**UserCodeExampleResponse**](UserCodeExampleResponse.md)


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

## tracerUsersGetCodeExampleListWithHttpInfo

> ApiResponse<UserCodeExampleResponse> tracerUsersGetCodeExampleList tracerUsersGetCodeExampleListWithHttpInfo()





### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.TracerApi;

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

        TracerApi apiInstance = new TracerApi(defaultClient);
        try {
            ApiResponse<UserCodeExampleResponse> response = apiInstance.tracerUsersGetCodeExampleListWithHttpInfo();
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling TracerApi#tracerUsersGetCodeExampleList");
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

ApiResponse<[**UserCodeExampleResponse**](UserCodeExampleResponse.md)>


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

