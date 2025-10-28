export const MIN_PREDICTION_ID_LEN = 1;
export const MAX_PREDICTION_ID_LEN = 128;

// The maximum number of character for tag values
export const MAX_TAG_LENGTH = 20_000;
export const MAX_TAG_LENGTH_TRUNCATION = 1_000;

export const MAX_PAST_YEARS_FROM_CURRENT_TIME = 5;
export const MAX_FUTURE_YEARS_FROM_CURRENT_TIME = 1;

export const MAX_RAW_DATA_CHARACTERS = 50_000;
export const MAX_RAW_DATA_CHARACTERS_TRUNCATION = 5_000;

// The maximum number of embeddings
export const MAX_NUMBER_OF_EMBEDDINGS = 30;
export const MAX_EMBEDDING_DIMENSIONALITY = 20_000;

// Reserved tag columns
export const RESERVED_TAG_COLS: string[] = [];

// Authentication via environment variables
export const SECRET_KEY_ENVVAR_NAME = "FI_SECRET_KEY";
export const API_KEY_ENVVAR_NAME = "FI_API_KEY";

export function get_base_url(): string {
    /**
     * Get the base URL from environment variable at runtime.
     * 
    This ensures that changes to the FI_BASE_URL environment variable
    are picked up even after the module has been imported.
    
    
    Returns:
        str: The base URL for the FutureAGI API
    */
    return process.env.FI_BASE_URL || "https://api.futureagi.com";
}

// Session settings
export const DEFAULT_TIMEOUT = 200;
export const DEFAULT_MAX_WORKERS = 8;
export const DEFAULT_MAX_QUEUE = 5000;
export const PAGE_SIZE = 100;

// Dataset settings
export const DATASET_TEMP_FILE_PREFIX = "tmp_fi_dataset_";
export const DATASET_TEMP_FILE_SUFFIX = ".csv";

// Environment variables specific to the subpackage
export const FI_PROJECT_NAME = "DEFAULT_PROJECT_NAME";
export const FI_PROJECT_VERSION_NAME = "DEFAULT_PROJECT_VERSION_NAME";

export const PREDICTION_SETTINGS = {
    MIN_PREDICTION_ID_LEN,
    MAX_PREDICTION_ID_LEN
};

export const TAG_SETTINGS = {
    MAX_TAG_LENGTH,
    MAX_TAG_LENGTH_TRUNCATION,
    RESERVED_TAG_COLS
};

export const TIME_SETTINGS = {
    MAX_PAST_YEARS_FROM_CURRENT_TIME,
    MAX_FUTURE_YEARS_FROM_CURRENT_TIME
};

export const RAW_DATA_SETTINGS = {
    MAX_RAW_DATA_CHARACTERS,
    MAX_RAW_DATA_CHARACTERS_TRUNCATION
};

export const EMBEDDING_SETTINGS = {
    MAX_NUMBER_OF_EMBEDDINGS,
    MAX_EMBEDDING_DIMENSIONALITY
};

export const AUTH_ENVVAR_NAME = {
    SECRET_KEY: SECRET_KEY_ENVVAR_NAME,
    API_KEY: API_KEY_ENVVAR_NAME
};

export const DEFAULT_SETTINGS = {
    TIMEOUT: DEFAULT_TIMEOUT,
    MAX_WORKERS: DEFAULT_MAX_WORKERS,
    MAX_QUEUE: DEFAULT_MAX_QUEUE,
    PAGE_SIZE
};

export const DATASET_TEMP_FILE = {
    PREFIX: DATASET_TEMP_FILE_PREFIX,
    SUFFIX: DATASET_TEMP_FILE_SUFFIX
};

export const FI_PROJECT = {
    NAME: FI_PROJECT_NAME,
    VERSION_NAME: FI_PROJECT_VERSION_NAME
};
