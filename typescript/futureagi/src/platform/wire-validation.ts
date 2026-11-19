import Ajv, { type ValidateFunction } from "ajv";
import { definitions } from "./_wireDefinitions";
import { ResponseValidationError } from "./errors";

// Only loaded for opt-in validation. Swagger formats are annotations, as in
// Python's Draft7Validator without a FormatChecker. Never coerce server values.
const ajv = new Ajv({ strictSchema: false, validateFormats: false, ownProperties: true });
const validators = new Map<string, ValidateFunction>();

export function validateResponse(operation: string, model: string, value: unknown): void {
  let validate = validators.get(model);
  if (!validate) {
    validate = ajv.compile({ definitions, $ref: `#/definitions/${model}` });
    validators.set(model, validate);
  }
  if (!validate(value)) {
    throw new ResponseValidationError(`${operation}: response violates ${validate.errors?.[0]?.keyword ?? "schema"}`);
  }
}
