# ScenariosApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**simulateScenariosAddColumnsCreate**](ScenariosApi.md#simulateScenariosAddColumnsCreate) | **POST** /simulate/scenarios/{scenario_id}/add-columns/ | Add columns to scenario |
| [**simulateScenariosAddColumnsCreateWithHttpInfo**](ScenariosApi.md#simulateScenariosAddColumnsCreateWithHttpInfo) | **POST** /simulate/scenarios/{scenario_id}/add-columns/ | Add columns to scenario |
| [**simulateScenariosAddRowsCreate**](ScenariosApi.md#simulateScenariosAddRowsCreate) | **POST** /simulate/scenarios/{scenario_id}/add-rows/ | Add rows to scenario |
| [**simulateScenariosAddRowsCreateWithHttpInfo**](ScenariosApi.md#simulateScenariosAddRowsCreateWithHttpInfo) | **POST** /simulate/scenarios/{scenario_id}/add-rows/ | Add rows to scenario |
| [**simulateScenariosGetColumnsList**](ScenariosApi.md#simulateScenariosGetColumnsList) | **GET** /simulate/scenarios/get-columns/ | List scenarios |
| [**simulateScenariosGetColumnsListWithHttpInfo**](ScenariosApi.md#simulateScenariosGetColumnsListWithHttpInfo) | **GET** /simulate/scenarios/get-columns/ | List scenarios |
| [**simulateScenariosPromptsUpdate**](ScenariosApi.md#simulateScenariosPromptsUpdate) | **PUT** /simulate/scenarios/{scenario_id}/prompts/ | Edit scenario prompts |
| [**simulateScenariosPromptsUpdateWithHttpInfo**](ScenariosApi.md#simulateScenariosPromptsUpdateWithHttpInfo) | **PUT** /simulate/scenarios/{scenario_id}/prompts/ | Edit scenario prompts |



## simulateScenariosAddColumnsCreate

> ScenarioAddColumnsResponse simulateScenariosAddColumnsCreate(scenarioId, scenarioAddColumnsRequest)

Add columns to scenario

Adds new columns to a scenario&#39;s dataset via Temporal workflow. Returns 202 Accepted.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ScenariosApi;

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

        ScenariosApi apiInstance = new ScenariosApi(defaultClient);
        String scenarioId = "scenarioId_example"; // String | 
        ScenarioAddColumnsRequest scenarioAddColumnsRequest = new ScenarioAddColumnsRequest(); // ScenarioAddColumnsRequest | 
        try {
            ScenarioAddColumnsResponse result = apiInstance.simulateScenariosAddColumnsCreate(scenarioId, scenarioAddColumnsRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ScenariosApi#simulateScenariosAddColumnsCreate");
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
| **scenarioId** | **String**|  | |
| **scenarioAddColumnsRequest** | [**ScenarioAddColumnsRequest**](ScenarioAddColumnsRequest.md)|  | |

### Return type

[**ScenarioAddColumnsResponse**](ScenarioAddColumnsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateScenariosAddColumnsCreateWithHttpInfo

> ApiResponse<ScenarioAddColumnsResponse> simulateScenariosAddColumnsCreate simulateScenariosAddColumnsCreateWithHttpInfo(scenarioId, scenarioAddColumnsRequest)

Add columns to scenario

Adds new columns to a scenario&#39;s dataset via Temporal workflow. Returns 202 Accepted.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ScenariosApi;

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

        ScenariosApi apiInstance = new ScenariosApi(defaultClient);
        String scenarioId = "scenarioId_example"; // String | 
        ScenarioAddColumnsRequest scenarioAddColumnsRequest = new ScenarioAddColumnsRequest(); // ScenarioAddColumnsRequest | 
        try {
            ApiResponse<ScenarioAddColumnsResponse> response = apiInstance.simulateScenariosAddColumnsCreateWithHttpInfo(scenarioId, scenarioAddColumnsRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ScenariosApi#simulateScenariosAddColumnsCreate");
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
| **scenarioId** | **String**|  | |
| **scenarioAddColumnsRequest** | [**ScenarioAddColumnsRequest**](ScenarioAddColumnsRequest.md)|  | |

### Return type

ApiResponse<[**ScenarioAddColumnsResponse**](ScenarioAddColumnsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateScenariosAddRowsCreate

> ScenarioAddRowsResponse simulateScenariosAddRowsCreate(scenarioId, scenarioAddRowsRequest)

Add rows to scenario

Adds new rows to a scenario&#39;s dataset via Temporal workflow. Returns 202 Accepted.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ScenariosApi;

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

        ScenariosApi apiInstance = new ScenariosApi(defaultClient);
        String scenarioId = "scenarioId_example"; // String | 
        ScenarioAddRowsRequest scenarioAddRowsRequest = new ScenarioAddRowsRequest(); // ScenarioAddRowsRequest | 
        try {
            ScenarioAddRowsResponse result = apiInstance.simulateScenariosAddRowsCreate(scenarioId, scenarioAddRowsRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ScenariosApi#simulateScenariosAddRowsCreate");
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
| **scenarioId** | **String**|  | |
| **scenarioAddRowsRequest** | [**ScenarioAddRowsRequest**](ScenarioAddRowsRequest.md)|  | |

### Return type

[**ScenarioAddRowsResponse**](ScenarioAddRowsResponse.md)


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |

## simulateScenariosAddRowsCreateWithHttpInfo

> ApiResponse<ScenarioAddRowsResponse> simulateScenariosAddRowsCreate simulateScenariosAddRowsCreateWithHttpInfo(scenarioId, scenarioAddRowsRequest)

Add rows to scenario

Adds new rows to a scenario&#39;s dataset via Temporal workflow. Returns 202 Accepted.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ScenariosApi;

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

        ScenariosApi apiInstance = new ScenariosApi(defaultClient);
        String scenarioId = "scenarioId_example"; // String | 
        ScenarioAddRowsRequest scenarioAddRowsRequest = new ScenarioAddRowsRequest(); // ScenarioAddRowsRequest | 
        try {
            ApiResponse<ScenarioAddRowsResponse> response = apiInstance.simulateScenariosAddRowsCreateWithHttpInfo(scenarioId, scenarioAddRowsRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ScenariosApi#simulateScenariosAddRowsCreate");
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
| **scenarioId** | **String**|  | |
| **scenarioAddRowsRequest** | [**ScenarioAddRowsRequest**](ScenarioAddRowsRequest.md)|  | |

### Return type

ApiResponse<[**ScenarioAddRowsResponse**](ScenarioAddRowsResponse.md)>


### Authorization

[X-Secret-Key](../README.md#X-Secret-Key), [X-Api-Key](../README.md#X-Api-Key)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Response |  -  |
| **400** | Response |  -  |
| **404** | Response |  -  |
| **500** | Response |  -  |
| **0** | Default error response |  -  |


## simulateScenariosGetColumnsList

> ScenarioListResponse simulateScenariosGetColumnsList(search, agentDefinitionId, agentType, page, limit)

List scenarios

Returns a paginated list of scenarios for the user&#39;s organization.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ScenariosApi;

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

        ScenariosApi apiInstance = new ScenariosApi(defaultClient);
        String search = ""; // String | 
        UUID agentDefinitionId = UUID.randomUUID(); // UUID | 
        String agentType = "agentType_example"; // String | 
        Integer page = 1; // Integer | 
        Integer limit = 56; // Integer | 
        try {
            ScenarioListResponse result = apiInstance.simulateScenariosGetColumnsList(search, agentDefinitionId, agentType, page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ScenariosApi#simulateScenariosGetColumnsList");
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
| **agentDefinitionId** | **UUID**|  | [optional] |
| **agentType** | **String**|  | [optional] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] |

### Return type

[**ScenarioListResponse**](ScenarioListResponse.md)


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

## simulateScenariosGetColumnsListWithHttpInfo

> ApiResponse<ScenarioListResponse> simulateScenariosGetColumnsList simulateScenariosGetColumnsListWithHttpInfo(search, agentDefinitionId, agentType, page, limit)

List scenarios

Returns a paginated list of scenarios for the user&#39;s organization.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ScenariosApi;

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

        ScenariosApi apiInstance = new ScenariosApi(defaultClient);
        String search = ""; // String | 
        UUID agentDefinitionId = UUID.randomUUID(); // UUID | 
        String agentType = "agentType_example"; // String | 
        Integer page = 1; // Integer | 
        Integer limit = 56; // Integer | 
        try {
            ApiResponse<ScenarioListResponse> response = apiInstance.simulateScenariosGetColumnsListWithHttpInfo(search, agentDefinitionId, agentType, page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ScenariosApi#simulateScenariosGetColumnsList");
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
| **agentDefinitionId** | **UUID**|  | [optional] |
| **agentType** | **String**|  | [optional] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] |

### Return type

ApiResponse<[**ScenarioListResponse**](ScenarioListResponse.md)>


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


## simulateScenariosPromptsUpdate

> ScenarioPromptsUpdateResponse simulateScenariosPromptsUpdate(scenarioId, scenarioEditPromptsRequest)

Edit scenario prompts

Updates the simulator agent prompt for a scenario.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ScenariosApi;

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

        ScenariosApi apiInstance = new ScenariosApi(defaultClient);
        String scenarioId = "scenarioId_example"; // String | 
        ScenarioEditPromptsRequest scenarioEditPromptsRequest = new ScenarioEditPromptsRequest(); // ScenarioEditPromptsRequest | 
        try {
            ScenarioPromptsUpdateResponse result = apiInstance.simulateScenariosPromptsUpdate(scenarioId, scenarioEditPromptsRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ScenariosApi#simulateScenariosPromptsUpdate");
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
| **scenarioId** | **String**|  | |
| **scenarioEditPromptsRequest** | [**ScenarioEditPromptsRequest**](ScenarioEditPromptsRequest.md)|  | |

### Return type

[**ScenarioPromptsUpdateResponse**](ScenarioPromptsUpdateResponse.md)


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

## simulateScenariosPromptsUpdateWithHttpInfo

> ApiResponse<ScenarioPromptsUpdateResponse> simulateScenariosPromptsUpdate simulateScenariosPromptsUpdateWithHttpInfo(scenarioId, scenarioEditPromptsRequest)

Edit scenario prompts

Updates the simulator agent prompt for a scenario.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.ScenariosApi;

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

        ScenariosApi apiInstance = new ScenariosApi(defaultClient);
        String scenarioId = "scenarioId_example"; // String | 
        ScenarioEditPromptsRequest scenarioEditPromptsRequest = new ScenarioEditPromptsRequest(); // ScenarioEditPromptsRequest | 
        try {
            ApiResponse<ScenarioPromptsUpdateResponse> response = apiInstance.simulateScenariosPromptsUpdateWithHttpInfo(scenarioId, scenarioEditPromptsRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling ScenariosApi#simulateScenariosPromptsUpdate");
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
| **scenarioId** | **String**|  | |
| **scenarioEditPromptsRequest** | [**ScenarioEditPromptsRequest**](ScenarioEditPromptsRequest.md)|  | |

### Return type

ApiResponse<[**ScenarioPromptsUpdateResponse**](ScenarioPromptsUpdateResponse.md)>


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

