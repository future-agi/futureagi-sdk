import type { Client } from "../generated/openapi/client";
import * as sdk from "../generated/openapi/sdk.gen";
import type * as types from "../generated/openapi/types.gen";
import { coreOptions, coreResult } from "../_resources";
import type { CatalogPageResult } from "../catalog-response-types";

/** The `create` body: one score for one source and label. */
export type ScoreCreateInput = types.CreateScore;
/** Score fields `update` changes. */
export type ScoreUpdate = Partial<types.ScoreWritable>;
/** Score filters; paging controls are not accepted by this endpoint. */
export type ScoreListQuery = types.ModelHubScoresListData["query"];
/** The annotation label `create` body. */
export type AnnotationLabelInput = types.AnnotationsLabelsWritable;
/** Filters and DRF page fields for annotation label `list`. */
export type AnnotationLabelListQuery = types.ModelHubAnnotationsLabelsListData["query"];
/** The kinds of source a score can be attached to. */
export type ScoreSourceType = types.ModelHubScoresForSourceData["query"]["source_type"];

/** Annotation labels can be archived and restored without deleting their scores. */
export class AnnotationLabelsClient {
  constructor(private readonly client: Client) {}
  /** Return a DRF page of labels with results, links, count, total_pages and current_page.
   * List annotation labels (DRF page). Pagination: page (1-based); limit (page size). */
  list(query?: AnnotationLabelListQuery) {
    // FA develop_annotations.py:160,392-400 returns a page; Swagger incorrectly declares an array.
    // Python fi/scores/__init__.py:30-31 and fi/_resources.py:78-80 preserve this same page.
    return coreResult(sdk.modelHubAnnotationsLabelsList(coreOptions(this.client, { query }))) as unknown as Promise<CatalogPageResult<types.AnnotationsLabels>>;
  }
  /** Create an annotation label. */
  create(body: AnnotationLabelInput) {
    return coreResult(sdk.modelHubAnnotationsLabelsCreate(coreOptions(this.client, { body })));
  }
  /** Fetch one annotation label. */
  get(labelId: string) {
    return coreResult(sdk.modelHubAnnotationsLabelsRead(coreOptions(this.client, { path: { id: labelId } })));
  }
  /** Change an annotation label's fields. */
  update(labelId: string, body: Partial<AnnotationLabelInput>) {
    return coreResult(sdk.modelHubAnnotationsLabelsPartialUpdate(coreOptions(this.client, {
      path: { id: labelId }, body: body as AnnotationLabelInput,
    })));
  }
  /** Archive a label; `restore` makes it available again. */
  delete(labelId: string) {
    return coreResult(sdk.modelHubAnnotationsLabelsDelete(coreOptions(this.client, { path: { id: labelId } })));
  }
  /** Restore an archived label. */
  restore(labelId: string) {
    return coreResult(sdk.modelHubAnnotationsLabelsRestore(coreOptions(this.client, { path: { id: labelId }, body: {} })));
  }
}

/** Create, query and update scores on supported annotation sources. */
export class ScoresClient {
  /** Annotation labels that scores refer to. */
  readonly labels: AnnotationLabelsClient;
  constructor(private readonly client: Client) {
    this.labels = new AnnotationLabelsClient(client);
  }
  /** Return a DRF score page including total_pages and current_page.
   * List scores (DRF page). Pagination: no supported paging parameters. The strict list serializer does not admit page or limit; the server returns its default page. */
  list(query?: ScoreListQuery) {
    // FA scores.py:346,379-381 uses ExtendedPageNumberPagination, not Swagger's partial page.
    return coreResult(sdk.modelHubScoresList(coreOptions(this.client, { query }))) as Promise<CatalogPageResult<types.Score>>;
  }
  /** Create one score. */
  create(body: ScoreCreateInput) {
    return coreResult(sdk.modelHubScoresCreate(coreOptions(this.client, { body })));
  }
  /** Create several scores for one source in one request. */
  bulkCreate(body: types.BulkCreateScores) {
    return coreResult(sdk.modelHubScoresBulkCreate(coreOptions(this.client, { body })));
  }
  /** Fetch one score. */
  get(scoreId: string) {
    return coreResult(sdk.modelHubScoresRead(coreOptions(this.client, { path: { id: scoreId } })));
  }
  /** Change a score's value or notes. */
  update(scoreId: string, body: ScoreUpdate) {
    return coreResult(sdk.modelHubScoresPartialUpdate(coreOptions(this.client, { path: { id: scoreId }, body: body as types.ScoreWritable })));
  }
  /** Delete a score. */
  delete(scoreId: string) {
    return coreResult(sdk.modelHubScoresDelete(coreOptions(this.client, { path: { id: scoreId } })));
  }
  /** Return the complete response: scores in `result` and optional `span_notes`. Pagination: no supported paging parameters. */
  forSource(sourceType: ScoreSourceType, sourceId: string, query: Omit<NonNullable<types.ModelHubScoresForSourceData["query"]>, "source_type" | "source_id"> = {}): Promise<types.ScoreForSourceResponse> {
    return coreResult(sdk.modelHubScoresForSource(coreOptions(this.client, {
      query: { ...query, source_type: sourceType, source_id: sourceId },
    })), false);
  }
}
