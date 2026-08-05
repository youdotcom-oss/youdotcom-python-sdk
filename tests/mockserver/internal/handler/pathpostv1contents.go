
package handler

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mockserver/internal/handler/assert"
	"mockserver/internal/logging"
	"mockserver/internal/sdk/models/operations"
	"mockserver/internal/sdk/types"
	"mockserver/internal/sdk/utils"
	"mockserver/internal/tracking"
	"net/http"
)

func pathPostV1Contents(dir *logging.HTTPFileDirectory, rt *tracking.RequestTracker) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		test := req.Header.Get("x-test-name")
		instanceID := req.Header.Get("x-test-instance-id")

		count := rt.GetRequestCount(test, instanceID)

	switch fmt.Sprintf("%s[%d]", test, count) {
	case "post_/v1/contents[0]":
		dir.HandlerFunc("post_/v1/contents", testPostV1ContentsPostV1Contents0)(w, req)
	case "post_/v1/contents[1]":
		dir.HandlerFunc("post_/v1/contents", testPostV1ContentsPostV1Contents1)(w, req)
	case "post_/v1/contents[2]":
		dir.HandlerFunc("post_/v1/contents", testPostV1ContentsPostV1Contents2)(w, req)
	case "post_/v1/contents[3]":
		dir.HandlerFunc("post_/v1/contents", testPostV1ContentsPostV1Contents3)(w, req)
	case "post_/v1/contents-unauthorized[0]":
		testPostV1ContentsUnauthorized(w, req)
	case "post_/v1/contents-forbidden[0]":
		testPostV1ContentsForbidden(w, req)
	default:
		dir.HandlerFunc("post_/v1/contents", testPostV1ContentsPostV1Contents0)(w, req)
	}
	}
}

func testPostV1ContentsPostV1Contents0(w http.ResponseWriter, req *http.Request) {
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
	// Accept header check removed - SDK might send different values
	if err := assert.HeaderExists(req, "User-Agent"); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	
	// Parse request body to determine formats, URLs, and crawl_timeout
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
	
	// Parse formats array (new in 2.0.0 - replaces single format field)
	// formats can be: "html", "markdown", "metadata"
	formats := make(map[string]bool)
	if formatsArray, ok := requestBody["formats"].([]interface{}); ok {
		for _, f := range formatsArray {
			if fStr, ok := f.(string); ok {
				formats[fStr] = true
			}
		}
	}
	// Default to html if no formats specified
	if len(formats) == 0 {
		formats["html"] = true
	}
	
	// Parse crawl_timeout (new in 2.0.0 - optional, 1-60 seconds)
	// We just acknowledge it here, mock server doesn't actually use it
	if crawlTimeout, ok := requestBody["crawl_timeout"].(float64); ok {
		log.Printf("crawl_timeout specified: %.1f seconds\n", crawlTimeout)
	}
	
	// Get URLs from request or use defaults
	var urls []string
	if urlsArray, ok := requestBody["urls"].([]interface{}); ok {
		urls = make([]string, 0, len(urlsArray))
		for _, url := range urlsArray {
			if urlStr, ok := url.(string); ok {
				urls = append(urls, urlStr)
			}
		}
	}
	// If no URLs provided, use defaults
	if len(urls) == 0 {
		urls = []string{"https://www.python.org"}
	}
	
	// Build response based on URLs and requested formats
	var respBody []operations.ResponseBody
	for _, url := range urls {
		item := operations.ResponseBody{
			URL:   types.String(url),
			Title: types.String("Mock Title for " + url),
		}
		
		// Include HTML if requested
		if formats["html"] {
			item.HTML = types.String("<html><body><h1>Mock HTML Content</h1><p>This is mock HTML content for " + url + "</p></body></html>")
		}
		
		// Include Markdown if requested
		if formats["markdown"] {
			item.Markdown = types.String("# Mock Markdown Content\n\nThis is mock markdown content for " + url)
		}
		
		// Include Metadata if requested (new in 2.0.0 - returns json+ld, opengraph info)
		if formats["metadata"] {
			item.Metadata = &operations.ContentsMetadata{
				SiteName:   types.String("Mock Site for " + url),
				FaviconURL: types.String(url + "/favicon.ico"),
			}
		}
		
		respBody = append(respBody, item)
	}
	
	respBodyBytes, err := utils.MarshalJSON(respBody, "", true)

	if err != nil {
		http.Error(
			w,
			"Unable to encode response body as JSON: "+err.Error(),
			http.StatusInternalServerError,
		)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(respBodyBytes)
}

func testPostV1ContentsPostV1Contents1(w http.ResponseWriter, req *http.Request) {
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
	if err := assert.AcceptHeader(req, []string{"application/json"}); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if err := assert.HeaderExists(req, "User-Agent"); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	var respBody []operations.ResponseBody = []operations.ResponseBody{
		operations.ResponseBody{
			URL:   types.String("https://www.python.org"),
			Title: types.String("Welcome to Python.org"),
		},
	}
	respBodyBytes, err := utils.MarshalJSON(respBody, "", true)

	if err != nil {
		http.Error(
			w,
			"Unable to encode response body as JSON: "+err.Error(),
			http.StatusInternalServerError,
		)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(respBodyBytes)
}

func testPostV1ContentsPostV1Contents2(w http.ResponseWriter, req *http.Request) {
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
	if err := assert.AcceptHeader(req, []string{"application/json"}); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if err := assert.HeaderExists(req, "User-Agent"); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	var respBody []operations.ResponseBody = []operations.ResponseBody{
		operations.ResponseBody{
			URL:   types.String("https://www.python.org"),
			Title: types.String("Welcome to Python.org"),
		},
		operations.ResponseBody{
			URL:   types.String("https://www.example.com"),
			Title: types.String("Example Domain"),
		},
	}
	respBodyBytes, err := utils.MarshalJSON(respBody, "", true)

	if err != nil {
		http.Error(
			w,
			"Unable to encode response body as JSON: "+err.Error(),
			http.StatusInternalServerError,
		)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(respBodyBytes)
}

func testPostV1ContentsPostV1Contents3(w http.ResponseWriter, req *http.Request) {
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
	if err := assert.AcceptHeader(req, []string{"application/json"}); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if err := assert.HeaderExists(req, "User-Agent"); err != nil {
		log.Printf("assertion error: %s\n", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	var respBody []operations.ResponseBody = []operations.ResponseBody{
		operations.ResponseBody{
			URL:   types.String("https://www.example.com"),
			Title: types.String("Example Domain"),
		},
	}
	respBodyBytes, err := utils.MarshalJSON(respBody, "", true)

	if err != nil {
		http.Error(
			w,
			"Unable to encode response body as JSON: "+err.Error(),
			http.StatusInternalServerError,
		)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(respBodyBytes)
}

func testPostV1ContentsUnauthorized(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	_, _ = w.Write([]byte(`{"message":"Invalid or expired API key"}`))
}

func testPostV1ContentsForbidden(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusForbidden)
	_, _ = w.Write([]byte(`{"message":"Forbidden"}`))
}
