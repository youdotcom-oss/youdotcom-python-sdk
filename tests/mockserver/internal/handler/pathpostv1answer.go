package handler

import (
	"log"
	"mockserver/internal/handler/assert"
	"mockserver/internal/logging"
	"mockserver/internal/tracking"
	"net/http"
)

func pathPostV1Answer(dir *logging.HTTPFileDirectory, rt *tracking.RequestTracker) http.HandlerFunc {
	_ = dir
	_ = rt
	return func(w http.ResponseWriter, req *http.Request) {
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

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{
			"answer": "The capital of France is Paris[[1]].",
			"citations": [
				{
					"source": "https://en.wikipedia.org/wiki/Paris",
					"excerpts": ["Paris is the capital and most populous city of France."]
				}
			],
			"results": {
				"web": [
					{
						"url": "https://en.wikipedia.org/wiki/Paris",
						"title": "Paris - Wikipedia",
						"snippets": ["Paris is the capital and most populous city of France."],
						"page_age": "2025-06-25T11:41:00Z"
					}
				]
			}
		}`))
	}
}
