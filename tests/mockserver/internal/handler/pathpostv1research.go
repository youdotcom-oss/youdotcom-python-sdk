package handler

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mockserver/internal/handler/assert"
	"mockserver/internal/logging"
	"mockserver/internal/tracking"
	"net/http"
)

// pathPostV1Research handles POST /v1/research.
//
// 2.4.0 surface included here:
//   - `output_schema=` → server returns `output.content_type="object"` and a
//     structured JSON object as `output.content`. Mirrors the live API:
//     same_entity + confidence + reason fields echoed back from the schema
//     so the SDK can assert round-trip through `Union[str, Dict]` Content.
func pathPostV1Research(dir *logging.HTTPFileDirectory, rt *tracking.RequestTracker) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		test := req.Header.Get("x-speakeasy-test-name")
		instanceID := req.Header.Get("x-speakeasy-test-instance-id")

		count := rt.GetRequestCount(test, instanceID)

		switch fmt.Sprintf("%s[%d]", test, count) {
		case "post_/v1/research[0]":
			dir.HandlerFunc("post_/v1/research", testPostV1ResearchSuccess)(w, req)
		case "post_/v1/research-unauthorized[0]":
			testPostV1ResearchUnauthorized(w, req)
		case "post_/v1/research-forbidden[0]":
			testPostV1ResearchForbidden(w, req)
		case "post_/v1/research-unprocessable[0]":
			testPostV1ResearchUnprocessable(w, req)
		case "post_/v1/research-internal-error[0]":
			testPostV1ResearchInternalError(w, req)
		default:
			dir.HandlerFunc("post_/v1/research", testPostV1ResearchSuccess)(w, req)
		}
	}
}

func testPostV1ResearchSuccess(w http.ResponseWriter, req *http.Request) {
	if err := assert.SecurityHeader(req, "X-API-Key", false); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusUnauthorized)
		return
	}
	if err := assert.ContentType(req, "application/json", true); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if err := assert.HeaderExists(req, "User-Agent"); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	bodyBytes, err := io.ReadAll(req.Body)
	if err != nil {
		log.Printf("error reading request body: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	var requestBody map[string]interface{}
	if err := json.Unmarshal(bodyBytes, &requestBody); err != nil {
		log.Printf("error parsing request body: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	input, _ := requestBody["input"].(string)
	effort, _ := requestBody["research_effort"].(string)
	if effort == "" {
		effort = "standard"
	}

	respBody := buildResearchResponse(input, effort, requestBody)
	respBodyBytes, err := json.Marshal(respBody)
	if err != nil {
		http.Error(w, "Unable to encode response body as JSON: "+err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(respBodyBytes)
}

// buildResearchResponse returns either a text or structured object response
// depending on whether `output_schema` was supplied. Mirrors the live API:
// when `output_schema` is set the server returns `content_type="object"` and
// `content` is a structured dict (not a string).
func buildResearchResponse(input, effort string, requestBody map[string]interface{}) map[string]interface{} {
	if _, hasOutputSchema := requestBody["output_schema"]; hasOutputSchema {
		return map[string]interface{}{
			"output": map[string]interface{}{
				"content_type": "object",
				"content": map[string]interface{}{
					"same_entity": true,
					"confidence":  0.95,
					"reason":      fmt.Sprintf(
						"Mock structured response for: %s (effort: %s)",
						input, effort,
					),
				},
				"sources": []map[string]interface{}{
					{
						"url":      "https://example.com/research/structured/1",
						"title":    "Mock Structured Research Source",
						"snippets": []string{"Reference snippet for the structured response."},
					},
				},
			},
		}
	}

	return map[string]interface{}{
		"output": map[string]interface{}{
			"content":      fmt.Sprintf("# Mock Research Response\n\nThis is a mock research response for: %s (effort: %s)\n\nQuantum computing has seen significant advances in recent years.", input, effort),
			"content_type": "text",
			"sources": []map[string]interface{}{
				{
					"url":      "https://example.com/research/1",
					"title":    "Mock Research Source 1",
					"snippets": []string{"This is a relevant snippet from source 1."},
				},
				{
					"url":      "https://example.com/research/2",
					"title":    "Mock Research Source 2",
					"snippets": []string{"This is a relevant snippet from source 2."},
				},
			},
		},
	}
}

func testPostV1ResearchUnauthorized(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	_, _ = w.Write([]byte(`{"message":"Invalid or expired API key"}`))
}

func testPostV1ResearchForbidden(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusForbidden)
	_, _ = w.Write([]byte(`{"message":"Forbidden"}`))
}

func testPostV1ResearchUnprocessable(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnprocessableEntity)
	_, _ = w.Write([]byte(`{"detail":[{"type":"missing","loc":["body","input"],"msg":"Field required","input":""}]}`))
}

func testPostV1ResearchInternalError(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusInternalServerError)
	_, _ = w.Write([]byte(`{"message":"Internal server error"}`))
}
