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

func pathPostV1FinanceResearch(dir *logging.HTTPFileDirectory, rt *tracking.RequestTracker) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		test := req.Header.Get("x-test-name")
		instanceID := req.Header.Get("x-test-instance-id")

		count := rt.GetRequestCount(test, instanceID)

		switch fmt.Sprintf("%s[%d]", test, count) {
		case "post_/v1/finance_research[0]":
			dir.HandlerFunc("post_/v1/finance_research", testPostV1FinanceResearchSuccess)(w, req)
		case "post_/v1/finance_research-unauthorized[0]":
			testPostV1FinanceResearchUnauthorized(w, req)
		case "post_/v1/finance_research-forbidden[0]":
			testPostV1FinanceResearchForbidden(w, req)
		case "post_/v1/finance_research-unprocessable[0]":
			testPostV1FinanceResearchUnprocessable(w, req)
		case "post_/v1/finance_research-internal-error[0]":
			testPostV1FinanceResearchInternalError(w, req)
		default:
			dir.HandlerFunc("post_/v1/finance_research", testPostV1FinanceResearchSuccess)(w, req)
		}
	}
}

// Finance Research sources intentionally never include the `snippets` field
// (FinanceResearchSource only defines `url` and `title`; extra fields are
// ignored by pydantic's default config).
func testPostV1FinanceResearchSuccess(w http.ResponseWriter, req *http.Request) {
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

	var requestBody map[string]interface{}
	bodyBytes, err := io.ReadAll(req.Body)
	if err != nil {
		log.Printf("error reading request body: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if err := json.Unmarshal(bodyBytes, &requestBody); err != nil {
		log.Printf("error parsing request body: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	effort, _ := requestBody["research_effort"].(string)
	if effort == "" {
		effort = "deep"
	}

	respBody := map[string]interface{}{
		"output": map[string]interface{}{
			"content": fmt.Sprintf(
				"# Mock Finance Research (effort: %s)\n\nNVIDIA's FY2025 revenue grew on Data Center demand.",
				effort,
			),
			"content_type": "text",
			"sources": []map[string]interface{}{
				{
					"url":   "https://investor.nvidia.com/financial-info/financial-reports/default.aspx",
					"title": "NVIDIA Corporation - Financial Reports",
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

func testPostV1FinanceResearchUnauthorized(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	_, _ = w.Write([]byte(`{"message":"Invalid or expired API key"}`))
}

func testPostV1FinanceResearchForbidden(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusForbidden)
	_, _ = w.Write([]byte(`{"message":"Forbidden"}`))
}

func testPostV1FinanceResearchUnprocessable(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnprocessableEntity)
	_, _ = w.Write([]byte(`{"detail":[{"type":"missing","loc":["body","input"],"msg":"Field required","input":""}]}`))
}

func testPostV1FinanceResearchInternalError(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusInternalServerError)
	_, _ = w.Write([]byte(`{"message":"Internal server error"}`))
}
