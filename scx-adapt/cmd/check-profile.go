/*
Copyright © 2026 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"
	"internal/helper"
	"io"
	"os"

	"github.com/spf13/cobra"
)

// checkProfileCmd represents the checkProfile command
var checkProfileCmd = &cobra.Command{
	Use:   "check-profile",
	Short: "Check if profile file in YAML format passed from STDIN is valid",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) == 0 {
			data, err := io.ReadAll(os.Stdin)
			if err != nil {
				fmt.Println("Error reading from stdin: ", err)
				os.Exit(1)
			}

			if err := helper.ValidateYAML(data); err != nil {
				fmt.Println(err)
				os.Exit(1)
			}

			fmt.Println("Valid config.")
		} else {
			fmt.Println("Too many arguments. scx-adapt --help to see usage")
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(checkProfileCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// checkProfileCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// checkProfileCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
