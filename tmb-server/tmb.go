package main

import (
    "fmt"
    "net/http"
)

type UUID struct {
	UserID string
	model string
}

type OutgoingData struct {
	uuid UUID
	verdict bool
}

type IncomingData struct {
	gpuUtilization float32
	powerDraw float32
	vramUsage float32
	uuid UUID
}

func clientVerificationRequest(w http.ResponseWriter, req *http.Request) {
    fmt.Fprintf(w, "clientVerificationRequest\n")
	// var clientRequest UUID = req.Body

}

func headers(w http.ResponseWriter, req *http.Request) {
    for name, headers := range req.Header {
        for _, h := range headers {
            fmt.Fprintf(w, "%v: %v\n", name, h)
        }
    }
}

func main() {
    http.HandleFunc("/clientVerificationRequest", clientVerificationRequest)
    http.HandleFunc("/headers", headers)
    http.ListenAndServe(":8090", nil)
}