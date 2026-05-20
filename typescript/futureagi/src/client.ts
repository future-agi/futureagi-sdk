import type { AxiosResponse } from 'axios';
import { APIKeyAuth, ResponseHandler } from './api/auth';
import type { APIKeyAuthConfig } from './api/auth';
import { HttpMethod } from './api/types';
import type { RequestConfig } from './api/types';
import { ModelTypes } from './datasets/types';
import {
  InvalidSupportedType,
  InvalidValueType,
  MissingRequiredKey,
} from './utils/errors';
import {
  MAX_FUTURE_YEARS_FROM_CURRENT_TIME,
  MAX_PAST_YEARS_FROM_CURRENT_TIME,
} from './utils/constants';
import { Routes } from './utils/routes';

export enum Environments {
  TRAINING = 1,
  VALIDATION = 2,
  PRODUCTION = 3,
  CORPUS = 4,
}

type PrimitiveTagValue = string | boolean | number;
type ConversationPayload = Record<string, any>;

export interface ModelLogOptions {
  modelId: string;
  modelType: ModelTypes;
  environment: Environments;
  modelVersion?: string;
  predictionTimestamp?: number;
  conversation?: ConversationPayload;
  tags?: Record<string, PrimitiveTagValue>;
  timeout?: number;
}

class ClientResponseHandler extends ResponseHandler<Record<string, any>, never> {
  public static _parseSuccess(response: AxiosResponse): Record<string, any> {
    const data = response.data ?? {};
    if (!('status' in data)) {
      return { ...data, status: response.status >= 200 && response.status < 300 ? 'success' : 'error' };
    }
    return data;
  }
}

export class Client extends APIKeyAuth {
  constructor(options: APIKeyAuthConfig = {}) {
    super(options);
  }

  async log({
    modelId,
    modelType,
    environment,
    modelVersion,
    predictionTimestamp,
    conversation,
    tags,
    timeout,
  }: ModelLogOptions): Promise<Record<string, any>> {
    this._validateParams({
      modelId,
      modelType,
      environment,
      modelVersion,
      predictionTimestamp,
      conversation,
      tags,
    });

    return this.request(
      {
        method: HttpMethod.POST,
        url: `${this.baseUrl}/${Routes.log_model}`,
        json: {
          model_id: modelId,
          model_type: modelType,
          environment,
          model_version: modelVersion,
          prediction_timestamp: predictionTimestamp,
          conversation,
          tags,
        },
        timeout,
      } as RequestConfig,
      ClientResponseHandler,
    ) as Promise<Record<string, any>>;
  }

  private _validateParams({
    modelId,
    modelType,
    environment,
    modelVersion,
    predictionTimestamp,
    conversation,
    tags,
  }: Omit<ModelLogOptions, 'timeout'>): void {
    if (typeof modelId !== 'string') {
      throw new InvalidValueType('model_id', modelId, 'string');
    }

    if (!Object.values(ModelTypes).includes(modelType)) {
      throw new InvalidValueType('model_type', modelType, 'ModelTypes');
    }

    if (![ModelTypes.GENERATIVE_LLM, ModelTypes.GENERATIVE_IMAGE].includes(modelType)) {
      throw new InvalidSupportedType(
        'model_type',
        modelType,
        'ModelTypes.GENERATIVE_LLM, ModelTypes.GENERATIVE_IMAGE',
      );
    }

    if (!Object.values(Environments).includes(environment)) {
      throw new InvalidValueType('environment', environment, 'Environments');
    }

    if (modelVersion != null && typeof modelVersion !== 'string') {
      throw new InvalidValueType('model_version', modelVersion, 'string');
    }

    this._validateConversation(conversation);
    this._validateTags(tags);
    this._validateTimestamp(predictionTimestamp);
  }

  private _validateConversation(conversation?: ConversationPayload): void {
    if (conversation == null) return;
    if (typeof conversation !== 'object' || Array.isArray(conversation)) {
      throw new InvalidValueType('conversation', conversation, 'object');
    }
    if (!('chat_history' in conversation) && !('chat_graph' in conversation)) {
      throw new MissingRequiredKey('conversation', '[chat_history, chat_graph]');
    }
    if ('chat_history' in conversation) {
      this._validateChatHistory(conversation.chat_history);
    }
    if ('chat_graph' in conversation) {
      this._validateChatGraph(conversation.chat_graph);
    }
  }

  private _validateChatHistory(chatHistory: any): void {
    if (!Array.isArray(chatHistory)) {
      throw new InvalidValueType("conversation['chat_history']", chatHistory, 'array');
    }
    for (const item of chatHistory) {
      if (typeof item !== 'object' || item == null || Array.isArray(item)) {
        throw new InvalidValueType('chat_history item', item, 'object');
      }
      for (const key of ['role', 'content']) {
        if (!(key in item)) {
          throw new MissingRequiredKey('chat_history item', key);
        }
      }
      if (typeof item.role !== 'string') {
        throw new InvalidValueType('chat_history role', item.role, 'string');
      }
      if (typeof item.content !== 'string') {
        throw new InvalidValueType('chat_history content', item.content, 'string');
      }
    }
  }

  private _validateChatGraph(chatGraph: any): void {
    if (typeof chatGraph !== 'object' || chatGraph == null || Array.isArray(chatGraph)) {
      throw new InvalidValueType("conversation['chat_graph']", chatGraph, 'object');
    }
    for (const key of ['conversation_id', 'nodes']) {
      if (!(key in chatGraph)) {
        throw new MissingRequiredKey('chat_graph', key);
      }
    }
    if (!Array.isArray(chatGraph.nodes)) {
      throw new InvalidValueType("chat_graph['nodes']", chatGraph.nodes, 'array');
    }
    for (const node of chatGraph.nodes) {
      if (!node?.message) {
        throw new MissingRequiredKey('chat_graph node', 'message');
      }
      const message = node.message;
      for (const key of ['id', 'author', 'content', 'context']) {
        if (!(key in message)) {
          throw new MissingRequiredKey('message', key);
        }
      }
      for (const key of ['role', 'metadata']) {
        if (!(key in message.author)) {
          throw new MissingRequiredKey('author', key);
        }
      }
      if (!['assistant', 'user', 'system'].includes(message.author.role)) {
        throw new InvalidValueType('author role', message.author.role, 'one of: assistant, user, system');
      }
      for (const key of ['content_type', 'parts']) {
        if (!(key in message.content)) {
          throw new MissingRequiredKey('content', key);
        }
      }
      if (!Array.isArray(message.content.parts)) {
        throw new InvalidValueType('content parts', message.content.parts, 'array');
      }
    }
  }

  private _validateTags(tags?: Record<string, PrimitiveTagValue>): void {
    if (tags == null) return;
    if (typeof tags !== 'object' || Array.isArray(tags)) {
      throw new InvalidValueType('tags', tags, 'object');
    }
    for (const [key, value] of Object.entries(tags)) {
      if (typeof key !== 'string') {
        throw new InvalidValueType(`tags key '${key}'`, key, 'string');
      }
      if (!['string', 'boolean', 'number'].includes(typeof value)) {
        throw new InvalidValueType(`tags value for key '${key}'`, value, 'string, boolean, or number');
      }
    }
  }

  private _validateTimestamp(predictionTimestamp?: number): void {
    if (predictionTimestamp == null) return;
    if (!Number.isInteger(predictionTimestamp)) {
      throw new InvalidValueType('prediction_timestamp', predictionTimestamp, 'integer');
    }
    const nowSeconds = Math.floor(Date.now() / 1000);
    const minSeconds = nowSeconds - MAX_PAST_YEARS_FROM_CURRENT_TIME * 365 * 24 * 60 * 60;
    const maxSeconds = nowSeconds + MAX_FUTURE_YEARS_FROM_CURRENT_TIME * 365 * 24 * 60 * 60;
    if (predictionTimestamp < minSeconds || predictionTimestamp > maxSeconds) {
      throw new Error(
        `prediction_timestamp: ${predictionTimestamp} is out of range. Must be within ` +
          `${MAX_FUTURE_YEARS_FROM_CURRENT_TIME} year in the future and ` +
          `${MAX_PAST_YEARS_FROM_CURRENT_TIME} years in the past from current time.`,
      );
    }
  }
}

export default Client;
