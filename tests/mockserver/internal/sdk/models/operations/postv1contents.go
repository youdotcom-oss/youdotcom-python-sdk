
package operations

import (
	"encoding/json"
	"fmt"
	"mockserver/internal/sdk/models/components"
)

// ContentsFormats represents the available format types for content retrieval.
// In 2.0.0, this changed from a single format string to an array of formats.
type ContentsFormats string

const (
	ContentsFormatsHTML     ContentsFormats = "html"
	ContentsFormatsMarkdown ContentsFormats = "markdown"
	ContentsFormatsMetadata ContentsFormats = "metadata"
)

func (e ContentsFormats) ToPointer() *ContentsFormats {
	return &e
}

func (e *ContentsFormats) UnmarshalJSON(data []byte) error {
	var v string
	if err := json.Unmarshal(data, &v); err != nil {
		return err
	}
	switch v {
	case "html":
		fallthrough
	case "markdown":
		fallthrough
	case "metadata":
		*e = ContentsFormats(v)
		return nil
	default:
		return fmt.Errorf("invalid value for ContentsFormats: %v", v)
	}
}

type PostV1ContentsRequest struct {
	// Array of URLs to fetch the contents from.
	Urls []string `json:"urls,omitempty"`
	// The formats of the content to be returned. Can include 'html', 'markdown', and/or 'metadata'.
	// Changed in 2.0.0: Now an array instead of single value.
	Formats []ContentsFormats `json:"formats,omitempty"`
	// The timeout in seconds for crawling each URL. Must be between 1 and 60 seconds.
	// New in 2.0.0.
	CrawlTimeout *float64 `json:"crawl_timeout,omitempty"`
}

func (o *PostV1ContentsRequest) GetUrls() []string {
	if o == nil {
		return nil
	}
	return o.Urls
}

func (o *PostV1ContentsRequest) GetFormats() []ContentsFormats {
	if o == nil {
		return nil
	}
	return o.Formats
}

func (o *PostV1ContentsRequest) GetCrawlTimeout() *float64 {
	if o == nil {
		return nil
	}
	return o.CrawlTimeout
}

// ContentsMetadata contains metadata about the web page.
// Only returned when 'metadata' is included in the formats array.
// Returns json+ld, opengraph information when available.
type ContentsMetadata struct {
	// The OpenGraph site name of the web page.
	SiteName *string `json:"site_name,omitempty"`
	// The URL of the favicon of the web page's domain.
	FaviconURL *string `json:"favicon_url,omitempty"`
}

func (o *ContentsMetadata) GetSiteName() *string {
	if o == nil {
		return nil
	}
	return o.SiteName
}

func (o *ContentsMetadata) GetFaviconURL() *string {
	if o == nil {
		return nil
	}
	return o.FaviconURL
}

type ResponseBody struct {
	// The webpage URL whose content has been fetched.
	URL *string `json:"url,omitempty"`
	// The title of the web page.
	Title *string `json:"title,omitempty"`
	// The retrieved HTML content of the web page.
	HTML *string `json:"html,omitempty"`
	// The retrieved Markdown content of the web page.
	Markdown *string `json:"markdown,omitempty"`
	// Metadata about the web page (json+ld, opengraph info).
	// Only returned when 'metadata' is included in the formats array.
	Metadata *ContentsMetadata `json:"metadata,omitempty"`
}

func (o *ResponseBody) GetURL() *string {
	if o == nil {
		return nil
	}
	return o.URL
}

func (o *ResponseBody) GetTitle() *string {
	if o == nil {
		return nil
	}
	return o.Title
}

func (o *ResponseBody) GetHTML() *string {
	if o == nil {
		return nil
	}
	return o.HTML
}

func (o *ResponseBody) GetMarkdown() *string {
	if o == nil {
		return nil
	}
	return o.Markdown
}

func (o *ResponseBody) GetMetadata() *ContentsMetadata {
	if o == nil {
		return nil
	}
	return o.Metadata
}

type PostV1ContentsResponse struct {
	HTTPMeta components.HTTPMetadata `json:"-"`
	// An array of JSON objects containing the page content of each web page
	ResponseBodies []ResponseBody
}

func (o *PostV1ContentsResponse) GetHTTPMeta() components.HTTPMetadata {
	if o == nil {
		return components.HTTPMetadata{}
	}
	return o.HTTPMeta
}

func (o *PostV1ContentsResponse) GetResponseBodies() []ResponseBody {
	if o == nil {
		return nil
	}
	return o.ResponseBodies
}
