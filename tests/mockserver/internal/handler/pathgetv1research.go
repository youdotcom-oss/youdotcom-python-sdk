package handler

import (
	"encoding/json"
	"fmt"
	"log"
	"mockserver/internal/handler/assert"
	"mockserver/internal/logging"
	"mockserver/internal/tracking"
	"net/http"
)

func pathGetV1Research(dir *logging.HTTPFileDirectory, rt *tracking.RequestTracker) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		test := req.Header.Get("x-test-name")
		instanceID := req.Header.Get("x-test-instance-id")

		count := rt.GetRequestCount(test, instanceID)

		switch fmt.Sprintf("%s[%d]", test, count) {
		case "get_/v1/research/{task_id}[0]":
			dir.HandlerFunc("get_/v1/research/{task_id}", testGetV1ResearchTaskSuccess)(w, req)
		case "get_/v1/research/{task_id}-not-found[0]":
			testGetV1ResearchTaskNotFound(w, req)
		case "get_/v1/research/{task_id}-unauthorized[0]":
			testGetV1ResearchTaskUnauthorized(w, req)
		case "get_/v1/research/{task_id}-forbidden[0]":
			testGetV1ResearchTaskForbidden(w, req)
		case "get_/v1/research/{task_id}-internal-error[0]":
			testGetV1ResearchTaskInternalError(w, req)
		default:
			dir.HandlerFunc("get_/v1/research/{task_id}", testGetV1ResearchTaskSuccess)(w, req)
		}
	}
}

// testGetV1ResearchTaskSuccess returns a TaskDetail with status "completed"
// and a populated result block, mirroring the structure used by the real API
// after a background research task finishes.
func testGetV1ResearchTaskSuccess(w http.ResponseWriter, req *http.Request) {
	if err := assert.SecurityHeader(req, "X-API-Key", false); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusUnauthorized)
		return
	}
	if err := assert.HeaderExists(req, "User-Agent"); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	respBody := map[string]interface{}{
		"id":           "00000000-0000-0000-0000-000000000001",
		"task_type":    "research",
		"status":       "completed",
		"created_at":   "2026-07-09T00:00:00Z",
		"updated_at":   "2026-07-09T00:02:30Z",
		"completed_at": "2026-07-09T00:02:30Z",
		"error":        nil,
		"input": map[string]interface{}{
			"input":           "Compare NVIDIA, AMD, and Intel revenue over 5 years",
			"research_effort": "deep",
		},
		"result": map[string]interface{}{
			"output": map[string]interface{}{
				"content":      "# Mock Research Result\n\nMock result for completed background task.",
				"content_type": "text",
				"sources": []map[string]interface{}{
					{
						"url":      "https://example.com/research/1",
						"title":    "Mock Research Source 1",
						"snippets": []string{"This is a relevant snippet from source 1."},
					},
				},
			},
		},
	}

	respBodyBytes, err := json.Marshal(respBody)
	if err != nil {
		http.Error(w, "Unable to encode response body as JSON: "+err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(respBodyBytes)
}

func testGetV1ResearchTaskNotFound(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	_, _ = w.Write([]byte(`{"detail":"Task not found"}`))
}

func testGetV1ResearchTaskUnauthorized(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	_, _ = w.Write([]byte(`{"message":"Invalid or expired API key"}`))
}

func testGetV1ResearchTaskForbidden(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusForbidden)
	_, _ = w.Write([]byte(`{"detail":"Forbidden"}`))
}

func testGetV1ResearchTaskInternalError(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusInternalServerError)
	_, _ = w.Write([]byte(`{"message":"Internal server error"}`))
}
