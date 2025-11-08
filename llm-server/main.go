package main

var models = []string{"gpt5", "gpt4", "gpt3"}

type PromptRequest struct {
	Uuid int 
	Prompt string
	Model string
}

import (
	"log"
	"net/http"
	"github.com/gin-gonic/gin"
	"strconv"
)

func main() {
	r := gin.Default()

	r.GET("/prompt", func(c *gin.Context) {
		uuid, err := strconv.Atoi(c.Param("uuid"))
		if err != nil {
			c.JSON(http.StatusErr, gin.H{})
			return
		}

		prompt := c.Param("prompt")

		model := c.Param("model")
		if !contains(models, model){
			c.JSON(http.StatusErr, gin.H{})
			return
		}

		state := PromptRequest {
			Uuid: uuid, 
			Prompt: prompt,
			model: model,
		}

		c.String(http.StatusOK, message)
		c.JSON(http.StatusOK, gin.H{
			"status": "received",
		})

		go handle_prompt(state)
	})

	// Start server on port 8080 (default)
	// Server will listen on 0.0.0.0:8080 (localhost:8080 on Windows)
	if err := r.Run(); err != nil {
		log.Fatalf("failed to run server: %v", err)
	}
}

func contains(slice []string, target string) bool {
	for _, v := range slice {
		if v == target {
			return true
		}
	}
	return false
}

func handle_prompt(state PromptRequest){
}

