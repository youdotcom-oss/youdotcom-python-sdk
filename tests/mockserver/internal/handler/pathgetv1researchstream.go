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

func pathGetV1ResearchStream(dir *logging.HTTPFileDirectory, rt *tracking.RequestTracker) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		test := req.Header.Get("x-speakeasy-test-name")
		instanceID := req.Header.Get("x-speakeasy-test-instance-id")

		count := rt.GetRequestCount(test, instanceID)

		switch fmt.Sprintf("%s[%d]", test, count) {
		case "get_/v1/research/{task_id}/stream[0]":
			dir.HandlerFunc("get_/v1/research/{task_id}/stream", testGetV1ResearchStreamSuccess)(w, req)
		case "get_/v1/research/{task_id}/stream-not-found[0]":
			testGetV1ResearchStreamNotFound(w, req)
		case "get_/v1/research/{task_id}/stream-unauthorized[0]":
			testGetV1ResearchStreamUnauthorized(w, req)
		case "get_/v1/research/{task_id}/stream-forbidden[0]":
			testGetV1ResearchStreamForbidden(w, req)
		case "get_/v1/research/{task_id}/stream-internal-error[0]":
			testGetV1ResearchStreamInternalError(w, req)
		default:
			dir.HandlerFunc("get_/v1/research/{task_id}/stream", testGetV1ResearchStreamSuccess)(w, req)
		}
	}
}

// testGetV1ResearchStreamSuccess emits the SSE sequence documented in the
// Research API stream spec: an opening `connected` event followed by a
// terminal `response.done` event, then a normal close.
//
// Event types match TERMINAL_SSE_EVENTS in
// `ydc_services/libs/workflows/task_shared.py` ({"response.done", "complete",
// "error", "cancelled"}).
func testGetV1ResearchStreamSuccess(w http.ResponseWriter, req *http.Request) {
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

	// SSE requires these headers; flushing after each event lets the client
	// receive events incrementally.
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")
	w.WriteHeader(http.StatusOK)

	flusher, ok := w.(http.Flusher)
	if !ok {
		log.Printf("response writer does not support flushing; stream may buffer")
	}

	writeSSE := func(id, event string, data map[string]interface{}) bool {
		payload, err := json.Marshal(data)
		if err != nil {
			log.Printf("error marshalling SSE data: %s", err)
			return false
		}
		if _, err := fmt.Fprintf(w, "id: %s\nevent: %s\ndata: %s\n\n", id, event, payload); err != nil {
			return false
		}
		if ok {
			flusher.Flush()
		}
		return true
	}

	taskID := "00000000-0000-0000-0000-000000000001"

	// 1) Opening event — sent unconditionally when the stream is opened.
	if !writeSSE("0", "connected", map[string]interface{}{
		"type":    "connected",
		"task_id": taskID,
		"status":  "running",
	}) {
		return
	}

	// 2) Terminal event — closes the stream. `response.done` is one of the
	// four TERMINAL_SSE_EVENTS values that the SDK treats as stream-end.
	if !writeSSE("1", "response.done", map[string]interface{}{
		"type":     "response.done",
		"task_id":  taskID,
		"status":   "completed",
		"sequence": 1,
	}) {
		return
	}
}

func testGetV1ResearchStreamNotFound(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	_, _ = w.Write([]byte(`{"detail":"Task not found"}`))
}

func testGetV1ResearchStreamUnauthorized(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	_, _ = w.Write([]byte(`{"message":"Invalid or expired API key"}`))
}

func testGetV1ResearchStreamForbidden(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusForbidden)
	_, _ = w.Write([]byte(`{"detail":"Forbidden"}`))
}

func testGetV1ResearchStreamInternalError(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusInternalServerError)
	_, _ = w.Write([]byte(`{"message":"Internal server error"}`))
}
