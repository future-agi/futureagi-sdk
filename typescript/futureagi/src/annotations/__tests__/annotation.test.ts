import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { Annotation } from '../annotation';
import { AnnotationRecord, BulkAnnotationResponse } from '../types';

// Mock the auth and request functionality
jest.mock('../../api/auth');

describe('Annotation', () => {
  let annotationClient: Annotation;
  let mockRequest: jest.MockedFunction<any>;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Create client instance
    annotationClient = new Annotation({
      fiApiKey: 'test-api-key',
      fiSecretKey: 'test-secret-key',
      fiBaseUrl: 'http://localhost:8000',
    });

    // Mock the request method
    mockRequest = jest.fn();
    (annotationClient as any).request = mockRequest;
  });

  describe('logAnnotations', () => {
    it('should successfully log annotations with flat format', async () => {
      // Mock dependencies
      const mockLabels = [
        { id: 'label-1', name: 'quality', type: 'text' },
        { id: 'label-2', name: 'rating', type: 'star' },
      ];
      
      const mockProjects = [
        { id: 'project-1', name: 'Test Project' },
      ];

      const mockResponse: BulkAnnotationResponse = {
        message: 'Bulk annotation completed',
        annotationsCreated: 2,
        annotationsUpdated: 0,
        notesCreated: 1,
        succeededCount: 3,
        errorsCount: 0,
        warningsCount: 0,
      };

      // Setup mocks
      mockRequest
        .mockResolvedValueOnce({ data: mockProjects }) // listProjects
        .mockResolvedValueOnce({ data: { result: mockLabels } }) // getLabels
        .mockResolvedValueOnce({ data: mockLabels }) // getLabels again for second annotation
        .mockResolvedValueOnce({ data: { result: mockResponse } }); // logAnnotations

      const records: AnnotationRecord[] = [
        {
          'context.span_id': 'span-123',
          'annotation.quality.text': 'good response',
          'annotation.rating.rating': 4,
          'annotation.notes': 'Test note',
        },
      ];

      const result = await annotationClient.logAnnotations(records, {
        projectName: 'Test Project',
      });

      expect(result).toEqual(mockResponse);
      expect(mockRequest).toHaveBeenCalledTimes(4);
      
      // Verify the final request to bulk annotation endpoint
      const finalCall = mockRequest.mock.calls[3];
      expect(finalCall[0].url).toContain('tracer/bulk-annotation/');
      expect(finalCall[0].data.records).toHaveLength(1);
      expect(finalCall[0].data.records[0]).toEqual({
        observation_span_id: 'span-123',
        annotations: [
          {
            annotation_label_id: 'label-1',
            value: 'good response',
          },
          {
            annotation_label_id: 'label-2',
            value_float: 4,
          },
        ],
        notes: [{ text: 'Test note' }],
      });
    });

    it('should handle multiple records', async () => {
      const mockLabels = [
        { id: 'label-1', name: 'quality', type: 'text' },
      ];
      
      const mockProjects = [
        { id: 'project-1', name: 'Test Project' },
      ];

      mockRequest
        .mockResolvedValueOnce({ data: mockProjects })
        .mockResolvedValueOnce({ data: { result: mockLabels } })
        .mockResolvedValueOnce({ data: { result: mockLabels } })
        .mockResolvedValueOnce({
          data: {
            result: {
              message: 'Completed',
              annotationsCreated: 2,
              annotationsUpdated: 0,
              notesCreated: 0,
              succeededCount: 2,
              errorsCount: 0,
              warningsCount: 0,
            },
          },
        });

      const records: AnnotationRecord[] = [
        {
          'context.span_id': 'span-1',
          'annotation.quality.text': 'good',
        },
        {
          'context.span_id': 'span-2',
          'annotation.quality.text': 'bad',
        },
      ];

      const result = await annotationClient.logAnnotations(records, {
        projectName: 'Test Project',
      });

      expect(result.annotationsCreated).toBe(2);
      
      // Verify backend format
      const finalCall = mockRequest.mock.calls[3];
      expect(finalCall[0].data.records).toHaveLength(2);
    });

    it('should handle different annotation types', async () => {
      const mockLabels = [
        { id: 'text-label', name: 'comment', type: 'text' },
        { id: 'cat-label', name: 'category', type: 'categorical' },
        { id: 'num-label', name: 'score', type: 'numeric' },
        { id: 'star-label', name: 'rating', type: 'star' },
        { id: 'bool-label', name: 'helpful', type: 'thumbs_up_down' },
      ];

      mockRequest
        .mockResolvedValueOnce({ data: [{ id: 'proj-1', name: 'Test' }] })
        .mockResolvedValueOnce({ data: mockLabels })
        .mockResolvedValueOnce({ data: mockLabels })
        .mockResolvedValueOnce({ data: mockLabels })
        .mockResolvedValueOnce({ data: mockLabels })
        .mockResolvedValueOnce({ data: mockLabels })
        .mockResolvedValueOnce({
          data: {
            message: 'Success',
            annotationsCreated: 5,
            annotationsUpdated: 0,
            notesCreated: 0,
            succeededCount: 5,
            errorsCount: 0,
            warningsCount: 0,
          },
        });

      const records: AnnotationRecord[] = [
        {
          'context.span_id': 'span-123',
          'annotation.comment.text': 'Great work',
          'annotation.category.label': 'positive',
          'annotation.score.score': 8.5,
          'annotation.rating.rating': 5,
          'annotation.helpful.thumbs': true,
        },
      ];

      await annotationClient.logAnnotations(records, { projectName: 'Test' });

      const finalCall = mockRequest.mock.calls[6];
      const backendRecord = finalCall[0].data.records[0];
      
      expect(backendRecord.annotations).toHaveLength(5);
      expect(backendRecord.annotations[0]).toEqual({
        annotation_label_id: 'text-label',
        value: 'Great work',
      });
      expect(backendRecord.annotations[1]).toEqual({
        annotation_label_id: 'cat-label',
        value_str_list: ['positive'],
      });
      expect(backendRecord.annotations[2]).toEqual({
        annotation_label_id: 'num-label',
        value_float: 8.5,
      });
      expect(backendRecord.annotations[3]).toEqual({
        annotation_label_id: 'star-label',
        value_float: 5,
      });
      expect(backendRecord.annotations[4]).toEqual({
        annotation_label_id: 'bool-label',
        value_bool: true,
      });
    });

    it('should throw error for invalid input', async () => {
      await expect(
        (annotationClient as any).logAnnotations('not-an-array')
      ).rejects.toThrow('Records must be an array');
    });

    it('should throw error for missing label', async () => {
      mockRequest
        .mockResolvedValueOnce({ data: [{ id: 'proj-1', name: 'Test' }] })
        .mockResolvedValueOnce({ data: [] }); // Empty labels

      const records: AnnotationRecord[] = [
        {
          'context.span_id': 'span-123',
          'annotation.missing.text': 'test',
        },
      ];

      await expect(
        annotationClient.logAnnotations(records, { projectName: 'Test' })
      ).rejects.toThrow('No annotation label found for name \'missing\' and type \'text\'');
    });

    it('should throw error for missing project', async () => {
      mockRequest.mockResolvedValueOnce({ data: [] }); // Empty projects

      const records: AnnotationRecord[] = [
        {
          'context.span_id': 'span-123',
          'annotation.test.text': 'test',
        },
      ];

      await expect(
        annotationClient.logAnnotations(records, { projectName: 'Missing Project' })
      ).rejects.toThrow('Project \'Missing Project\' not found');
    });
  });

  describe('getLabels', () => {
    it('should fetch labels successfully', async () => {
      const mockLabels = [
        {
          id: 'label-1',
          name: 'quality',
          type: 'text',
          description: 'Quality assessment',
          settings: { max_length: 100 },
        },
      ];

      mockRequest.mockResolvedValueOnce({
        data: { result: mockLabels },
      });

      const result = await annotationClient.getLabels();

      expect(result).toEqual(mockLabels);
      expect(mockRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: 'http://localhost:8000/tracer/get-annotation-labels/',
        params: {},
        timeout: undefined,
      });
    });

    it('should fetch labels with project filter', async () => {
      const mockLabels = [{ id: 'label-1', name: 'test', type: 'text' }];

      mockRequest.mockResolvedValueOnce({
        data: { result: mockLabels },
      });

      await annotationClient.getLabels({ projectId: 'project-123' });

      expect(mockRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: 'http://localhost:8000/tracer/get-annotation-labels/',
        params: { project_id: 'project-123' },
        timeout: undefined,
      });
    });
  });

  describe('listProjects', () => {
    it('should list projects successfully', async () => {
      const mockProjects = [
        {
          id: 'project-1',
          name: 'Test Project',
          project_type: 'observe',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      mockRequest.mockResolvedValueOnce({
        data: { result: { table: mockProjects } },
      });

      const result = await annotationClient.listProjects();

      expect(result).toEqual(mockProjects);
      expect(mockRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: 'http://localhost:8000/tracer/project/list_projects/',
        params: {
          page_number: 0,
          page_size: 20,
        },
        timeout: undefined,
      });
    });

    it('should list projects with filters', async () => {
      mockRequest.mockResolvedValueOnce({
        data: { result: { table: [] } },
      });

      await annotationClient.listProjects({
        projectType: 'experiment',
        name: 'Test',
        pageNumber: 1,
        pageSize: 50,
      });

      expect(mockRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: 'http://localhost:8000/tracer/project/list_projects/',
        params: {
          page_number: 1,
          page_size: 50,
          project_type: 'experiment',
          name: 'Test',
        },
        timeout: undefined,
      });
    });
  });

  describe('error handling', () => {
    it('should handle 403 authentication errors', async () => {
      const authError = new Error('Auth failed');
      (authError as any).response = { status: 403 };
      
      mockRequest.mockRejectedValueOnce(authError);

      await expect(annotationClient.getLabels()).rejects.toThrow('Invalid authentication');
    });

    it('should handle general API errors', async () => {
      const apiError = new Error('API Error');
      (apiError as any).response = {
        status: 500,
        data: { message: 'Internal server error' },
      };
      
      mockRequest.mockRejectedValueOnce(apiError);

      await expect(annotationClient.getLabels()).rejects.toThrow('Failed to fetch annotation labels');
    });
  });
}); 