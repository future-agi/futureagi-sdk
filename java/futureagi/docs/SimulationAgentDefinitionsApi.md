# SimulationAgentDefinitionsApi

All URIs are relative to *https://api.futureagi.com*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createAgentDefinition**](SimulationAgentDefinitionsApi.md#createAgentDefinition) | **POST** /simulate/agent-definitions/create/ |  |
| [**createAgentDefinitionWithHttpInfo**](SimulationAgentDefinitionsApi.md#createAgentDefinitionWithHttpInfo) | **POST** /simulate/agent-definitions/create/ |  |
| [**deleteAgentDefinition**](SimulationAgentDefinitionsApi.md#deleteAgentDefinition) | **DELETE** /simulate/agent-definitions/{agent_id}/delete/ |  |
| [**deleteAgentDefinitionWithHttpInfo**](SimulationAgentDefinitionsApi.md#deleteAgentDefinitionWithHttpInfo) | **DELETE** /simulate/agent-definitions/{agent_id}/delete/ |  |
| [**getAgentDefinition**](SimulationAgentDefinitionsApi.md#getAgentDefinition) | **GET** /simulate/agent-definitions/{agent_id}/ |  |
| [**getAgentDefinitionWithHttpInfo**](SimulationAgentDefinitionsApi.md#getAgentDefinitionWithHttpInfo) | **GET** /simulate/agent-definitions/{agent_id}/ |  |
| [**listAgentDefinitions**](SimulationAgentDefinitionsApi.md#listAgentDefinitions) | **GET** /simulate/agent-definitions/ |  |
| [**listAgentDefinitionsWithHttpInfo**](SimulationAgentDefinitionsApi.md#listAgentDefinitionsWithHttpInfo) | **GET** /simulate/agent-definitions/ |  |
| [**updateAgentDefinition**](SimulationAgentDefinitionsApi.md#updateAgentDefinition) | **PUT** /simulate/agent-definitions/{agent_id}/edit/ |  |
| [**updateAgentDefinitionWithHttpInfo**](SimulationAgentDefinitionsApi.md#updateAgentDefinitionWithHttpInfo) | **PUT** /simulate/agent-definitions/{agent_id}/edit/ |  |



## createAgentDefinition

> AgentDefinitionCreateResponse createAgentDefinition(agentDefinitionCreateRequest)



Create a new agent definition with its first version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        AgentDefinitionCreateRequest agentDefinitionCreateRequest = new AgentDefinitionCreateRequest(); // AgentDefinitionCreateRequest | 
        try {
            AgentDefinitionCreateResponse result = apiInstance.createAgentDefinition(agentDefinitionCreateRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#createAgentDefinition");
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
| **agentDefinitionCreateRequest** | [**AgentDefinitionCreateRequest**](AgentDefinitionCreateRequest.md)|  | |

### Return type

[**AgentDefinitionCreateResponse**](AgentDefinitionCreateResponse.md)


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

## createAgentDefinitionWithHttpInfo

> ApiResponse<AgentDefinitionCreateResponse> createAgentDefinition createAgentDefinitionWithHttpInfo(agentDefinitionCreateRequest)



Create a new agent definition with its first version.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        AgentDefinitionCreateRequest agentDefinitionCreateRequest = new AgentDefinitionCreateRequest(); // AgentDefinitionCreateRequest | 
        try {
            ApiResponse<AgentDefinitionCreateResponse> response = apiInstance.createAgentDefinitionWithHttpInfo(agentDefinitionCreateRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#createAgentDefinition");
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
| **agentDefinitionCreateRequest** | [**AgentDefinitionCreateRequest**](AgentDefinitionCreateRequest.md)|  | |

### Return type

ApiResponse<[**AgentDefinitionCreateResponse**](AgentDefinitionCreateResponse.md)>


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


## deleteAgentDefinition

> AgentDefinitionDeleteResponse deleteAgentDefinition(agentId)



Soft delete an agent definition.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            AgentDefinitionDeleteResponse result = apiInstance.deleteAgentDefinition(agentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#deleteAgentDefinition");
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

[**AgentDefinitionDeleteResponse**](AgentDefinitionDeleteResponse.md)


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

## deleteAgentDefinitionWithHttpInfo

> ApiResponse<AgentDefinitionDeleteResponse> deleteAgentDefinition deleteAgentDefinitionWithHttpInfo(agentId)



Soft delete an agent definition.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            ApiResponse<AgentDefinitionDeleteResponse> response = apiInstance.deleteAgentDefinitionWithHttpInfo(agentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#deleteAgentDefinition");
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

ApiResponse<[**AgentDefinitionDeleteResponse**](AgentDefinitionDeleteResponse.md)>


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


## getAgentDefinition

> AgentDefinitionResponse getAgentDefinition(agentId)



Get details of a specific agent definition with version information.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            AgentDefinitionResponse result = apiInstance.getAgentDefinition(agentId);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#getAgentDefinition");
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

[**AgentDefinitionResponse**](AgentDefinitionResponse.md)


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

## getAgentDefinitionWithHttpInfo

> ApiResponse<AgentDefinitionResponse> getAgentDefinition getAgentDefinitionWithHttpInfo(agentId)



Get details of a specific agent definition with version information.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        try {
            ApiResponse<AgentDefinitionResponse> response = apiInstance.getAgentDefinitionWithHttpInfo(agentId);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#getAgentDefinition");
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

ApiResponse<[**AgentDefinitionResponse**](AgentDefinitionResponse.md)>


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


## listAgentDefinitions

> List<AgentDefinitionListResponse> listAgentDefinitions(search, agentType, agentDefinitionId, page, limit)



Get paginated list of agent definitions for the user&#39;s organization.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        String search = ""; // String | 
        String agentType = "voice"; // String | 
        UUID agentDefinitionId = UUID.randomUUID(); // UUID | 
        Integer page = 1; // Integer | 
        Integer limit = 56; // Integer | 
        try {
            List<AgentDefinitionListResponse> result = apiInstance.listAgentDefinitions(search, agentType, agentDefinitionId, page, limit);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#listAgentDefinitions");
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
| **agentType** | **String**|  | [optional] [enum: voice, text] |
| **agentDefinitionId** | **UUID**|  | [optional] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] |

### Return type

[**List&lt;AgentDefinitionListResponse&gt;**](AgentDefinitionListResponse.md)


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

## listAgentDefinitionsWithHttpInfo

> ApiResponse<List<AgentDefinitionListResponse>> listAgentDefinitions listAgentDefinitionsWithHttpInfo(search, agentType, agentDefinitionId, page, limit)



Get paginated list of agent definitions for the user&#39;s organization.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        String search = ""; // String | 
        String agentType = "voice"; // String | 
        UUID agentDefinitionId = UUID.randomUUID(); // UUID | 
        Integer page = 1; // Integer | 
        Integer limit = 56; // Integer | 
        try {
            ApiResponse<List<AgentDefinitionListResponse>> response = apiInstance.listAgentDefinitionsWithHttpInfo(search, agentType, agentDefinitionId, page, limit);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#listAgentDefinitions");
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
| **agentType** | **String**|  | [optional] [enum: voice, text] |
| **agentDefinitionId** | **UUID**|  | [optional] |
| **page** | **Integer**|  | [optional] [default to 1] |
| **limit** | **Integer**|  | [optional] |

### Return type

ApiResponse<[**List&lt;AgentDefinitionListResponse&gt;**](AgentDefinitionListResponse.md)>


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


## updateAgentDefinition

> AgentDefinitionEditResponse updateAgentDefinition(agentId, agentDefinitionEditRequest)



Update an existing agent definition.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        AgentDefinitionEditRequest agentDefinitionEditRequest = new AgentDefinitionEditRequest(); // AgentDefinitionEditRequest | 
        try {
            AgentDefinitionEditResponse result = apiInstance.updateAgentDefinition(agentId, agentDefinitionEditRequest);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#updateAgentDefinition");
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
| **agentDefinitionEditRequest** | [**AgentDefinitionEditRequest**](AgentDefinitionEditRequest.md)|  | |

### Return type

[**AgentDefinitionEditResponse**](AgentDefinitionEditResponse.md)


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

## updateAgentDefinitionWithHttpInfo

> ApiResponse<AgentDefinitionEditResponse> updateAgentDefinition updateAgentDefinitionWithHttpInfo(agentId, agentDefinitionEditRequest)



Update an existing agent definition.

### Example

```java
// Import classes:
import com.futureagi.sdk.ApiClient;
import com.futureagi.sdk.ApiException;
import com.futureagi.sdk.ApiResponse;
import com.futureagi.sdk.Configuration;
import com.futureagi.sdk.auth.*;
import com.futureagi.sdk.models.*;
import com.futureagi.sdk.api.SimulationAgentDefinitionsApi;

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

        SimulationAgentDefinitionsApi apiInstance = new SimulationAgentDefinitionsApi(defaultClient);
        String agentId = "agentId_example"; // String | 
        AgentDefinitionEditRequest agentDefinitionEditRequest = new AgentDefinitionEditRequest(); // AgentDefinitionEditRequest | 
        try {
            ApiResponse<AgentDefinitionEditResponse> response = apiInstance.updateAgentDefinitionWithHttpInfo(agentId, agentDefinitionEditRequest);
            System.out.println("Status code: " + response.getStatusCode());
            System.out.println("Response headers: " + response.getHeaders());
            System.out.println("Response body: " + response.getData());
        } catch (ApiException e) {
            System.err.println("Exception when calling SimulationAgentDefinitionsApi#updateAgentDefinition");
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
| **agentDefinitionEditRequest** | [**AgentDefinitionEditRequest**](AgentDefinitionEditRequest.md)|  | |

### Return type

ApiResponse<[**AgentDefinitionEditResponse**](AgentDefinitionEditResponse.md)>


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

