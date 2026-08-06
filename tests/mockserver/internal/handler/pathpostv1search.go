package handler

import (
	"log"
	"mockserver/internal/handler/assert"
	"mockserver/internal/logging"
	"mockserver/internal/tracking"
	"net/http"
)

func pathPostV1Search(dir *logging.HTTPFileDirectory, rt *tracking.RequestTracker) http.HandlerFunc {
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
			"results": {
				"web": [
					{
						"url": "https://you.com",
						"title": "The World's Greatest Search Engine!",
						"description": "Search on YDC",
						"snippets": ["I'm an AI assistant that helps you get more done."],
						"thumbnail_url": "https://www.somethumbnailsite.com/thumbnail.jpg",
						"page_age": "2025-06-25T11:41:00Z",
						"favicon_url": "https://someurl.com/favicon"
					}
				],
				"news": [
					{
						"title": "You.com becomes the backbone of the EU's AI strategy",
						"description": "You.com becomes the backbone of the EU's AI strategy.",
						"page_age": "2025-06-25T11:41:00Z",
						"thumbnail_url": "https://www.somethumbnailsite.com/thumbnail.jpg",
						"url": "https://www.you.com/news/eu-ai-strategy-youcom"
					}
				]
			},
			"metadata": {
				"search_uuid": "942ccbdd-7705-4d9c-9d37-4ef386658e90",
				"query": "Your query",
				"latency": 0.123
			}
		}`))
	}
}
