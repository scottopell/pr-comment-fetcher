package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"strings"

	"golang.org/x/net/html"
)

type RepositoryData map[string]map[string]PRData

type PRData struct {
	RegressionComment RegressionComment `json:"regression_comment"`
	MilestoneTitle    string            `json:"milestone_title"`
	RegressionRunId   string            `json:"regression_run_id"`
}

type RegressionComment struct {
	Body string `json:"body"`
}

func main() {
	filePath := "../regression_comments_by_pr.json"
	log.SetOutput(os.Stdout)

	data, err := readJSONFile(filePath)
	if err != nil {
		log.Fatalf("Failed to read JSON file: %v", err)
	}

	extractFields(data)
}

func readJSONFile(filePath string) (RepositoryData, error) {
	fileContent, err := ioutil.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var data RepositoryData
	err = json.Unmarshal(fileContent, &data)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal JSON: %w", err)
	}

	return data, nil
}

func extractFields(data RepositoryData) {
	for repo, prDataMap := range data {
		for prNumber, prData := range prDataMap {
			htmlContent := prData.RegressionComment.Body

			htmlReader := strings.NewReader(htmlContent)

			doc, err := html.Parse(htmlReader)
			if err != nil {
				log.Fatalf("Failed to parse HTML: %v", err)
			}

			rows := extractTableRows(doc)
			for _, row := range rows {
				if len(row) >= 2 && row[0] == "uds_dogstatsd_to_api" {
					log.Printf("https://github.com/%s/pull/%s\t %v\n", repo, prNumber, row)
				}
			}
		}
	}
}

func extractTableRows(node *html.Node) [][]string {
	var rows [][]string

	var traverse func(*html.Node)
	traverse = func(n *html.Node) {
		if n.Type == html.ElementNode && n.Data == "tr" {
			row := extractTableRow(n)
			rows = append(rows, row)
		}

		for c := n.FirstChild; c != nil; c = c.NextSibling {
			traverse(c)
		}
	}

	traverse(node)
	return rows
}

func extractTableRow(node *html.Node) []string {
	var row []string

	for c := node.FirstChild; c != nil; c = c.NextSibling {
		if c.Type == html.ElementNode && c.Data == "td" {
			row = append(row, extractTableCell(c))
		}
	}

	return row
}

func extractTableCell(node *html.Node) string {
	var text string

	for c := node.FirstChild; c != nil; c = c.NextSibling {
		if c.Type == html.TextNode {
			text += c.Data
		}
	}

	return text
}
