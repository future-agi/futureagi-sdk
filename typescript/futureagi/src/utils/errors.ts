/**
 * Base exception for all SDK errors.
 */
class SDKException extends Error {
    public readonly customMessage?: string;
    public readonly cause?: Error;

    constructor(message?: string, cause?: Error) {
        super(message || (cause ? `An SDK error occurred, caused by: ${cause.message}` : 'An unknown error occurred in the SDK.'));
        this.name = this.constructor.name;
        this.customMessage = message;
        this.cause = cause;
        
        // Set the prototype explicitly to maintain instanceof checks
        Object.setPrototypeOf(this, new.target.prototype);
    }

    public getMessage(): string {
        if (this.customMessage) {
            return this.customMessage;
        }
        if (this.cause) {
            return `An SDK error occurred, caused by: ${this.cause.message}`;
        }
        return 'An unknown error occurred in the SDK.';
    }

    public getErrorCode(): string {
        return 'UNKNOWN_SDK_ERROR';
    }

    public toString(): string {
        return `${this.name}(message='${this.getMessage()}', code='${this.getErrorCode()}')`;
    }
}

/**
 * Base exception for all dataset operations.
 */
class DatasetError extends SDKException {
    public getMessage(): string {
        return 'Invalid Dataset Operation.';
    }

    public getErrorCode(): string {
        return 'DATASET_OPERATION_INVALID';
    }
}

/**
 * Raised when a dataset cannot be found.
 */
class DatasetNotFoundError extends DatasetError {
    public getMessage(): string {
        return 'No Existing Dataset Found for Current Dataset Name.';
    }

    public getErrorCode(): string {
        return 'DATASET_NOT_FOUND';
    }
}

/**
 * Raised when authentication fails for dataset operations (e.g., invalid API key).
 */
class DatasetAuthError extends DatasetError {
    public getMessage(): string {
        return 'Invalid Dataset Authentication, please check your API key and Secret key.';
    }

    public getErrorCode(): string {
        return 'DATASET_AUTH_ERROR';
    }
}

/**
 * Raised when input data fails validation.
 */
class DatasetValidationError extends DatasetError {
    public getMessage(): string {
        return 'Invalid Dataset Validation, please check your input data.';
    }

    public getErrorCode(): string {
        return 'DATASET_VALIDATION_ERROR';
    }
}

/**
 * Raised when API rate limits are exceeded.
 */
class RateLimitError extends DatasetError {
    public getMessage(): string {
        return 'Rate Limit Exceeded, please contact FutureAGI support at support@futureagi.com or check your current plan.';
    }

    public getErrorCode(): string {
        return 'RATE_LIMIT_EXCEEDED';
    }
}

/**
 * Raised for server-side errors.
 */
class ServerError extends DatasetError {
    public getMessage(): string {
        return 'Internal Server Error, please contact FutureAGI support at support@futureagi.com.';
    }

    public getErrorCode(): string {
        return 'SERVER_ERROR';
    }
}

/**
 * Raised when the service is temporarily unavailable.
 */
class ServiceUnavailableError extends DatasetError {
    public getMessage(): string {
        return 'Service Unavailable, please try again later.';
    }

    public getErrorCode(): string {
        return 'SERVICE_UNAVAILABLE';
    }
}

/**
 * Raised when required authentication credentials are missing.
 */
class MissingAuthError extends SDKException {
    public readonly missingApiKey: boolean;
    public readonly missingSecretKey: boolean;

    constructor(fiApiKey?: string, fiSecretKey?: string, cause?: Error) {
        super(undefined, cause);
        this.missingApiKey = !fiApiKey;
        this.missingSecretKey = !fiSecretKey;
    }

    public getMessage(): string {
        const missing: string[] = [];
        if (this.missingApiKey) {
            missing.push("'fi_api_key'");
        }
        if (this.missingSecretKey) {
            missing.push("'fi_secret_key'");
        }

        return `FI Client could not obtain credentials. You can pass your fi_api_key and fi_secret_key ` +
               `directly to the FI Client, or you can set environment variables which will be read if the ` +
               `keys are not directly passed. ` +
               `To set the environment variables use the following variable names: \n` +
               ` - ${process.env.FI_API_KEY_NAME || 'FI_API_KEY'} for the api key\n` +
               ` - ${process.env.FI_SECRET_KEY_NAME || 'FI_SECRET_KEY'} for the secret key\n` +
               `Missing: ${missing.join(', ')}`;
    }

    public getErrorCode(): string {
        return 'MISSING_FI_CLIENT_AUTHENTICATION';
    }
}

/**
 * Exception raised when API authentication fails due to invalid credentials.
 */
class InvalidAuthError extends SDKException {
    constructor(message?: string, cause?: Error) {
        super(message || 'Invalid FI Client Authentication, please check your API key and secret key.', cause);
    }

    public getMessage(): string {
        return this.customMessage || 'Invalid FI Client Authentication, please check your API key and secret key.';
    }

    public getErrorCode(): string {
        return 'INVALID_FI_CLIENT_AUTHENTICATION';
    }
}

class TemplateNotFound extends SDKException {
  public readonly templateName: string;

  constructor(templateName: string, message?: string, cause?: Error) {
    super(message || `Template with name '${templateName}' not found.`, cause);
    this.templateName = templateName;
  }

  public getErrorCode(): string {
    return 'TEMPLATE_NOT_FOUND';
  }
}

/**
 * Exception raised when additional headers are invalid.
 */
class InvalidAdditionalHeaders extends SDKException {
    public readonly invalidHeaderNames: string[];

    constructor(invalidHeaders: string[], cause?: Error) {
        super(undefined, cause);
        this.invalidHeaderNames = invalidHeaders;
    }

    public getMessage(): string {
        return `Found invalid additional header, cannot use reserved headers named: ${this.invalidHeaderNames.join(', ')}.`;
    }

    public getErrorCode(): string {
        return 'INVALID_ADDITIONAL_HEADERS';
    }
}

/**
 * Exception raised when the number of embeddings is invalid.
 */
class InvalidNumberOfEmbeddings extends SDKException {
    public readonly numberOfEmbeddings: number;
    public readonly maxEmbeddings: number;

    constructor(numberOfEmbeddings: number, maxEmbeddings: number = 30, cause?: Error) {
        super(undefined, cause);
        this.numberOfEmbeddings = numberOfEmbeddings;
        this.maxEmbeddings = maxEmbeddings;
    }

    public getMessage(): string {
        return `The schema contains ${this.numberOfEmbeddings} different embeddings when a maximum of ${this.maxEmbeddings} is allowed.`;
    }

    public getErrorCode(): string {
        return 'INVALID_NUMBER_OF_EMBEDDINGS';
    }
}

/**
 * Exception raised when the value type is invalid.
 */
class InvalidValueType extends SDKException {
    public readonly valueName: string;
    public readonly value: unknown;
    public readonly correctType: string;

    constructor(valueName: string, value: unknown, correctType: string, cause?: Error) {
        const message = `${valueName} with value ${JSON.stringify(value)} is of type ${typeof value}, but expected from ${correctType}.`;
        super(message, cause);
        this.valueName = valueName;
        this.value = value;
        this.correctType = correctType;
    }

    public getMessage(): string {
        return `${this.valueName} with value ${JSON.stringify(this.value)} is of type ${typeof this.value}, but expected from ${this.correctType}.`;
    }

    public getErrorCode(): string {
        return 'INVALID_VALUE_TYPE';
    }
}

/**
 * Exception raised when the supported type is invalid.
 */
class InvalidSupportedType extends SDKException {
    public readonly valueName: string;
    public readonly value: unknown;
    public readonly correctType: string;

    constructor(valueName: string, value: unknown, correctType: string, cause?: Error) {
        super(undefined, cause);
        this.valueName = valueName;
        this.value = value;
        this.correctType = correctType;
    }

    public getMessage(): string {
        return `${this.valueName} with value ${JSON.stringify(this.value)} is not supported as of now. Supported types/values are: ${this.correctType}.`;
    }

    public getErrorCode(): string {
        return 'UNSUPPORTED_TYPE_OR_VALUE';
    }
}

/**
 * Exception raised when a required key is missing.
 */
class MissingRequiredKey extends SDKException {
    public readonly fieldName: string;
    public readonly missingKey: string;

    constructor(fieldName: string, missingKey: string, cause?: Error) {
        const message = `Missing required key '${missingKey}' in ${fieldName}. Please check your configuration or API documentation.`;
        super(message, cause);
        this.fieldName = fieldName;
        this.missingKey = missingKey;
    }

    public getErrorCode(): string {
        return 'MISSING_REQUIRED_KEY';
    }
}

/**
 * Exception raised when required config for eval template is missing.
 */
class MissingRequiredConfigForEvalTemplate extends SDKException {
    public readonly missingKey: string;
    public readonly evalTemplateName: string;

    constructor(missingKey: string, evalTemplateName: string, cause?: Error) {
        const message = `Missing required config '${missingKey}' for eval template '${evalTemplateName}'.`;
        super(message, cause);
        this.missingKey = missingKey;
        this.evalTemplateName = evalTemplateName;
    }

    public getErrorCode(): string {
        return 'MISSING_EVAL_TEMPLATE_CONFIG';
    }
}

/**
 * Exception raised when a file is not found.
 */
class FileNotFoundException extends SDKException {
    public readonly filePath: string | string[];

    constructor(filePath: string | string[], message?: string, cause?: Error) {
        super(message || FileNotFoundException.generateMessage(filePath), cause);
        this.filePath = filePath;
    }

    private static generateMessage(filePath: string | string[]): string {
        if (Array.isArray(filePath)) {
            const displayPaths = filePath.slice(0, 3);
            let pathsStr = displayPaths.join(', ');
            if (filePath.length > 3) {
                pathsStr += `, and ${filePath.length - 3} more`;
            }
            return `Files not found: ${pathsStr}.`;
        }
        return `File not found: ${filePath}.`;
    }

    public getErrorCode(): string {
        return 'FILE_NOT_FOUND';
    }
}

/**
 * Exception raised when a file type is not supported.
 */
class UnsupportedFileType extends SDKException {
    public readonly fileExt: string;
    public readonly fileName: string;

    constructor(fileExt: string, fileName: string, message?: string, cause?: Error) {
        super(message || `Unsupported file type: '.${fileExt}' for file '${fileName}'.`, cause);
        this.fileExt = fileExt;
        this.fileName = fileName;
    }

    public getErrorCode(): string {
        return 'UNSUPPORTED_FILE_TYPE';
    }
}

/**
 * Exception raised when a template already exists.
 */
class TemplateAlreadyExists extends SDKException {
    public readonly templateName: string;

    constructor(templateName: string, message?: string, cause?: Error) {
        super(message || `Template '${templateName}' already exists. Please use a different name to create a new template.`, cause);
        this.templateName = templateName;
    }

    public getErrorCode(): string {
        return 'TEMPLATE_ALREADY_EXISTS';
    }
}


export {
    SDKException,
    DatasetError,
    DatasetNotFoundError,
    DatasetAuthError,
    DatasetValidationError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
    MissingAuthError,
    InvalidAuthError,
    InvalidAdditionalHeaders,
    InvalidNumberOfEmbeddings,
    InvalidValueType,
    InvalidSupportedType,
    MissingRequiredKey,
    MissingRequiredConfigForEvalTemplate,
    FileNotFoundException,
    UnsupportedFileType,
    TemplateAlreadyExists,
    TemplateNotFound
}
