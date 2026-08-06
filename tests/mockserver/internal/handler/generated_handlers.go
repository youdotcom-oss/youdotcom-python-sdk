
package handler

import (
	"context"
	"mockserver/internal/logging"
	"mockserver/internal/tracking"
	"net/http"
)

// GeneratedHandlers returns all generated handlers.
func GeneratedHandlers(ctx context.Context, dir *logging.HTTPFileDirectory, rt *tracking.RequestTracker) []*GeneratedHandler {
	return []*GeneratedHandler{
		NewGeneratedHandler(ctx, http.MethodPost, "/v1/search", pathPostV1Search(dir, rt)),
		NewGeneratedHandler(ctx, http.MethodPost, "/v1/contents", pathPostV1Contents(dir, rt)),
		NewGeneratedHandler(ctx, http.MethodPost, "/v1/answer", pathPostV1Answer(dir, rt)),
		NewGeneratedHandler(ctx, http.MethodPost, "/v1/research", pathPostV1Research(dir, rt)),
		NewGeneratedHandler(ctx, http.MethodGet, "/v1/research/{task_id}", pathGetV1Research(dir, rt)),
		NewGeneratedHandler(ctx, http.MethodGet, "/v1/research/{task_id}/stream", pathGetV1ResearchStream(dir, rt)),
		NewGeneratedHandler(ctx, http.MethodPost, "/v1/finance_research", pathPostV1FinanceResearch(dir, rt)),
	}
}
